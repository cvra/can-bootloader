#include <libopencm3/cm3/systick.h>
#include "timeout_timer.h"

static uint32_t timer_freq;
static uint32_t timeout_in_millisec;

bool timeout_reached(void)
{
    static uint32_t sys_ticks = 0;
    sys_ticks += STK_RVR_RELOAD - systick_get_value();
    if (systick_get_countflag()) {
        sys_ticks += STK_RVR_RELOAD + 1;
    }
    STK_CVR = STK_RVR_RELOAD;
    return timeout_in_millisec < sys_ticks / (timer_freq / 1000);
}

void timeout_timer_init(uint32_t f_cpu, uint32_t timeout_ms)
{
    timer_freq = f_cpu;
    timeout_in_millisec = timeout_ms;
    systick_counter_enable();
    systick_set_clocksource(STK_CSR_CLKSOURCE_AHB);
    systick_set_reload(STK_RVR_RELOAD);
}
