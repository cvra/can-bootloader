#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/flash.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/can.h>
#include <stddef.h>
#include <bootloader.h>
#include <boot_arg.h>
#include <platform/mcu/armv7-m/timeout_timer.h>
#include "platform.h"

#define GPIOA_LED GPIO4
#define GPIOB_CAN_EN GPIO0
#define GPIOA_CAN_RX GPIO11
#define GPIOA_CAN_TX GPIO12

// page buffer used by config commands.
uint8_t config_page_buffer[CONFIG_PAGE_SIZE];

void can_interface_init(void)
{
    rcc_periph_clock_enable(RCC_CAN);

    /*
    STM32F3 CAN on 36MHz configured APB1 peripheral clock
    36MHz / 2 -> 18MHz
    18MHz / (1tq + 10tq + 7tq) = 1MHz => 1Mbit
    */
    can_init(CAN, // Interface
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
        CAN,
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

typedef struct {
    uint8_t pllpre;
    uint8_t pll;
    uint8_t pllsrc;
    uint32_t flash_config;
    uint8_t hpre;
    uint8_t ppre1;
    uint8_t ppre2;
    uint8_t power_save;
    uint32_t apb1_frequency;
    uint32_t apb2_frequency;
} my_clock_scale_t;

// clock config for external HSE 16MHz cristal
static const my_clock_scale_t clock_72mhz = {
    .pllpre = RCC_CFGR2_PREDIV_HSE_IN_PLL_DIV_2,
    .pll = RCC_CFGR_PLLMUL_PLL_IN_CLK_X9,
    .pllsrc = RCC_CFGR_PLLSRC_HSE_PREDIV,
    .hpre = RCC_CFGR_HPRE_DIV_NONE,
    .ppre1 = RCC_CFGR_PPRE1_DIV_2,
    .ppre2 = RCC_CFGR_PPRE2_DIV_NONE,
    .power_save = 1,
    .flash_config = FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY_2WS,
    .apb1_frequency = 36000000,
    .apb2_frequency = 72000000,
};

static inline void rcc_set_main_pll_hse(uint32_t pll)
{
    RCC_CFGR = (~RCC_CFGR_PLLMUL_MASK & RCC_CFGR) | (pll << RCC_CFGR_PLLMUL_SHIFT) | RCC_CFGR_PLLSRC;
}

static inline void rcc_clock_setup_hse(const my_clock_scale_t* clock)
{
    /* Enable internal high-speed oscillator. */
    rcc_osc_on(HSE);
    rcc_wait_for_osc_ready(HSE);
    /* Select HSE as SYSCLK source. */
    rcc_set_sysclk_source(RCC_CFGR_SW_HSE);
    rcc_wait_for_sysclk_status(HSE);

    rcc_osc_off(PLL);
    rcc_wait_for_osc_not_ready(PLL);
    rcc_set_pll_source(clock->pllsrc);
    rcc_set_main_pll_hse(clock->pll);
    RCC_CFGR2 = (clock->pllpre << RCC_CFGR2_PREDIV_SHIFT);
    /* Enable PLL oscillator and wait for it to stabilize. */
    rcc_osc_on(PLL);
    rcc_wait_for_osc_ready(PLL);

    rcc_set_hpre(clock->hpre);
    rcc_set_ppre2(clock->ppre2);
    rcc_set_ppre1(clock->ppre1);
    /* Configure flash settings. */
    flash_set_ws(clock->flash_config);
    /* Select PLL as SYSCLK source. */
    rcc_set_sysclk_source(RCC_CFGR_SW_PLL);
    /* Wait for PLL clock to be selected. */
    rcc_wait_for_sysclk_status(PLL);

    /* Set the peripheral clock frequencies used. */
    rcc_apb1_frequency = clock->apb1_frequency;
    rcc_apb2_frequency = clock->apb2_frequency;
}

void platform_main(int arg)
{
    rcc_clock_setup_hse(&clock_72mhz);

    rcc_periph_clock_enable(RCC_GPIOA);
    rcc_periph_clock_enable(RCC_GPIOB);

    // CAN pin
    gpio_mode_setup(GPIOA, GPIO_MODE_AF, GPIO_PUPD_NONE, GPIOA_CAN_RX | GPIOA_CAN_TX);
    gpio_set_output_options(GPIOA, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOA_CAN_RX | GPIOA_CAN_TX);
    gpio_set_af(GPIOA, GPIO_AF9, GPIOA_CAN_RX | GPIOA_CAN_TX);

    // enable CAN transceiver
    gpio_mode_setup(GPIOB, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIOB_CAN_EN);
    gpio_set_output_options(GPIOB, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOB_CAN_EN);
    gpio_clear(GPIOB, GPIOB_CAN_EN);

    // LED on
    gpio_mode_setup(GPIOA, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIOA_LED);
    gpio_set_output_options(GPIOA, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPIOA_LED);
    gpio_set(GPIOA, GPIOA_LED);

    // configure timeout of 10000 milliseconds
    timeout_timer_init(72000000, 10000);

    can_interface_init();

    bootloader_main(arg);

    reboot_system(BOOT_ARG_START_BOOTLOADER);
}
