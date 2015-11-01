#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

extern "C" {
#include "../../boot_arg.h"
}

void reboot_system(uint8_t arg)
{
    mock().actualCall("reboot").withIntParameter("arg", arg);
}
