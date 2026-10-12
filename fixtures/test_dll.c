#include <windows.h>

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved)
{
    if (fdwReason == DLL_PROCESS_ATTACH) {
        HANDLE hFile = CreateFileA(
            "C:\\Users\\Public\\mifa_dll_test.txt",
            GENERIC_WRITE,
            0,
            NULL,
            CREATE_ALWAYS,
            FILE_ATTRIBUTE_NORMAL,
            NULL
        );

        if (hFile != INVALID_HANDLE_VALUE) {
            const char msg[] = "Mifa DLL Injection runtime test successful.\r\n";
            DWORD written = 0;
            WriteFile(hFile, msg, sizeof(msg) - 1, &written, NULL);
            CloseHandle(hFile);
        }
    }

    return TRUE;
}
