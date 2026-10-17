# Mifa

**A reproducible build and validation workflow for Windows security technique research.**

Mifa provides a consistent workflow around existing Windows security techniques.

The techniques already exist. Mifa focuses on the work around testing them consistently: payload preparation, compatibility checks, source generation, compilation, validation, and build reporting.

## Why Mifa?

Testing an existing technique often means repeating the same setup for every experiment.

Mifa provides one consistent workflow to:

- Prepare payloads consistently
- Catch architecture and format mismatches early
- Build technique implementations reproducibly
- Preserve hashes, compiler details, and build metadata
- Compare previous experiments
- Generate a report for each completed build

## Supported Techniques

| Technique | Implementation |
|---|---|
| DLL Injection | LoadLibrary-based DLL injection |
| Process Hollowing | Suspended-process entry-point overwrite variant |
| Reflective DLL Injection | In-memory loading of a compatible reflective DLL |
| Remote Thread Injection | Remote thread execution of a raw payload |

## Interactive Workflow

The current interactive workflow is intentionally **Windows x64 only**.

Start Mifa:

```bash
python3 mifa.py

Select a technique:
1  DLL Injection
2  Process Hollowing
3  Reflective DLL Injection
4  Remote Thread Injection

q  Exit

For DLL Injection, Process Hollowing, and Remote Thread Injection, Mifa uses msfvenom automatically and prompts for a payload module:
Payload module

  Example: windows/x64/exec

> windows/x64/exec

Optional msfvenom parameters are passed dynamically using KEY=VALUE syntax:
Payload options

> CMD=calc.exe

Multiple options are supported:
KEY=VALUE KEY=VALUE

Values containing spaces can be quoted:
CMD="cmd.exe /c whoami"

Reflective DLL Injection uses the Mifa built-in reflective DLL automatically.
Before building, Mifa presents a review with sensitive option values redacted.
Workflow
Technique
    ↓
Payload configuration
    ↓
Build review
    ↓
Source generation
    ↓
Compilation
    ↓
Preflight validation
    ↓
Build report

Direct CLI
The direct CLI exposes the lower-level build options, including explicit architecture and payload provider selection:
python3 mifa.py build \
  --technique <technique> \
  --arch <architecture> \
  --provider <provider> \
  --payload <payload>

Available providers can include:
- Local files
- External artifacts
- msfvenom
- Mifa built-in reflective DLL
Use the built-in help for the current options:
python3 mifa.py build --help

Commands
Command	Purpose
python3 mifa.py	Start interactive mode
python3 mifa.py techniques	List available techniques
python3 mifa.py payloads	List payload providers
python3 mifa.py builds	List recent builds
python3 mifa.py builds --all	List all recorded builds
python3 mifa.py show <BUILD_ID>	Show build details
python3 mifa.py preflight <BUILD_ID>	Validate a completed build
python3 mifa.py report <BUILD_ID>	Generate a build report
python3 mifa.py build --help	Show build options
python3 mifa.py --verbose	Enable verbose output
python3 mifa.py --no-color	Disable terminal colors


Requirements
- Python 3
- MinGW-w64
- msfvenom for msfvenom-backed builds
Validation
Mifa currently validates the build artifact, architecture, payload compatibility, hashes, and build metadata.
Runtime behavior and security-product observations are tested separately and are not implied by a successful preflight result.
Scope
Mifa is intended for controlled and authorized security research, training, and technique validation.
License
MIT
