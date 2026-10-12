#include <windows.h>

__declspec(dllexport)
DWORD WINAPI ReflectiveLoader(LPVOID lpParameter)
{
    (void)lpParameter;
    return 0x1234;
}

BOOL WINAPI DllMain(
    HINSTANCE hinstDLL,
    DWORD fdwReason,
    LPVOID lpReserved
)
{
    return TRUE;
}
