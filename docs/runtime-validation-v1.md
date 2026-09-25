# Runtime Validation v1

Runtime validation was performed on a controlled Windows x64 lab host.

## Command

Validated both x64 and x86 builds.

Observed behavior:

- Child process created successfully.
- `whoami` executed successfully.
- Process returned exit code `0`.

Status: `runtime-tested`

## Local DLL

Validated both x64 and x86 builds using the Windows `version.dll` system library.

Observed behavior:

- DLL loaded successfully.
- Module path was resolved.
- DLL unloaded successfully.

Status: `runtime-tested`

## Script

Validated both x64 and x86 builds using a benign PowerShell script.

Observed behavior:

- Script process created successfully.
- x64 execution reported AMD64 process architecture.
- x86 execution reported x86 process architecture.
- Both executions returned exit code `0`.

Status: `runtime-tested`

## Managed

Both x64 and x86 wrapper artifacts compile and pass build preflight.

Runtime validation of the managed DLL path was not completed because the Windows lab host did not have the `dotnet` runtime installed.

Status: `build-tested`
