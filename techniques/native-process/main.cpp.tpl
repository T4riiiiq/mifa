#include <windows.h>

#include <iostream>
#include <string>
#include <vector>


static std::wstring QuoteArgument(
    const std::wstring& argument
)
{
    if (
        argument.find_first_of(
            L" \t\""
        ) == std::wstring::npos
    )
    {
        return argument;
    }

    std::wstring result = L"\"";
    size_t backslashes = 0;

    for (wchar_t character : argument)
    {
        if (character == L'\\')
        {
            ++backslashes;
            continue;
        }

        if (character == L'"')
        {
            result.append(
                backslashes * 2 + 1,
                L'\\'
            );

            result.push_back(
                L'"'
            );

            backslashes = 0;
            continue;
        }

        result.append(
            backslashes,
            L'\\'
        );

        backslashes = 0;

        result.push_back(
            character
        );
    }

    result.append(
        backslashes * 2,
        L'\\'
    );

    result.push_back(
        L'"'
    );

    return result;
}


int wmain(
    int argc,
    wchar_t* argv[]
)
{
    if (argc < 2)
    {
        std::wcerr
            << L"Usage: mifa-native.exe "
            << L"<application> [arguments...]"
            << std::endl;

        return 1;
    }

    const std::wstring application =
        argv[1];

    std::wstring command_line =
        QuoteArgument(
            application
        );

    for (int index = 2; index < argc; ++index)
    {
        command_line += L" ";
        command_line += QuoteArgument(
            argv[index]
        );
    }

    std::vector<wchar_t> mutable_command(
        command_line.begin(),
        command_line.end()
    );

    mutable_command.push_back(
        L'\0'
    );

    STARTUPINFOW startup_info{};
    PROCESS_INFORMATION process_info{};

    startup_info.cb =
        sizeof(
            startup_info
        );

    BOOL created = CreateProcessW(
        application.c_str(),
        mutable_command.data(),
        nullptr,
        nullptr,
        FALSE,
        0,
        nullptr,
        nullptr,
        &startup_info,
        &process_info
    );

    if (!created)
    {
        DWORD error =
            GetLastError();

        std::wcerr
            << L"CreateProcessW failed. "
            << L"Error: "
            << error
            << std::endl;

        return 2;
    }

    std::wcout
        << L"[+] Process created"
        << std::endl;

    std::wcout
        << L"PID: "
        << process_info.dwProcessId
        << std::endl;

    WaitForSingleObject(
        process_info.hProcess,
        INFINITE
    );

    DWORD exit_code = 0;

    if (
        !GetExitCodeProcess(
            process_info.hProcess,
            &exit_code
        )
    )
    {
        exit_code = 1;
    }

    CloseHandle(
        process_info.hThread
    );

    CloseHandle(
        process_info.hProcess
    );

    std::wcout
        << L"Exit code: "
        << exit_code
        << std::endl;

    return static_cast<int>(
        exit_code
    );
}
