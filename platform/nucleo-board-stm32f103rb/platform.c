#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/flash.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/can.h>
#include <stddef.h>
#include <bootloader.h>
#include <boot_arg.h>
#include <platform/mcu/armv7-m/timeout_timer.h>
#include "platform.h"

// page buffer used by config commands.
uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void can_interface_init(void)
{
    rcc_periph_clock_enable(RCC_CAN1);

    /*
    STM32F3 CAN1 on 18MHz configured APB1 peripheral clock
    18MHz / 2 -> 9MHz
    9MHz / (1tq + 10tq + 7tq) = 500kHz => 500kbit
    */
    can_init(CAN1, // Interface
             false, // Time triggered communication mode.
             true, // Automatic bus-off management.
             false, // Automatic wakeup mode.
             false, // No automatic retransmission.
             false, // Receive FIFO locked mode.
             true, // Transmit FIFO priority.
             CAN_BTR_SJW_1TQ, // Resynchronization time quanta jump width
             CAN_BTR_TS1_10TQ, // Time segment 1 time quanta width
             CAN_BTR_TS2_7TQ, // Time segment 2 time quanta width
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
void rcc_clock_setup_in_hsi_out_36mhz(void)
{
    /* Enable internal high-speed oscillator. */
    rcc_osc_on(HSI);
    rcc_wait_for_osc_ready(HSI);

    /* Select HSI as SYSCLK source. */
    rcc_set_sysclk_source(RCC_CFGR_SW_SYSCLKSEL_HSICLK);

    /*
     * Set prescalers for AHB, ADC, ABP1, ABP2.
     * Do this before touching the PLL (TODO: why?).
     */
    rcc_set_hpre(RCC_CFGR_HPRE_SYSCLK_NODIV); /*Set.36MHz Max.72MHz */
    rcc_set_adcpre(RCC_CFGR_ADCPRE_PCLK2_DIV6); /*Set. 6MHz Max.14MHz */
    rcc_set_ppre1(RCC_CFGR_PPRE1_HCLK_DIV2); /*Set.18MHz Max.36MHz */
    rcc_set_ppre2(RCC_CFGR_PPRE2_HCLK_NODIV); /*Set.36MHz Max.72MHz */

    /*
     * Sysclk runs with 48MHz -> 1 waitstates.
     * 0WS from 0-24MHz
     * 1WS from 24-48MHz
     * 2WS from 48-72MHz
     */
    flash_set_ws(FLASH_ACR_LATENCY_1WS);

    /*
     * Set the PLL multiplication factor to 12.
     * 8MHz (internal) * 9 (multiplier) / 2 (PLLSRC_HSI_CLK_DIV2) = 36MHz
     */
    rcc_set_pll_multiplication_factor(RCC_CFGR_PLLMUL_PLL_CLK_MUL9);

    /* Select HSI/2 as PLL source. */
    rcc_set_pll_source(RCC_CFGR_PLLSRC_HSI_CLK_DIV2);

    /* Enable PLL oscillator and wait for it to stabilize. */
    rcc_osc_on(PLL);
    rcc_wait_for_osc_ready(PLL);

    /* Select PLL as SYSCLK source. */
    rcc_set_sysclk_source(RCC_CFGR_SW_SYSCLKSEL_PLLCLK);

    /* Set the peripheral clock frequencies used */
    rcc_apb1_frequency = 18000000;
    rcc_apb2_frequency = 36000000;
}
void platform_main(int arg)
{
    /*
    //If external 8MHz on PC14/PC15
	rcc_clock_setup_in_hse_8mhz_out_72mhz();*/
    //Else internal clock
    rcc_clock_setup_in_hsi_out_36mhz();

    //Activate PORTA
    rcc_periph_clock_enable(RCC_GPIOA);
    rcc_periph_clock_enable(RCC_AFIO);

    // CAN pin
    /* init PA12 (TX) to Alternativ function output */
    gpio_set_mode(GPIOA, GPIO_MODE_OUTPUT_50_MHZ, GPIO_CNF_OUTPUT_ALTFN_PUSHPULL, GPIO_CAN1_TX); //TX output
    /* init PA11 (RX) to input pull up */
    gpio_set_mode(GPIOA, GPIO_MODE_INPUT, GPIO_CNF_INPUT_PULL_UPDOWN, GPIO_CAN1_RX); //RX input pull up/down
    gpio_set(GPIOA, GPIO_CAN1_RX); //pull up
    /* Remap the can to pin PA11 and PA12 , sould already be by default */
    gpio_primary_remap(AFIO_MAPR_SWJ_CFG_FULL_SWJ, AFIO_MAPR_CAN1_REMAP_PORTA); //Can sur port A pin 11/12

    // LED on
    /*init the PA5 port to output in PushPull mode at maxspeed */
    gpio_set_mode(PORT_LED2, GPIO_MODE_OUTPUT_50_MHZ, GPIO_CNF_OUTPUT_PUSHPULL, PIN_LED2); //led output

    //Blinking led on PA5 (build in led in the nucleo-stm32f103rb)
    /*
    uint32_t i=0,j=0;
    for(i=0;i<11;i++)
    {
        for(j=0;j<1000000;j++)
        {
            asm("nop");
        }
        gpio_toggle(PORT_LED2,PIN_LED2);
    }
    for(j=0;j<10000000;j++)
    {
        asm("nop");
    }
    gpio_set(PORT_LED2,PIN_LED2);*/

    // configure timeout of 10000 milliseconds on a 36Mhz
    timeout_timer_init(36000000, 10000);
    can_interface_init();
    bootloader_main(arg);

    reboot_system(BOOT_ARG_START_BOOTLOADER);
}
