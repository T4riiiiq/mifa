# Mifa


<p align="center">
  <img src="docs/mifa-oven.png" alt="Mifa" width="100%">
</p>

## Why Mifa?

Mifa started from a simple idea: **a technique oven**.

Testing Windows execution techniques often involves repeating the same preparation steps — choosing a payload, validating compatibility, generating source, compiling, and checking the final artifact.

Mifa brings that workflow into one place.

```text
Technique → Payload → Validate → Build → Test
```

**Less time preparing. More time testing.**

## Techniques

- DLL Injection
- Remote Thread Injection
- Process Hollowing
- Reflective DLL Injection

## What Mifa Handles

- Payload preparation
- Compatibility validation
- Source generation
- MinGW-w64 compilation
- Build metadata
- Post-build verification

## Payload Sources

Mifa can work with local payloads, external tools, and **msfvenom** where supported.

## Requirements

- Python 3
- MinGW-w64
- msfvenom *(optional)*

## Usage

Clone the repository:

```bash
git clone https://github.com/T4riiiiq/mifa.git
cd mifa
python3 mifa.py
```

List available techniques:

```bash
python3 mifa.py techniques
```

## Scope

Mifa is intended for controlled and authorized security research and training environments.
