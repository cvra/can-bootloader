#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/flash.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/can.h>
#include <stddef.h>
#include <bootloader.h>
#include <boot_arg.h>
#include <platform/mcu/armv7-m/timeout_timer.h>
#include "platform.h"

#define GPIOC_LED GPIO13
#define GPIOD_CAN1_RX GPIO0
#define GPIOD_CAN1_TX GPIO1

// page buffer used by config commands.
uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void can_interface_init(void)
{
    rcc_periph_clock_enable(RCC_CAN1);

    /*
    STM32F3 CAN1 on 42MHz configured APB1 peripheral clock
    42MHz / 2 -> 21MHz
    21MHz / (1tq + 12tq + 8tq) = 1MHz => 1Mbit
    */
    can_init(CAN1, // Interface
             false, // Time triggered communication mode.
             true, // Automatic bus-off management.
             false, // Automatic wakeup mode.
             false, // No automatic retransmission.
             false, // Receive FIFO locked mode.
             true, // Transmit FIFO priority.
             CAN_BTR_SJW_4TQ, // Resynchronization time quanta jump width
             CAN_BTR_TS1_12TQ, // Time segment 1 time quanta width
             CAN_BTR_TS2_8TQ, // Time segment 2 time quanta width
             2, // Prescaler
             false, // Loopback
             false); // Silent

    // filter to match any standard id
    // mask bits: 0 = Don't care, 1 = mute match corresponding id bit
    can_filter_id_mask_32bit_init(
        CAN1,
        0, // filter nr
        0, // id: only std id, no rtr
        6 | (7 << 29), // mask: match only std id[10:8] = 0 (bootloader frames)
        0, // assign to fifo0
        true // enable
    );
}

void fault_handler(void)
{
    // while(1); // debug
    reboot_system(BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);
}

void platform_main(int arg)
{
    rcc_clock_setup_hse_3v3(&hse_12mhz_3v3[CLOCK_3V3_168MHZ]);

    rcc_periph_clock_enable(RCC_GPIOD);
    rcc_periph_clock_enable(RCC_GPIOC);

    // CAN pin
    gpio_mode_setup(GPIOD, GPIO_MODE_AF, GPIO_PUPD_NONE, GPIOD_CAN1_RX | GPIOD_CAN1_TX);
    gpio_set_output_options(GPIOD, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOD_CAN1_RX | GPIOD_CAN1_TX);
    gpio_set_af(GPIOD, GPIO_AF9, GPIOD_CAN1_RX | GPIOD_CAN1_TX);

    // LED on
    gpio_mode_setup(GPIOC, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIOC_LED);
    gpio_set_output_options(GPIOC, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOC_LED);
    gpio_clear(GPIOC, GPIOC_LED);

    // configure timeout of 10000 milliseconds
    timeout_timer_init(168000000, 10000);

    can_interface_init();

    bootloader_main(arg);

    reboot_system(BOOT_ARG_START_BOOTLOADER);
}
