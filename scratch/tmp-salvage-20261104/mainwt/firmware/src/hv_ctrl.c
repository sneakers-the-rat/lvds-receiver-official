/* hv_ctrl.c - see hv_ctrl.h. Update rate assumption: 10 Hz, so the
 * per-update slew step is HV_SLEW_V_PER_S / 10. If the call rate in
 * main.c changes, this constant must change with it. */
#include "hv_ctrl.h"
#include "board.h"
#include "dac8562.h"
#include "gpio.h"
#include "hv_sense.h"

#define HV_UPDATE_HZ 10.0f

/* J5 sense thresholds (millivolts at the SHDN node; the three node
 * signatures are derived in docs/03): with PC7 clamped low a fitted
 * J5 holds the node at ~0 V, so anything below 450 mV is "fitted";
 * with PC7 driving high through a fitted J5 the node sits at
 * ~3.3 V, so anything above 2500 mV is "fitted". Between them is
 * the divider-alone signature (0.83-1.03 V over all corners): J5
 * absent. A failed sense read (-1) counts as absent. */
#define HV_SENSE_FITTED_CLAMPED_MAX_MV 450
#define HV_SENSE_FITTED_DRIVEN_MIN_MV  2500

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

/* Is the J5 interlock jumper fitted, per the node sense? The
 * reading is only meaningful against PC7's current state, which
 * hv->enabled tracks: disabled means PC7 is clamped low. */
static int jumper_fitted(const hv_ctrl_t *hv)
{
    int mv = hv_sense_read_mv();
    if (mv < 0) {
        return 0;
    }
    if (hv->enabled) {
        return mv > HV_SENSE_FITTED_DRIVEN_MIN_MV;
    }
    return mv < HV_SENSE_FITTED_CLAMPED_MAX_MV;
}

uint16_t hv_ctrl_volts_to_counts(float volts)
{
    /* Invert the fitted network's transfer (hv_ctrl.h):
     * V_DAC = (253.2 - V_HV) / 54.86, saturated to the DAC span.
     * A request of 0 V maps to DAC full-scale = the minimum demand
     * the hardware can express (116.1 V); the rail reaches true 0
     * only via the SHDN clamp, which is how disable works. */
    float vdac = (HV_XFER_V_AT_DAC_ZERO
                  - clampf(volts, 0.0f, HV_MAX_V))
               / HV_XFER_SLOPE_V_PER_V;
    vdac = clampf(vdac, 0.0f, HV_DAC_FULL_SCALE_V);
    return (uint16_t)(vdac / HV_DAC_FULL_SCALE_V * 65535.0f + 0.5f);
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
     * SHDN node to ~0 V through the fitted J5 (board.h).
     * gpio_init_board_pins() has already configured the pin as an
     * output driving low; this write keeps hv_ctrl_init()
     * self-sufficient about the state it owns. */
    gpio_write(BOARD_HV_SHDN_PORT, BOARD_HV_SHDN_PIN, 0);
    /* DAC bias channel to minimum demand - under the fitted
     * network's inverse transfer that is hv_ctrl_volts_to_counts(0)
     * = DAC full-scale, NOT 0 counts (0 counts is the maximum
     * demand, 253.2 V). The caller (main) runs dac8562_init before
     * hv_ctrl_init, so the channel exists. Even the maximum-demand
     * state is safe here: the converter is held off and 253.2 V is
     * inside the fitted APD's envelope (docs/03). */
    hv->dac_counts = hv_ctrl_volts_to_counts(0.0f);
    (void)dac8562_set_bias_setpoint(hv->dac_counts);
    /* Publish the sensed jumper state for GET_STATUS. */
    hv->interlock_ok = jumper_fitted(hv);
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
        /* The gate is the sensed J5 interlock jumper (docs/06 owner
         * decision). The hardware is authoritative - with J5 absent
         * PC7 is not connected to the SHDN node at all - and this
         * sensed gate keeps the protocol honest on top of it:
         * SET_BIAS reports INTERLOCK and GET_STATUS shows the
         * jumper state. A failed sense read counts as absent. */
        if (!jumper_fitted(hv)) {
            hv->interlock_ok = 0;
            hv->fault = 1;
            return -1; /* refused: J5 interlock jumper not fitted */
        }
        hv->interlock_ok = 1;
        hv->fault = 0;
        hv->enabled = 1;
        /* Release the shutdown clamp: PC7 high drives the SHDN node
         * to ~3.3 V through the fitted J5, above the LT3757
         * threshold (the divider alone holds it at 0.94 V, below
         * threshold - board.h, docs/03). */
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

    /* Refresh the sensed gate state, then enforce the safety
     * invariant: if the gate is (or becomes) unsatisfied while HV
     * is enabled - J5 pulled, or the sense unreadable - drop HV
     * immediately. (With J5 pulled the hardware drops the node to
     * the divider's 0.94 V on its own; this makes the firmware
     * state follow the hardware fact.) */
    hv->interlock_ok = jumper_fitted(hv);
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
