/* hv_ctrl.h - APD bias (high voltage) control loop.
 *
 * The setpoint lives in the DAC8562 bias channel; this module adds:
 *   - temperature compensation at the C30737 breakdown tempco,
 *   - slew-rate limiting on every change,
 *   - an interlock gate (HV can only be enabled with the interlock
 *     input closed, and drops immediately if it opens),
 *   - safe defaults: off at power-up, output driven to 0 on disable.
 * The hardware side (docs/02) additionally has an independent OVP
 * zener clamp at 440 V, a primary current limit, and a bleeder that
 * discharges the rail below 60 V within 10 s of disable - firmware is
 * never the only protection. */
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
/* Hard firmware clamp, below the 440 V hardware OVP clamp. */
#define HV_MAX_V              430.0f

typedef struct {
    float    setpoint_v_at_25c; /* host-requested bias, referred to 25 C */
    float    commanded_v;       /* slew-limited voltage actually applied */
    uint16_t dac_counts;        /* counts last written to the DAC */
    int      enabled;           /* HV output stage enabled */
    int      interlock_ok;      /* last interlock sample */
    int      fault;             /* latched fault: interlock/temp/DAC error */
} hv_ctrl_t;

void hv_ctrl_init(hv_ctrl_t *hv);
/* Request a setpoint (volts at 25 C). Does not by itself enable HV. */
void hv_ctrl_set_setpoint(hv_ctrl_t *hv, float volts_at_25c);
/* Enable/disable the HV output (GPIO HV_EN + DAC). Enabling is
 * refused (returns -1) while the interlock is open. */
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
