#include <windows.h>

#include <algorithm>
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


static std::wstring LowerExtension(
    const std::wstring& path
)
{
    size_t dot = path.find_last_of(
        L'.'
    );

    if (
        dot == std::wstring::npos
    )
    {
        return L"";
    }

    std::wstring extension =
        path.substr(
            dot
        );

    std::transform(
        extension.begin(),
        extension.end(),
        extension.begin(),
        ::towlower
    );

    return extension;
}


static int Launch(
    const wchar_t* application,
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
        application,
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

        return 3;
    }

    std::wcout
        << L"[+] Managed process created"
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
            << L"Usage: mifa-managed.exe "
            << L"<application.exe|assembly.dll> "
            << L"[arguments...]"
            << std::endl;

        return 1;
    }

    const std::wstring target =
        argv[1];

    const std::wstring extension =
        LowerExtension(
            target
        );

    std::wstring command_line;
    const wchar_t* application = nullptr;

    if (extension == L".dll")
    {
        command_line =
            L"dotnet.exe "
            + QuoteArgument(
                target
            );
    }
    else if (extension == L".exe")
    {
        application =
            target.c_str();

        command_line =
            QuoteArgument(
                target
            );
    }
    else
    {
        std::wcerr
            << L"Managed target must be "
            << L".dll or .exe"
            << std::endl;

        return 2;
    }

    for (
        int index = 2;
        index < argc;
        ++index
    )
    {
        command_line += L" ";
        command_line += QuoteArgument(
            argv[index]
        );
    }

    return Launch(
        application,
        command_line
    );
}
