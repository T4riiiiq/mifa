# Mifa

**A reproducible build and validation workflow for Windows security technique research.**

**Current version:** `1.2.0`

Mifa does not try to reinvent Windows execution or injection techniques. It standardizes the work around testing them consistently: payload preparation, compatibility checks, source generation, compilation, preflight validation, metadata capture, and build reporting.

The result is a repeatable workflow where the payload, provider, architecture, and technique can be changed without rebuilding the surrounding process every time.

## Why Mifa?

Security technique testing often becomes a collection of one-off scripts, compiler commands, payload-generation steps, and manually recorded results.

Mifa provides one workflow to:

- Prepare payloads consistently
- Validate payload format and architecture before runtime testing
- Build technique implementations reproducibly
- Preserve hashes, compiler details, provider metadata, and build configuration
- Compare previous experiments
- Re-run preflight checks against completed builds
- Export a report for each build

## Supported Techniques

| Technique | Implementation | Payload | Architecture |
|---|---|---|---|
| DLL Injection | `LoadLibrary`-based DLL injection | PE DLL | x64 / x86 |
| Process Hollowing | Suspended-process entry-point overwrite variant | Raw payload | x64 / x86 |
| Reflective DLL Injection | In-memory loading of a DLL exporting `ReflectiveLoader` | PE DLL | x64 |
| Remote Thread Injection | Remote thread execution of a raw payload | Raw payload | x64 / x86 |

> Process Hollowing in Mifa is specifically the **entry-point overwrite variant**. It should not be interpreted as full image replacement.

## Quick Start

```bash
git clone https://github.com/T4riiiiq/mifa.git
cd mifa
python3 mifa.py
```

Interactive mode is intentionally **Windows x64 only** and guides the build from technique selection through preflight validation.

```text
Select technique

  1  DLL Injection
  2  Process Hollowing
  3  Reflective DLL Injection
  4  Remote Thread Injection

  q  Exit
```

For DLL Injection, Process Hollowing, and Remote Thread Injection, interactive mode uses the `msfvenom` provider and prompts for a Windows x64 payload module.

Example:

```text
Payload module

> windows/x64/exec

Payload options

> CMD="cmd.exe /c whoami"
```

Optional payload parameters use `KEY=VALUE` syntax. Multiple values may be supplied on the same line, and values containing spaces may be quoted.

Reflective DLL Injection uses Mifa's built-in reflective DLL automatically in interactive mode.

Before compilation, Mifa displays a build review and redacts option values while preserving their keys.

## Workflow

```text
Technique
    ↓
Payload configuration
    ↓
Build review
    ↓
Payload preparation
    ↓
Source generation
    ↓
Compilation
    ↓
Preflight validation
    ↓
Build metadata / report
```

## Direct CLI

The direct CLI exposes the lower-level build controls, including architecture, provider, payload type, transform, build type, and provider-specific options.

General form:

```bash
python3 mifa.py build \
  --technique <technique> \
  --arch <x64|x86> \
  --provider <provider> \
  --payload <payload>
```

Example using a local raw payload:

```bash
python3 mifa.py build \
  --technique remote-thread \
  --arch x64 \
  --provider file \
  --payload ./payload.bin
```

Example using the `msfvenom` provider with a benign command payload:

```bash
python3 mifa.py build \
  --technique remote-thread \
  --arch x64 \
  --provider msfvenom \
  --payload windows/x64/exec \
  --msf-option CMD=calc.exe
```

Reflective DLL Injection with the built-in payload:

```bash
python3 mifa.py build \
  --technique reflective-dll \
  --arch x64 \
  --provider reflective-builtin
```

Use the built-in help for the authoritative option list:

```bash
python3 mifa.py build --help
```

## Payload Providers

Mifa currently includes four providers:

| Provider | Purpose |
|---|---|
| `file` | Use a local payload file |
| `external` | Use an externally produced payload artifact |
| `msfvenom` | Generate a payload through `msfvenom` |
| `reflective-builtin` | Build and use Mifa's built-in reflective DLL |

Provider compatibility is enforced by each technique's payload contract.

## Reflective DLL Contract

Reflective DLL Injection accepts compatible x64 PE DLLs that export:

```text
ReflectiveLoader
```

The built-in reflective provider uses Mifa's reflective loader ABI v1.

## Commands

| Command | Purpose |
|---|---|
| `python3 mifa.py` | Start interactive mode |
| `python3 mifa.py techniques` | List available techniques |
| `python3 mifa.py techniques --all` | Include hidden techniques |
| `python3 mifa.py payloads` | List payload providers |
| `python3 mifa.py builds` | List recent builds |
| `python3 mifa.py builds --all` | List all recorded builds |
| `python3 mifa.py show <BUILD_ID>` | Show build details |
| `python3 mifa.py preflight <BUILD_ID>` | Re-run preflight validation |
| `python3 mifa.py report <BUILD_ID>` | Export a build report |
| `python3 mifa.py build --help` | Show direct build options |
| `python3 mifa.py --verbose` | Enable verbose output |
| `python3 mifa.py --no-color` | Disable ANSI color output |

## Preflight Validation

A successful build is followed by preflight validation. Depending on the technique and payload contract, Mifa verifies items such as:

- Build artifact existence
- Artifact hash integrity
- Expected architecture
- Payload compatibility
- Payload round-trip integrity where applicable
- Recorded build metadata

Preflight validates the **build and artifact**, not the runtime outcome.

A `PASS` therefore means the generated artifact is internally consistent with the recorded build contract. It does **not** imply that execution will succeed on every Windows host or that a security product will allow the artifact to run.

## Runtime Validation

Runtime testing is intentionally kept separate from preflight.

The current technique set has been exercised in a controlled Windows lab with benign validation payloads, including:

- Remote Thread Injection with a minimal raw payload
- DLL Injection with a benign x64 DLL
- Process Hollowing entry-point overwrite with a minimal raw payload
- Reflective DLL Injection with the built-in reflective DLL

Runtime and security-product observations are environment-specific and are not treated as universal evasion claims.

## Requirements

- Python 3
- MinGW-w64
- `msfvenom` for builds using the `msfvenom` provider

The built-in reflective provider also requires the toolchain needed to compile its DLL payload.

## Project Layout

```text
mifa.py          CLI and interactive workflow
core/            Build, validation, and reporting logic
providers/       Payload providers
techniques/      Technique manifests and source templates
payloads/        Payload-related assets
sdk/             Supporting SDK components
tests/           Automated test suite
ui/              Console presentation helpers
```

## Scope

Mifa is intended for controlled and authorized security research, training, lab validation, and comparative technique testing.

It is a build and validation framework, not a claim that any technique or generated artifact will bypass a particular security product.

## License

MIT
