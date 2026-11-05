# Firmware Makefile - photodiode LVDS receiver (STM32H723)
#
#   make host-test   build + run the host-side tests: the codec suite
#                    (codec/test_codec.c), the USB descriptor audit,
#                    the USB framing round-trip, the DAC8562 driver
#                    test and the HV control test (tests/). Works
#                    with the host gcc alone.
#   make arm         cross-compile firmware for the target; needs
#                    arm-none-eabi-gcc - if it is not installed this
#                    target says so and fails, it does not fake a build
#   make clean       remove build/

BUILD      := build
CODEC_DIR  := codec
SRC_DIR    := src
TESTS_DIR  := tests
TUSB_DIR   := third_party/tinyusb/src
TUSB_PORT  := $(SRC_DIR)/tinyusb_port

HOST_CC    := gcc
HOST_FLAGS := -std=c99 -Wall -Wextra -Werror -O2

ARM_CC     := arm-none-eabi-gcc
ARM_CPU    := -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard
ARM_FLAGS  := -std=c99 -Wall -Wextra -O2 -ffunction-sections -fdata-sections \
              -fno-common -I$(CODEC_DIR) -I$(SRC_DIR) -I$(TUSB_DIR) -I$(TUSB_PORT)
ARM_LD     := -T linker.ld -Wl,--gc-sections -nostartfiles -Wl,-Map=$(BUILD)/rxfw.map

# TinyUSB (third_party/PROVENANCE.md) is compiled as C11 with its own
# warning set kept visible but non-fatal; it is upstream code, not
# held to this repo's -Werror bar (the host build) nor edited to
# satisfy ours.
TUSB_FLAGS := -std=gnu11 -Wall -O2 -ffunction-sections -fdata-sections \
              -fno-common -I$(TUSB_DIR) -I$(TUSB_PORT) -I$(SRC_DIR)
TUSB_SRCS  := $(TUSB_DIR)/tusb.c \
              $(TUSB_DIR)/device/usbd.c \
              $(TUSB_DIR)/common/tusb_fifo.c \
              $(TUSB_DIR)/class/cdc/cdc_device.c \
              $(TUSB_DIR)/portable/synopsys/dwc2/dcd_dwc2.c \
              $(TUSB_DIR)/portable/synopsys/dwc2/dwc2_common.c

CODEC_SRCS := $(CODEC_DIR)/codec.c
TEST_SRCS  := $(CODEC_DIR)/test_codec.c
ARM_SRCS   := startup.c \
              $(CODEC_SRCS) \
              $(SRC_DIR)/main.c \
              $(SRC_DIR)/clocks.c \
              $(SRC_DIR)/gpio.c \
              $(SRC_DIR)/i2c.c \
              $(SRC_DIR)/spi.c \
              $(SRC_DIR)/dac8562.c \
              $(SRC_DIR)/tmp117.c \
              $(SRC_DIR)/adn2813.c \
              $(SRC_DIR)/hv_ctrl.c \
              $(SRC_DIR)/hv_sense.c \
              $(SRC_DIR)/capture.c \
              $(SRC_DIR)/usb_app.c \
              $(SRC_DIR)/usb_descriptors.c \
              $(SRC_DIR)/usb_device_tinyusb.c
ARM_OBJS   := $(patsubst %.c,$(BUILD)/%.o,$(ARM_SRCS)) \
              $(patsubst %.c,$(BUILD)/tusb/%.o,$(notdir $(TUSB_SRCS)))

.PHONY: host-test arm clean

host-test: $(BUILD)/test_codec $(BUILD)/test_usb_descriptors \
           $(BUILD)/test_usb_framing $(BUILD)/test_dac8562 \
           $(BUILD)/test_hv_ctrl
	./$(BUILD)/test_codec
	./$(BUILD)/test_usb_descriptors
	./$(BUILD)/test_usb_framing
	./$(BUILD)/test_dac8562
	./$(BUILD)/test_hv_ctrl

$(BUILD)/test_codec: $(CODEC_SRCS) $(TEST_SRCS) $(CODEC_DIR)/codec.h
	@mkdir -p $(BUILD)
	$(HOST_CC) $(HOST_FLAGS) -I$(CODEC_DIR) $(CODEC_SRCS) $(TEST_SRCS) -o $@

$(BUILD)/test_usb_descriptors: $(TESTS_DIR)/test_usb_descriptors.c \
                               $(SRC_DIR)/usb_descriptors_data.h
	@mkdir -p $(BUILD)
	$(HOST_CC) $(HOST_FLAGS) -I$(SRC_DIR) \
	    $(TESTS_DIR)/test_usb_descriptors.c -o $@

