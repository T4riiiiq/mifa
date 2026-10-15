# Mifa

**A reproducible build and validation workflow for Windows security technique research.**

Mifa provides a consistent workflow around existing Windows security techniques.

The techniques already exist. Mifa focuses on the work around testing them consistently: payload preparation, compatibility checks, source generation, compilation, validation, and build reporting.

## Why Mifa?

Testing an existing technique often means repeating the same setup for every experiment.

Mifa provides one consistent workflow that makes it easier to:

- Switch between supported payload sources
- Catch architecture and format mismatches early
- Build technique implementations consistently
- Preserve hashes, compiler details, and build metadata
- Reproduce and compare previous experiments
- Generate a report for each completed build

## Supported Techniques

| Technique | Implementation |
|---|---|
| DLL Injection | LoadLibrary-based DLL injection |
| Remote Thread Injection | Remote thread execution of a raw payload |
| Process Hollowing | Suspended-process entry-point overwrite variant |
| Reflective DLL Injection | In-memory loading of a compatible reflective DLL |

## Payload Sources

Mifa supports:

- Existing local files
- External payload generators
- msfvenom, where supported
- Built-in reflective DLL payloads

## Workflow

1. Select a technique
2. Select the target architecture
3. Select a payload source
4. Validate compatibility
5. Generate and compile the source
6. Validate the resulting artifact
7. Review or export the build report

## Usage

Clone the repository:

```bash
git clone https://github.com/T4riiiiq/mifa.git
cd mifa
```

Start the interactive interface:

```bash
python3 mifa.py
```

Or build directly:

```bash
python3 mifa.py build \
  --technique <technique> \
  --arch <architecture> \
  --provider <provider> \
  --payload <payload>
```

## Commands

| Command | Purpose |
|---|---|
| `python3 mifa.py` | Start interactive mode |
| `python3 mifa.py techniques` | List available techniques |
| `python3 mifa.py payloads` | List payload providers |
| `python3 mifa.py builds` | List recent builds |
| `python3 mifa.py builds --all` | List all recorded builds |
| `python3 mifa.py show <BUILD_ID>` | Show build details |
| `python3 mifa.py preflight <BUILD_ID>` | Validate a completed build |
| `python3 mifa.py report <BUILD_ID>` | Generate a build report |
| `python3 mifa.py build --help` | Show build options |
| `python3 mifa.py --verbose` | Enable verbose output |
| `python3 mifa.py --no-color` | Disable terminal colors |

## Requirements

- Python 3
- MinGW-w64
- msfvenom *(optional)*

## Scope

Mifa is intended for controlled and authorized security research, training, and technique validation.

## License

MIT
