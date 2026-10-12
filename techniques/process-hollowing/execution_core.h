#ifndef MIFA_PROCESS_HOLLOWING_CORE_H
#define MIFA_PROCESS_HOLLOWING_CORE_H

#include <stddef.h>

int execute_technique(
    const unsigned char *payload,
    size_t payload_len,
    const char *target
);

#endif