# The framing round-trip runs the real usb_app.c protocol handler
# through the real usb_device_if.h byte pipe, with mock control
# backends and an in-memory loopback standing where the TinyUSB
# transport sits on target (see the test's header comment).
$(BUILD)/test_usb_framing: $(TESTS_DIR)/test_usb_framing.c \
                           $(SRC_DIR)/usb_app.c $(CODEC_SRCS)
	@mkdir -p $(BUILD)
	$(HOST_CC) $(HOST_FLAGS) -I$(CODEC_DIR) -I$(SRC_DIR) \
	    $(TESTS_DIR)/test_usb_framing.c $(SRC_DIR)/usb_app.c \
	    $(CODEC_SRCS) -o $@

# The DAC8562 driver test links the real dac8562.c against mock
# gpio_write / spi_transfer backends (tests/test_dac8562.c carries
# its own copies), so it observes which pin the driver frames SYNC
# on and the exact bytes transferred. spi.c/gpio.c are NOT linked.
$(BUILD)/test_dac8562: $(TESTS_DIR)/test_dac8562.c \
                       $(SRC_DIR)/dac8562.c $(SRC_DIR)/dac8562.h \
                       $(SRC_DIR)/board.h
	@mkdir -p $(BUILD)
	$(HOST_CC) $(HOST_FLAGS) -I$(SRC_DIR) \
	    $(TESTS_DIR)/test_dac8562.c $(SRC_DIR)/dac8562.c -o $@

# The HV control test links the real hv_ctrl.c against mock
# dac8562_set_bias_setpoint / gpio_write / hv_sense_read_mv
# backends (tests/test_hv_ctrl.c carries them), so it observes the
# volts->counts transfer and the J5 interlock gate behaviour.
# dac8562.c/gpio.c/hv_sense.c are NOT linked.
$(BUILD)/test_hv_ctrl: $(TESTS_DIR)/test_hv_ctrl.c \
                       $(SRC_DIR)/hv_ctrl.c $(SRC_DIR)/hv_ctrl.h \
                       $(SRC_DIR)/board.h
	@mkdir -p $(BUILD)
	$(HOST_CC) $(HOST_FLAGS) -I$(SRC_DIR) \
	    $(TESTS_DIR)/test_hv_ctrl.c $(SRC_DIR)/hv_ctrl.c -o $@

arm:
	@command -v $(ARM_CC) >/dev/null 2>&1 || { \
	    echo "ERROR: $(ARM_CC) is not installed - cannot build the ARM target."; \
	    echo "Install gcc-arm-none-eabi, then re-run 'make arm'."; \
	    echo "'make host-test' works without it."; exit 1; }
	$(MAKE) $(BUILD)/rxfw.elf
	arm-none-eabi-objcopy -O binary $(BUILD)/rxfw.elf $(BUILD)/rxfw.bin
	arm-none-eabi-size $(BUILD)/rxfw.elf
	@echo "Built $(BUILD)/rxfw.elf and $(BUILD)/rxfw.bin"

$(BUILD)/rxfw.elf: $(ARM_OBJS) linker.ld
	@mkdir -p $(BUILD)
	$(ARM_CC) $(ARM_CPU) $(ARM_OBJS) $(ARM_LD) -o $@

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(ARM_CC) $(ARM_CPU) $(ARM_FLAGS) -c $< -o $@

$(BUILD)/tusb/%.o: $(TUSB_DIR)/%.c
	@mkdir -p $(dir $@)
	$(ARM_CC) $(ARM_CPU) $(TUSB_FLAGS) -c $< -o $@

$(BUILD)/tusb/%.o: $(TUSB_DIR)/device/%.c
	@mkdir -p $(dir $@)
	$(ARM_CC) $(ARM_CPU) $(TUSB_FLAGS) -c $< -o $@

$(BUILD)/tusb/%.o: $(TUSB_DIR)/common/%.c
	@mkdir -p $(dir $@)
	$(ARM_CC) $(ARM_CPU) $(TUSB_FLAGS) -c $< -o $@

$(BUILD)/tusb/%.o: $(TUSB_DIR)/class/cdc/%.c
	@mkdir -p $(dir $@)
	$(ARM_CC) $(ARM_CPU) $(TUSB_FLAGS) -c $< -o $@

$(BUILD)/tusb/%.o: $(TUSB_DIR)/portable/synopsys/dwc2/%.c
	@mkdir -p $(dir $@)
	$(ARM_CC) $(ARM_CPU) $(TUSB_FLAGS) -c $< -o $@

clean:
	rm -rf $(BUILD)
