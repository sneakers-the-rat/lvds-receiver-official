/* hv_sense.h - readback of the LT3757 SHDN/UVLO node voltage.
 *
 * The node (net HV_SHDN, hw/circuit.py) is wired to PA6
 * (BOARD_HV_SENSE_*) purely as a sense input: it lets firmware see
 * the state of the J5 HV-enable interlock jumper (docs/06 owner
 * decision). The node has three signatures (docs/03):
 *   - PC7 clamped low, J5 FITTED:  ~0 V (PC7 holds the node down)
 *   - J5 ABSENT (any PC7 state):   ~0.94 V (R25/R26 divider alone)
 *   - PC7 driving high, J5 FITTED: ~3.3 V (the enabled state)
 * A digital input cannot separate 0 V from 0.94 V (both sit at or
 * below the STM32 VIL band edge), so the pin is read with ADC1.
 *
 * The sense is a veto/reporting layer only: the hardware jumper in
 * series in the PC7 path is the authoritative gate. A broken or
 * misread sense can refuse enable, never grant it past the jumper.
 */
#ifndef HV_SENSE_H
#define HV_SENSE_H

/* Node voltage in millivolts, or -1 when no conversion completed.
 * Callers must treat -1 as "state unknown" (= not fitted), never
 * as a voltage. */
int hv_sense_read_mv(void);

#endif /* HV_SENSE_H */
