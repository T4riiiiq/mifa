# Mifa

**Technique-first Windows build utility for security research.**

<p align="center">
  <img src="docs/mifa-oven.png" alt="Mifa" width="100%">
</p>

## Why Mifa?

Mifa started from a simple idea: **a technique oven**.

Testing Windows execution techniques often means repeating the same preparation work — selecting a payload, validating compatibility, generating source, compiling, and checking the final artifact.

Mifa puts that workflow in one place.

```text
Technique → Payload → Validate → Build → Test
```

**Less time preparing. More time testing.**

## Built for Security Research

Mifa is designed for security researchers who need a consistent way to prepare and test Windows execution techniques in controlled environments.

Instead of rebuilding the same supporting workflow for every experiment, Mifa keeps payload handling, validation, compilation, and build metadata consistent across techniques.

This makes it easier to:

- Reproduce technique tests
- Compare different implementations
- Keep build artifacts organized
- Validate payload compatibility
- Focus on the technique itself rather than repetitive setup

## Techniques

Mifa currently supports:

- DLL Injection
- Remote Thread Injection
- Process Hollowing
- Reflective DLL Injection

## How It Works

Mifa handles the common steps around each technique:

- Payload preparation
- Compatibility validation
- Source generation
- MinGW-w64 compilation
- Build metadata
- Post-build verification

Payloads can come from:

- Existing files
- External tools
- msfvenom, where supported

## Usage

Clone the repository:

```bash
git clone https://github.com/T4riiiiq/mifa.git
cd mifa
```

Start Mifa:

```bash
python3 mifa.py
```

Running Mifa without a command opens the interactive workflow:

```text
Select Technique
      ↓
Select Architecture
      ↓
Select Payload Source
      ↓
Configure Payload
      ↓
Review Build
      ↓
Build
      ↓
Validate
```

### Commands

| Command | Purpose |
|---|---|
| `python3 mifa.py` | Start interactive mode |
| `python3 mifa.py techniques` | List available techniques |
| `python3 mifa.py payloads` | List payload providers |
| `python3 mifa.py builds` | List recent builds |
| `python3 mifa.py builds --all` | List all recorded builds |
| `python3 mifa.py show <BUILD_ID>` | Show build details |
| `python3 mifa.py preflight <BUILD_ID>` | Verify a completed build |
| `python3 mifa.py report <BUILD_ID>` | Export a build report |

### Direct Build

Mifa can also run directly without the interactive menu:

```bash
python3 mifa.py build \
  --technique <technique> \
  --arch <architecture> \
  --provider <provider> \
  --payload <payload>
```

Additional build options:

```bash
python3 mifa.py build --help
```

Verbose output:

```bash
python3 mifa.py --verbose
```

Disable terminal colors:

```bash
python3 mifa.py --no-color
```

General help:

```bash
python3 mifa.py --help
```

## Requirements

- Python 3
- MinGW-w64
- msfvenom *(optional)*

## Scope

Mifa is intended for controlled and authorized security research and training environments.
