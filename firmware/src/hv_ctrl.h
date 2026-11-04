/* hv_ctrl.h - APD bias (high voltage) control loop.
 *
 * The setpoint lives in the DAC8562 bias channel; this module adds:
 *   - temperature compensation at the C30737 breakdown tempco,
 *   - slew-rate limiting on every change,
 *   - an interlock gate (HV can only be enabled while the gate is
 *     satisfied, and drops immediately if it ceases to be),
 *   - safe defaults: off at power-up, output driven to 0 on disable.
 *
 * The gate has NO input on rev A: the drawn design fits no interlock
 * jumper, switch or sense pin (inventory: docs/06-hv-cdr-pin-
 * inventory.md), so nothing ever satisfies it and hv_ctrl_enable()
 * refuses every enable. That is deliberate - an owner design
 * decision recorded in docs/00-status.md and firmware/BRINGUP.md,
 * not a stub: firmware must not invent a safety input the board
 * does not have. The converter is held off positively via PC7
 * (HV_SHDN, board.h) regardless.
 *
 * Drawn hardware protections (hw/circuit.py - the earlier claim of
 * an independent OVP zener clamp came from docs/02 and is NOT in
 * the drawn design; do not rely on it): the LT3757's cycle-by-cycle
 * primary current limit via the R28 sense resistor, the R30 4.7 MOhm
 * bleeder discharging the rail below 60 V within ~1 s of disable
 * (docs/03), and the feedback divider ceiling (~420 V at V_DAC = 0). */
#ifndef HV_CTRL_H
#define HV_CTRL_H

#include <stdint.h>

/* C30737 Vbr temperature coefficient: 1.3 V/degC
 * (datasheets/C30737.pdf, via docs/02-architecture.md). */
#define HV_APD_TEMPCO_V_PER_C 1.3f
#define HV_REF_TEMP_C         25.0f
/* HV range mapped onto the DAC full scale by the flyback feedback
 * divider: 0 counts = 0 V, 65535 counts = 420 V.
 * VERIFY the divider ratio against the hv/ design at bring-up. */
#define HV_FULL_SCALE_V       420.0f
/* Slew limit applied to the commanded bias: volts per second. */
#define HV_SLEW_V_PER_S       5.0f
/* Hard firmware clamp on the requested setpoint. There is no
 * separate hardware OVP clamp in rev A (see header); the drawn
 * loop's own ceiling is the feedback divider's, ~420 V. */
#define HV_MAX_V              430.0f

typedef struct {
    float    setpoint_v_at_25c; /* host-requested bias, referred to 25 C */
    float    commanded_v;       /* slew-limited voltage actually applied */
    uint16_t dac_counts;        /* counts last written to the DAC */
    int      enabled;           /* HV output stage enabled */
    int      interlock_ok;      /* enable-gate state. On rev A no
                                   interlock input exists, so nothing
                                   ever sets this and it stays 0 -
                                   see the header of this file. It is
                                   published in GET_STATUS as-is. */
    int      fault;             /* latched fault: interlock/temp/DAC error */
} hv_ctrl_t;

void hv_ctrl_init(hv_ctrl_t *hv);
/* Request a setpoint (volts at 25 C). Does not by itself enable HV. */
void hv_ctrl_set_setpoint(hv_ctrl_t *hv, float volts_at_25c);
/* Enable/disable the HV output (HV_SHDN clamp + DAC). Enabling is
 * refused (returns -1) while the interlock gate is unsatisfied -
 * which on rev A is always (see header). Disabling always works. */
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
