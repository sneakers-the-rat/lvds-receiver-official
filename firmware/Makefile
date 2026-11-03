# Firmware Makefile - photodiode LVDS receiver (STM32H723)
#
#   make host-test   build the codec library + host tests with the
#                    host gcc and run them (works today)
#   make arm         cross-compile firmware for the target; needs
#                    arm-none-eabi-gcc - if it is not installed this
#                    target says so and fails, it does not fake a build
#   make clean       remove build/

BUILD      := build
CODEC_DIR  := codec
SRC_DIR    := src

HOST_CC    := gcc
HOST_FLAGS := -std=c99 -Wall -Wextra -Werror -O2

ARM_CC     := arm-none-eabi-gcc
ARM_CPU    := -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard
ARM_FLAGS  := -std=c99 -Wall -Wextra -O2 -ffunction-sections -fdata-sections \
              -fno-common -I$(CODEC_DIR) -I$(SRC_DIR)
ARM_LD     := -T linker.ld -Wl,--gc-sections -nostartfiles -Wl,-Map=$(BUILD)/rxfw.map

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
              $(SRC_DIR)/capture.c \
              $(SRC_DIR)/usb_app.c \
              $(SRC_DIR)/usb_device_stub.c
ARM_OBJS   := $(patsubst %.c,$(BUILD)/%.o,$(ARM_SRCS))

.PHONY: host-test arm clean

host-test: $(BUILD)/test_codec
	./$(BUILD)/test_codec

$(BUILD)/test_codec: $(CODEC_SRCS) $(TEST_SRCS) $(CODEC_DIR)/codec.h
	@mkdir -p $(BUILD)
	$(HOST_CC) $(HOST_FLAGS) -I$(CODEC_DIR) $(CODEC_SRCS) $(TEST_SRCS) -o $@

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

clean:
	rm -rf $(BUILD)
