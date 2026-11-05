/*
 * test_hv_ctrl.c - host tests for the HV control module
 * (src/hv_ctrl.c), linked against mock dac8562_set_bias_setpoint /
 * gpio_write / hv_sense_read_mv backends.
 *
 * What the mocks can and cannot observe, stated plainly:
 *
 * - OBSERVABLE: the volts->counts transfer is a pure function and
 *   is checked against the fitted network's equation (docs/03:
 *   V_HV = 253.2 - 54.86 * V_DAC, V_DAC = counts/65535 * 2.5 V),
 *   with expected counts computed independently in
 *   results/hvfix/derivation.py. The interlock gate is checked
 *   behaviourally: the mock sense returns the three node
 *   signatures (fitted-clamped ~0 mV, absent ~940 mV, fitted-
 *   driven ~3300 mV, docs/03) and the mock GPIO records what PC7
 *   is driven to, so refusal, enable and drop-on-pull are all
 *   exercised end to end at the module boundary.
 * - NOT OBSERVABLE: the ADC register sequence in hv_sense.c and
 *   the real node voltages. Those are target-side and VERIFY at
 *   bring-up, like every register block in this repo.
 *
 * Pin-map literals are independent on purpose (same convention as
 * test_dac8562.c): hw/circuit.py assigns PC7 = HV_EN (via J5 to
 * the SHDN node) and PA6 = HV_SHDN (sense).
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "board.h"
#include "hv_ctrl.h"

static int failures = 0;

#define CHECK(cond, name)                                              \
    do {                                                               \
        if (cond) {                                                    \
            printf("PASS %s\n", (name));                               \
        } else {                                                       \
            printf("FAIL %s (line %d)\n", (name), __LINE__);           \
            failures++;                                                \
        }                                                              \
    } while (0)

/* ------------------------- mock backends ------------------------- */

static int mock_sense_mv = 940; /* power-on state: J5 absent */
int hv_sense_read_mv(void)
{
    return mock_sense_mv;
}

static uint16_t mock_dac_counts = 0;
static int mock_dac_writes = 0;
int dac8562_set_bias_setpoint(uint16_t counts)
{
    mock_dac_counts = counts;
    mock_dac_writes++;
    return 0;
}

static int mock_pc7 = -1; /* last level written to PC7, -1 = never */
static int mock_pc7_high_writes = 0;
void gpio_write(gpio_regs_t *port, uint32_t pin, int value)
{
    if (port == BOARD_HV_SHDN_PORT && pin == BOARD_HV_SHDN_PIN) {
        mock_pc7 = value;
        if (value) {
            mock_pc7_high_writes++;
        }
    }
}

/* ------------------------------ main ------------------------------ */

static int counts_near(float volts, int expected, int tol)
{
    int c = (int)hv_ctrl_volts_to_counts(volts);
    return c >= expected - tol && c <= expected + tol;
}

