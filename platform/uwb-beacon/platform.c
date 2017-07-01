#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/flash.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/can.h>
#include <libopencm3/stm32/timer.h>
#include <libopencm3/cm3/nvic.h>
#include <stddef.h>
#include <bootloader.h>
#include <boot_arg.h>
#include <platform/mcu/armv7-m/timeout_timer.h>
#include "platform.h"

#define GPIOB_LED_ERROR GPIO0
#define GPIOB_LED_DEBUG GPIO1
#define GPIOB_LED_STATUS GPIO2
#define GPIOB_LED_ALL (GPIOB_LED_ERROR | GPIOB_LED_DEBUG | GPIOB_LED_STATUS)

#define GPIOB_CAN1_RX GPIO8
#define GPIOB_CAN1_TX GPIO9

// page buffer used by config commands.
uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void can_interface_init(void)
{
    rcc_periph_clock_enable(RCC_CAN1);

    /*
    STM32F4 CAN1 on 42MHz configured APB1 peripheral clock
    42MHz / 2 -> 21MHz
    21MHz / (1tq + 12tq + 8tq) = 1MHz => 1Mbit
    */
    can_init(CAN1,            // Interface
             false,           // Time triggered communication mode.
             true,            // Automatic bus-off management.
             false,           // Automatic wakeup mode.
             false,           // No automatic retransmission.
             false,           // Receive FIFO locked mode.
             true,            // Transmit FIFO priority.
             CAN_BTR_SJW_4TQ, // Resynchronization time quanta jump width
             CAN_BTR_TS1_12TQ,// Time segment 1 time quanta width
             CAN_BTR_TS2_8TQ, // Time segment 2 time quanta width
             2,               // Prescaler
             false,           // Loopback
             false);          // Silent

    // filter to match any standard id
    // mask bits: 0 = Don't care, 1 = mute match corresponding id bit
    can_filter_id_mask_32bit_init(
        CAN1,
        0,      // filter nr
        0,      // id: only std id, no rtr
        6 | (7<<29), // mask: match only std id[10:8] = 0 (bootloader frames)
        0,      // assign to fifo0
        true    // enable
    );
}

void fault_handler(void)
{
    gpio_clear(GPIOB, GPIOB_LED_ALL);
    gpio_set(GPIOB, GPIOB_LED_ERROR);
    // while(1); // debug
    reboot_system(BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);
}


void platform_main(int arg)
{
    rcc_clock_setup_hse_3v3(&hse_16mhz_3v3[CLOCK_3V3_168MHZ]);

    rcc_periph_clock_enable(RCC_GPIOB);

    // CAN pin
    gpio_mode_setup(GPIOB, GPIO_MODE_AF, GPIO_PUPD_NONE, GPIOB_CAN1_RX | GPIOB_CAN1_TX);
    gpio_set_output_options(GPIOB, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOB_CAN1_RX | GPIOB_CAN1_TX);
    gpio_set_af(GPIOB, GPIO_AF9, GPIOB_CAN1_RX | GPIOB_CAN1_TX);

    // LED on
    gpio_mode_setup(GPIOB, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIOB_LED_ALL);
    gpio_set_output_options(GPIOB, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOB_LED_ALL);
    gpio_clear(GPIOB, GPIOB_LED_ALL);
    gpio_set(GPIOB, GPIOB_LED_STATUS);

    // configure timeout of 10000 milliseconds
    timeout_timer_init(168000000, 10000);

    can_interface_init();

    bootloader_main(arg);

    reboot_system(BOOT_ARG_START_BOOTLOADER);
}
