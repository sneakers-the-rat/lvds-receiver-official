/* hv_ctrl.h - APD bias (high voltage) control loop.
 *
 * The setpoint lives in the DAC8562 bias channel; this module adds:
 *   - temperature compensation at the C30737 breakdown tempco,
 *   - slew-rate limiting on every change,
 *   - an interlock gate (HV can only be enabled while the J5
 *     interlock jumper is sensed fitted, and drops immediately if
 *     it ceases to be),
 *   - safe defaults: off at power-up, output driven to 0 on disable.
 *
 * The interlock is the J5 deliberate-action jumper (owner decision,
 * docs/06): a 2-pin header in series in the PC7 -> SHDN path. With
 * J5 absent the MCU pin is not connected to the SHDN node at all
 * and the R25/R26 divider alone holds the node in shutdown, so no
 * firmware state can start the converter; the gate in this module
 * is the sensed/reported layer on top of that hardware fact. The
 * sense is PA6 reading the node voltage via ADC1 (hv_sense.c);
 * while it reports the jumper absent (or cannot be read),
 * hv_ctrl_enable() refuses and SET_BIAS returns INTERLOCK, exactly
 * as the pre-jumper firmware refused unconditionally.
 *
 * Drawn hardware protections (hw/circuit.py - the earlier claim of
 * an independent OVP zener clamp came from docs/02 and is NOT in
 * the drawn design; do not rely on it): the LT3757's cycle-by-cycle
 * primary current limit via the R28 sense resistor, the R30 4.7 MOhm
 * bleeder discharging the rail below 60 V within ~1 s of disable
 * (docs/03), the fitted feedback network's ceiling (253.2 V at
 * V_DAC = 0 for the C30737 population - a hardware bound, not a
 * firmware one), and the J5 jumper above. */
#ifndef HV_CTRL_H
#define HV_CTRL_H

#include <stdint.h>

/* C30737 Vbr temperature coefficient: 1.3 V/degC
 * (datasheets/C30737.pdf, via docs/02-architecture.md). */
#define HV_APD_TEMPCO_V_PER_C 1.3f
#define HV_REF_TEMP_C         25.0f
/* Set-point transfer of the fitted feedback network, C30737
 * population (docs/03 "HV set-point network"): the LT3757 servos
 * FBX to 1.6 V across R31 7.68 Mohm / R32 75.0 kohm with the DAC
 * injected via R33 140 kohm, giving
 *     V_HV = 253.2 - 54.86 * V_DAC,     V_DAC in [0, 2.5] V
 * DAC zero-scale (the DAC8562 power-up state) is therefore the
 * maximum demand, 253.2 V - the hardware ceiling, inside the
 * C30737's 260 V breakdown maximum at every tolerance corner
 * (worst case 259.4 V; docs/03). DAC full-scale demands 116.1 V.
 * hv_ctrl_volts_to_counts() inverts this transfer.
 * The S8664 stuffing variant (docs/03) restores the original
 * network and its transfer (A = 419.7 V, slope 107.4 V/V); a board
 * built that way needs those constants here instead. */
#define HV_XFER_V_AT_DAC_ZERO 253.21f
#define HV_XFER_SLOPE_V_PER_V 54.857f
#define HV_DAC_FULL_SCALE_V   2.5f
/* Slew limit applied to the commanded bias: volts per second. */
#define HV_SLEW_V_PER_S       5.0f
/* Hard firmware clamp on the requested setpoint: the fitted
 * network's own ceiling. Requests above it saturate at the DAC. */
#define HV_MAX_V              253.21f

typedef struct {
    float    setpoint_v_at_25c; /* host-requested bias, referred to 25 C */
    float    commanded_v;       /* slew-limited voltage actually applied */
    uint16_t dac_counts;        /* counts last written to the DAC */
    int      enabled;           /* HV output stage enabled */
    int      interlock_ok;      /* enable-gate state: the sensed J5
                                   jumper state (hv_sense), refreshed
                                   by hv_ctrl_init/enable/update. It
                                   is published in GET_STATUS as-is. */
    int      fault;             /* latched fault: interlock/temp/DAC error */
} hv_ctrl_t;

void hv_ctrl_init(hv_ctrl_t *hv);
/* Request a setpoint (volts at 25 C). Does not by itself enable HV. */
void hv_ctrl_set_setpoint(hv_ctrl_t *hv, float volts_at_25c);
/* Enable/disable the HV output (HV_SHDN clamp + DAC). Enabling is
 * refused (returns -1) while the J5 interlock jumper is sensed
 * absent (see header). Disabling always works. */
int  hv_ctrl_enable(hv_ctrl_t *hv, int on);
/* Temperature-compensated target for a given temperature:
 *   Vset(T) = Vset25 + 1.3 V/C * (T - 25 C)     (pure function) */
float hv_ctrl_target_for_temp(const hv_ctrl_t *hv, float temp_c);
/* Periodic update - call at 10 Hz from the main loop with the newest
 * TMP117 reading. Applies temp compensation + slew limiting and
 * writes the DAC when the counts change. temp_valid=0 forces a
 * safe state (ramp to 0, fault latched). Returns 0 or a DAC error. */
int  hv_ctrl_update(hv_ctrl_t *hv, float temp_c, int temp_valid);

uint16_t hv_ctrl_volts_to_counts(float volts); /* pure */

#endif /* HV_CTRL_H */
