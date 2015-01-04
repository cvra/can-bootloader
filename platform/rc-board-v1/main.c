#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/can.h>
#include <stddef.h>
#include <bootloader.h>
#include <boot_arg.h>
#include <platform/mcu/armv7-m/timeout_timer.h>

// must be large enought to contain the packed config, 2048 bytes max
#define CONFIG_SIZE 256

extern int app_start, config_page1, config_page2; // defined by linkerscript
const size_t config_page_size = CONFIG_SIZE;
uint8_t config_page_buffer[CONFIG_SIZE];

void *memory_get_app_addr(void)
{
    return &app_start;
}

void *memory_get_config1_addr(void)
{
    return &config_page1;
}

void *memory_get_config2_addr(void)
{
    return &config_page2;
}

void can_interface_init(void)
{
    rcc_periph_clock_enable(RCC_CAN);
    rcc_periph_clock_enable(RCC_GPIOA);

    gpio_mode_setup(GPIOA, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIO8);
    gpio_set_output_options(GPIOA, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIO8);
    gpio_clear(GPIOA, GPIO8);

    gpio_mode_setup(GPIOA, GPIO_MODE_AF, GPIO_PUPD_NONE, GPIO11 | GPIO12);
    gpio_set_output_options(GPIOA, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIO11 | GPIO12);
    gpio_set_af(GPIOA, GPIO_AF9, GPIO11 | GPIO12);

    /*
    STM32F3 CAN on 32MHz configured APB1 peripheral clock
    32MHz / 2 -> 16MHz
    16MHz / (1tq + 9tq + 6tq) = 1MHz => 1Mbit
    */
    can_init(CAN,             // Interface
             false,           // Time triggered communication mode.
             true,            // Automatic bus-off management.
             false,           // Automatic wakeup mode.
             false,           // No automatic retransmission.
             false,           // Receive FIFO locked mode.
             true,            // Transmit FIFO priority.
             CAN_BTR_SJW_1TQ, // Resynchronization time quanta jump width
             CAN_BTR_TS1_9TQ, // Time segment 1 time quanta width
             CAN_BTR_TS2_6TQ, // Time segment 2 time quanta width
             2,               // Prescaler
             false,           // Loopback
             false);          // Silent

    // filter to match any standard id
    // mask bits: 0 = Don't care, 1 = mute match corresponding id bit
    can_filter_id_mask_32bit_init(
        CAN,
        0,      // filter nr
        0,      // id: only std id, no rtr
        6,      // mask: macth any std id
        0,      // assign to fifo0
        true    // enable
    );
}

void fault_handler(void)
{
    gpio_set(GPIOC, GPIO15);

    while(1); // debug

    reboot(BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);
}

void platform_main(int arg)
{
    rcc_clock_setup_hsi(&hsi_8mhz[CLOCK_64MHZ]);

    // LEDs
    rcc_periph_clock_enable(RCC_GPIOC);
    gpio_mode_setup(GPIOC, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIO13 | GPIO14 | GPIO15);
    gpio_set_output_options(GPIOC, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIO13 | GPIO14 | GPIO15);

    // white led on
    gpio_set(GPIOC, GPIO13);

    // configure timeout of 3000 milliseconds
    timeout_timer_init(64000000, 3000);

    can_interface_init();

    bootloader_main(arg);

    reboot(BOOT_ARG_START_BOOTLOADER);
}
