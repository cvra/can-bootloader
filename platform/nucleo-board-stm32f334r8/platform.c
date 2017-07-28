
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/flash.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/can.h>

#include <bootloader.h>
#include <boot_arg.h>
#include <platform/mcu/armv7-m/timeout_timer.h>
#include "platform.h"


// page buffer used by config commands.
uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void can_interface_init(void)
{
    // Enable clock to GPIO port A
    rcc_periph_clock_enable(RCC_GPIOA);

    // Enable clock to CAN peripheral
    rcc_periph_clock_enable(RCC_CAN);

    // Setup CAN pins
    gpio_mode_setup(
            GPIO_BANK_CAN_TX,
            GPIO_MODE_AF,
            GPIO_PUPD_NONE,
            GPIO_CAN_TX);
    gpio_set_af(
            GPIO_BANK_CAN_TX,
            GPIO_AF_CAN,
            GPIO_CAN_TX
            );

    gpio_mode_setup(
            GPIO_BANK_CAN_RX,
            GPIO_MODE_AF,
            GPIO_PUPD_NONE,
            GPIO_CAN_RX
            );
    gpio_set_af(
            GPIO_BANK_CAN_RX,
            GPIO_AF_CAN,
            GPIO_CAN_RX
            );

    /* Remap the can to pin PA11 and PA12 , should already be by default */
/*
    gpio_primary_remap(
            AFIO_MAPR_SWJ_CFG_FULL_SWJ,
            AFIO_MAPR_CAN1_REMAP_PORTA
            );
*/

    /*
    STM32F3 CAN1 on 18MHz configured APB1 peripheral clock
    18MHz / 2 -> 9MHz
    9MHz / (1tq + 10tq + 7tq) = 500kHz => 500kbit
    */
    can_init(CAN,            // Interface
             false,           // Time triggered communication mode.
             true,            // Automatic bus-off management.
             false,           // Automatic wakeup mode.
             false,           // No automatic retransmission.
             false,           // Receive FIFO locked mode.
             true,            // Transmit FIFO priority.
             CAN_BTR_SJW_1TQ, // Resynchronization time quanta jump width
             CAN_BTR_TS1_10TQ,// Time segment 1 time quanta width
             CAN_BTR_TS2_7TQ, // Time segment 2 time quanta width
             2,               // Prescaler
             false,           // Loopback
             false);          // Silent

    // filter to match any standard id
    // mask bits: 0 = Don't care, 1 = mute match corresponding id bit
    can_filter_id_mask_32bit_init(
        CAN,
        0,      // filter nr
        0,      // id: only std id, no rtr
        6 | (7<<29), // mask: match only std id[10:8] = 0 (bootloader frames)
        0,      // assign to fifo0
        true    // enable
    );

//    nvic_enable_irq(NVIC_IRQ_CAN);
}

void fault_handler(void)
{
    // while(1); // debug
    reboot_system(BOOT_ARG_START_BOOTLOADER_NO_TIMEOUT);
}

void rcc_clock_setup_in_hsi_out_36mhz(void)
{
    static clock_scale_t clock_36mhz =
    {
        pll: RCC_CFGR_PLLMUL_PLL_IN_CLK_X9,
        pllsrc: RCC_CFGR_PLLSRC_HSI_DIV2,
        hpre: RCC_CFGR_HPRE_DIV_NONE,
        ppre1: RCC_CFGR_PPRE1_DIV_2,
        ppre2: RCC_CFGR_PPRE2_DIV_NONE,
        power_save: 1,
        flash_config: FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY_1WS,
        apb1_frequency: 18000000,
        apb2_frequency: 36000000,
    };

    rcc_clock_setup_hsi(&clock_36mhz);
}

void platform_main(int arg)
{
    /*
    // If external 8MHz present on PF0/PF1
    rcc_clock_setup_in_hse_8mhz_out_72mhz();
    */
    // otherwise use internal RC oscillator
    rcc_clock_setup_in_hsi_out_36mhz();

    /* Init the PA5 port to output at maximum speed */
    gpio_mode_setup(
            PORT_LED2,
            GPIO_MODE_OUTPUT,
            GPIO_PUPD_NONE,
            PIN_LED2
            );

    // Blink onboard led
    uint32_t i=0,j=0;
    for(i=0;i<11;i++)
    {
//        for(j=0;j<1000000;j++)
//        {
//            asm("nop");
//        }
        gpio_toggle(PORT_LED2,PIN_LED2);
    }
    /*
    for(j=0;j<10000000;j++)
    {
        asm("nop");
    }
    gpio_set(PORT_LED2,PIN_LED2);
    */

    // configure timeout of 10000 milliseconds (assuming 36 Mhz system clock, see above)
    timeout_timer_init(36000000, 10000);
    can_interface_init();
    bootloader_main(arg);

    reboot_system(BOOT_ARG_START_BOOTLOADER);
}
