#include <windows.h>

#include <iostream>
#include <string>


int wmain(
    int argc,
    wchar_t* argv[]
)
{
    if (argc != 2)
    {
        std::wcerr
            << L"Usage: mifa-local-dll.exe "
            << L"<dll-path>"
            << std::endl;

        return 1;
    }

    const std::wstring dll_path =
        argv[1];

    HMODULE module = LoadLibraryW(
        dll_path.c_str()
    );

    if (!module)
    {
        std::wcerr
            << L"LoadLibraryW failed. Error: "
            << GetLastError()
            << std::endl;

        return 2;
    }

    wchar_t loaded_path[
        MAX_PATH
    ]{};

    DWORD length = GetModuleFileNameW(
        module,
        loaded_path,
        MAX_PATH
    );

    std::wcout
        << L"[+] DLL loaded"
        << std::endl;

    if (
        length > 0
        && length < MAX_PATH
    )
    {
        std::wcout
            << L"Module: "
            << loaded_path
            << std::endl;
    }

    if (!FreeLibrary(
        module
    ))
    {
        std::wcerr
            << L"FreeLibrary failed. Error: "
            << GetLastError()
            << std::endl;

        return 3;
    }

    std::wcout
        << L"[+] DLL unloaded"
        << std::endl;

    return 0;
}
