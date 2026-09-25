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


static int Launch(
    const std::wstring& application,
    const std::wstring& command_line
)
{
    std::vector<wchar_t> mutable_command(
        command_line.begin(),
        command_line.end()
    );

    mutable_command.push_back(
        L'\0'
    );

    STARTUPINFOW startup{};
    PROCESS_INFORMATION process{};

    startup.cb = sizeof(
        startup
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
        &startup,
        &process
    );

    if (!created)
    {
        std::wcerr
            << L"CreateProcessW failed. Error: "
            << GetLastError()
            << std::endl;

        return 2;
    }

    std::wcout
        << L"[+] Process created"
        << std::endl;

    std::wcout
        << L"PID: "
        << process.dwProcessId
        << std::endl;

    WaitForSingleObject(
        process.hProcess,
        INFINITE
    );

    DWORD exit_code = 1;

    GetExitCodeProcess(
        process.hProcess,
        &exit_code
    );

    CloseHandle(
        process.hThread
    );

    CloseHandle(
        process.hProcess
    );

    std::wcout
        << L"Exit code: "
        << exit_code
        << std::endl;

    return static_cast<int>(
        exit_code
    );
}


int wmain(
    int argc,
    wchar_t* argv[]
)
{
    if (argc < 2)
    {
        std::wcerr
            << L"Usage: mifa-command.exe "
            << L"<command> [arguments...]"
            << std::endl;

        return 1;
    }

    wchar_t comspec[
        MAX_PATH
    ]{};

    DWORD length = GetEnvironmentVariableW(
        L"ComSpec",
        comspec,
        MAX_PATH
    );

    if (
        length == 0
        || length >= MAX_PATH
    )
    {
        std::wcerr
            << L"Unable to resolve ComSpec"
            << std::endl;

        return 2;
    }

    std::wstring command =
        QuoteArgument(
            comspec
        )
        + L" /S /C ";

    for (
        int index = 1;
        index < argc;
        ++index
    )
    {
        if (index > 1)
        {
            command += L" ";
        }

        command += QuoteArgument(
            argv[index]
        );
    }

    return Launch(
        comspec,
        command
    );
}
