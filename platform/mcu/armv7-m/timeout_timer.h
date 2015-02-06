#ifndef TIMEOUT_TIMER_H
#define TIMEOUT_TIMER_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/** Configures the timeout hardware timer.
 * @param [in] f_cpu The CPU frequency, with which the timer runs.
 * @param [in] timeout_ms The timeout in milliseconds.
 */
void timeout_timer_init(uint32_t f_cpu, uint32_t timeout_ms);

#ifdef __cplusplus
}
#endif

#endif /* TIMEOUT_TIMER_H */