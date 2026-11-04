/* hv_ctrl.c - see hv_ctrl.h. Update rate assumption: 10 Hz, so the
 * per-update slew step is HV_SLEW_V_PER_S / 10. If the call rate in
 * main.c changes, this constant must change with it. */
#include "hv_ctrl.h"
#include "board.h"
#include "dac8562.h"
#include "gpio.h"

#define HV_UPDATE_HZ 10.0f

static float clampf(float v, float lo, float hi)
{
    if (v < lo) {
        return lo;
    }
    if (v > hi) {
        return hi;
    }
    return v;
}

uint16_t hv_ctrl_volts_to_counts(float volts)
{
    float c = clampf(volts, 0.0f, HV_MAX_V) / HV_FULL_SCALE_V * 65535.0f;
    return (uint16_t)(c + 0.5f);
}

void hv_ctrl_init(hv_ctrl_t *hv)
{
    hv->setpoint_v_at_25c = 0.0f;
    hv->commanded_v = 0.0f;
    hv->dac_counts = 0;
    hv->enabled = 0;
    hv->interlock_ok = 0;
    hv->fault = 0;
    /* Hold the converter in shutdown: PC7 low pulls the LT3757
     * SHDN node to ~0 V (board.h). gpio_init_board_pins() has
     * already configured the pin as an output driving low; this
     * write keeps hv_ctrl_init() self-sufficient about the state
     * it owns. */
    gpio_write(BOARD_HV_SHDN_PORT, BOARD_HV_SHDN_PIN, 0);
    /* DAC bias channel to 0 - the caller (main) runs dac8562_init
     * before hv_ctrl_init, so the channel exists. */
    (void)dac8562_set_bias_setpoint(0u);
}

void hv_ctrl_set_setpoint(hv_ctrl_t *hv, float volts_at_25c)
{
    hv->setpoint_v_at_25c = clampf(volts_at_25c, 0.0f, HV_MAX_V);
}

float hv_ctrl_target_for_temp(const hv_ctrl_t *hv, float temp_c)
{
    float v = hv->setpoint_v_at_25c
            + HV_APD_TEMPCO_V_PER_C * (temp_c - HV_REF_TEMP_C);
    return clampf(v, 0.0f, HV_MAX_V);
}

int hv_ctrl_enable(hv_ctrl_t *hv, int on)
{
    if (on) {
        /* The gate is NOT sampled from a pin: rev A has no interlock
         * input (docs/06-hv-cdr-pin-inventory.md), so interlock_ok
         * is never set and this refusal always fires. That is the
         * recorded owner design decision - see hv_ctrl.h. */
        if (!hv->interlock_ok) {
            hv->fault = 1;
            return -1; /* refused: interlock gate unsatisfied */
        }
        hv->fault = 0;
        hv->enabled = 1;
        /* Release the shutdown clamp: PC7 high lets the SHDN node
         * rise to the divider's 1.24 V, above the LT3757 threshold. */
        gpio_write(BOARD_HV_SHDN_PORT, BOARD_HV_SHDN_PIN, 1);
        return 0;
    }
    hv->enabled = 0;
    gpio_write(BOARD_HV_SHDN_PORT, BOARD_HV_SHDN_PIN, 0);
    /* Note: with HV_SHDN clamped low the flyback stops; the
     * hardware bleeder (R30, docs/03) discharges the rail below
     * 60 V within ~1 s. The DAC setpoint is also driven to 0 in
     * hv_ctrl_update's disabled path so a later enable starts
     * from 0 and slews up, never jumps. */
    return 0;
}

int hv_ctrl_update(hv_ctrl_t *hv, float temp_c, int temp_valid)
{
    float target;
    float max_step = HV_SLEW_V_PER_S / HV_UPDATE_HZ;
    uint16_t counts;
    int r;

    /* Safety invariant, kept even though rev A can never be in the
     * enabled state: if the gate is (or becomes) unsatisfied while
     * HV is enabled, drop HV immediately. Nothing samples a pin
     * here - there is no interlock input to sample (hv_ctrl.h). */
    if (hv->enabled && !hv->interlock_ok) {
        (void)hv_ctrl_enable(hv, 0);
        hv->fault = 1;
    }
    if (!temp_valid) {
        /* No trustworthy temperature -> no compensation -> no HV
         * above 0. Ramp down at the slew limit, fault latched. */
        hv->fault = 1;
        target = 0.0f;
    } else if (!hv->enabled) {
        target = 0.0f;
    } else {
        target = hv_ctrl_target_for_temp(hv, temp_c);
    }

    /* Slew-rate limit toward the target. */
    if (hv->commanded_v < target) {
        hv->commanded_v += max_step;
        if (hv->commanded_v > target) {
            hv->commanded_v = target;
        }
    } else if (hv->commanded_v > target) {
        hv->commanded_v -= max_step;
        if (hv->commanded_v < target) {
            hv->commanded_v = target;
        }
    }

    counts = hv_ctrl_volts_to_counts(hv->commanded_v);
    if (counts != hv->dac_counts) {
        r = dac8562_set_bias_setpoint(counts);
        if (r != 0) {
            hv->fault = 1;
            return r;
        }
        hv->dac_counts = counts;
    }
    return 0;
}
