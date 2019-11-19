#include <libopencm3/stm32/can.h>
#include <can_interface.h>

bool can_interface_read_message(uint32_t* id, uint8_t* message, uint8_t* length, uint32_t retries)
{
    uint32_t fid;
    uint8_t len;
    bool ext, rtr;

    while (retries-- != 0 && (CAN_RF0R(CAN) & CAN_RF0R_FMP0_MASK) == 0)
        ;

    if ((CAN_RF0R(CAN) & CAN_RF0R_FMP0_MASK) == 0) {
        return false;
    }

    can_receive(
        CAN, // canport
        0, // fifo
        true, // release
        id, // can id
        &ext, // extended id
        &rtr, // transmission request
        &fid, // filter id
        &len, // length
        message);

    *length = len;

    return true;
}

bool can_interface_send_message(uint32_t id, uint8_t* message, uint8_t length, uint32_t retries)
{
    do {
        can_transmit(
            CAN, // canport
            id, // can id
            false, // extended id
            false, // request transmit
            length, // data length
            message // data
        );

        while ((CAN_TSR(CAN) & CAN_TSR_RQCP0) == 0)
            ;

        if ((CAN_TSR(CAN) & CAN_TSR_TXOK0)) {
            return true; // can ok
        }
    } while (retries-- > 0);

    return false;
}