int main(void)
{
    hv_ctrl_t hv;

    /* Pin-map lock. */
    CHECK(BOARD_HV_SHDN_PORT == GPIOC && BOARD_HV_SHDN_PIN == 7u,
          "hv shdn drive is PC7");
    CHECK(BOARD_HV_SENSE_PORT == GPIOA && BOARD_HV_SENSE_PIN == 6u,
          "hv sense is PA6");

    /* Transfer: V_HV = 253.2 - 54.86 * V_DAC (docs/03). */
    CHECK(hv_ctrl_volts_to_counts(0.0f) == 65535,
          "0 V request -> DAC full-scale (minimum demand)");
    CHECK(hv_ctrl_volts_to_counts(253.21f) <= 1,
          "253.21 V request -> DAC zero-scale (maximum demand)");
    CHECK(counts_near(184.64f, 32768, 2),
          "184.64 V -> mid-scale counts 32768");
    CHECK(counts_near(150.0f, 49321, 3), "150 V -> 49321 counts");
    CHECK(counts_near(200.0f, 25428, 3), "200 V -> 25428 counts");
    CHECK(counts_near(250.0f, 1535, 3), "250 V -> 1535 counts");
    CHECK(hv_ctrl_volts_to_counts(120.0f) > hv_ctrl_volts_to_counts(150.0f)
          && hv_ctrl_volts_to_counts(150.0f) > hv_ctrl_volts_to_counts(200.0f)
          && hv_ctrl_volts_to_counts(200.0f) > hv_ctrl_volts_to_counts(250.0f),
          "counts strictly decrease as requested volts rise");
    CHECK(hv_ctrl_volts_to_counts(400.0f) == hv_ctrl_volts_to_counts(253.21f),
          "request above the ceiling clamps to the ceiling");
    CHECK(hv_ctrl_volts_to_counts(-5.0f) == 65535,
          "negative request clamps to minimum demand");

    /* Temperature compensation (unchanged pure function). */
    memset(&hv, 0, sizeof(hv));
    hv_ctrl_set_setpoint(&hv, 200.0f);
    CHECK(hv_ctrl_target_for_temp(&hv, 25.0f) > 199.99f
          && hv_ctrl_target_for_temp(&hv, 25.0f) < 200.01f,
          "temp comp is identity at 25 C");
    CHECK(hv_ctrl_target_for_temp(&hv, 35.0f) > 212.99f
          && hv_ctrl_target_for_temp(&hv, 35.0f) < 213.01f,
          "temp comp adds 1.3 V/C above 25 C");

    /* Init with J5 absent: gate published closed, DAC left at
     * minimum demand, PC7 clamped low. */
    mock_sense_mv = 940;
    mock_pc7 = -1;
    hv_ctrl_init(&hv);
    CHECK(hv.interlock_ok == 0, "init publishes J5 absent (940 mV)");
    CHECK(mock_dac_counts == 65535 && hv.dac_counts == 65535,
          "init leaves DAC at minimum demand (full-scale counts)");
    CHECK(mock_pc7 == 0, "init clamps PC7 low");

    /* Enable refused while the jumper is absent - and on a failed
     * sense read. PC7 must never be driven high. */
    mock_pc7_high_writes = 0;
    CHECK(hv_ctrl_enable(&hv, 1) == -1 && hv.enabled == 0
          && hv.fault == 1,
          "enable refused with J5 absent");
    mock_sense_mv = -1;
    CHECK(hv_ctrl_enable(&hv, 1) == -1 && hv.enabled == 0,
          "enable refused when the sense read fails");
    CHECK(mock_pc7_high_writes == 0, "PC7 never driven high on refusal");

    /* Enable with J5 fitted (node clamped ~0 mV by PC7 itself). */
    mock_sense_mv = 20;
    hv_ctrl_set_setpoint(&hv, 200.0f);
    CHECK(hv_ctrl_enable(&hv, 1) == 0 && hv.enabled == 1
          && hv.interlock_ok == 1 && mock_pc7 == 1,
          "enable proceeds with J5 fitted, PC7 driven high");

    /* Running update with the node driven (~3.3 V) stays enabled. */
    mock_sense_mv = 3300;
    CHECK(hv_ctrl_update(&hv, 25.0f, 1) == 0 && hv.enabled == 1,
          "update keeps HV enabled while node reads driven");

    /* Pulling J5 mid-run (node falls to the divider's 940 mV)
     * drops HV immediately and clamps PC7 low. */
    mock_sense_mv = 940;
    CHECK(hv_ctrl_update(&hv, 25.0f, 1) == 0 && hv.enabled == 0
          && hv.fault == 1 && mock_pc7 == 0,
          "update drops HV when J5 is pulled mid-run");

    /* Disabled-state updates keep GET_STATUS truthful. */
    mock_sense_mv = 20;
    (void)hv_ctrl_update(&hv, 25.0f, 1);
    CHECK(hv.interlock_ok == 1, "disabled update publishes J5 fitted");
    mock_sense_mv = 940;
    (void)hv_ctrl_update(&hv, 25.0f, 1);
    CHECK(hv.interlock_ok == 0, "disabled update publishes J5 absent");

    if (failures) {
        printf("test_hv_ctrl: %d FAILURE(S)\n", failures);
        return 1;
    }
    printf("test_hv_ctrl: all checks passed\n");
    return 0;
}
