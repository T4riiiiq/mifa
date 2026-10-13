# Mifa


<p align="center">
  <img src="docs/mifa-oven.png" alt="Mifa" width="100%">
</p>

## Why Mifa?

Mifa started from a simple idea: **a technique oven**.

When testing Windows execution techniques, a lot of time is spent repeating the same preparation work — selecting a payload, checking compatibility, generating the build, compiling it, and validating the final artifact.

Mifa puts that workflow in one place.

```text
Technique → Payload → Validate → Build → Test

The goal is simple: less time preparing, more time testing.
Techniques
Mifa currently supports:
- DLL Injection
- Remote Thread Injection
- Process Hollowing
- Reflective DLL Injection
What Mifa Handles
- Payload preparation
- Compatibility validation
- Source generation
- MinGW-w64 compilation
- Build metadata
- Post-build verification
Payload Sources
- Local files
- External tools
- msfvenom, where supported
Requirements
- Python 3
- MinGW-w64
- msfvenom — optional
Usage
Clone the repository:
git clone https://github.com/T4riiiiq/mifa.git
cd mifa
python3 mifa.py

List available techniques:
python3 mifa.py techniques

Scope
Mifa is built for controlled and authorized security research and training environments.
