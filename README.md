# Mifa

Mifa is a Kali-side operational build framework for repeatable Windows
artifact preparation, configuration, compilation, validation, provenance,
and reporting.

Version: **1.0.0**

## Overview

Mifa keeps the build workflow on Kali and produces Windows artifacts that can
be transferred into a controlled target environment when required.

The framework separates configuration from generated artifacts and records
each build in a dedicated manifest.

Core workflow:

~~~text
Technique
    |
    v
Architecture
    |
    v
Input / Payload
    |
    v
Provider
    |
    v
Compatibility
    |
    v
Processing
    |
    v
Source Generation
    |
    v
Compilation
    |
    v
Artifact
    |
    v
Preflight
    |
    v
Manifest + Report
~~~

## Features

- x64 and x86 Windows builds
- Operational technique contracts
- File and external artifact providers
- Compatibility validation
- Source generation
- MinGW-w64 compilation
- SHA-256 provenance
- Per-build manifests
- Automatic reports
- Artifact preflight validation
- Payload round-trip verification
- Interactive and CLI workflows

## Payload Processing

Mifa supports deterministic processing stages for compatible workflows.

Internal processing order:

~~~text
Input
  |
  v
Compression
  |
  v
Transform
  |
  v
Encoding
  |
  v
Staged Input
~~~

Available transforms:

- None
- XOR
- AES-256-CBC
- AES-256-GCM

Available encoding:

- None
- Base64
- Hex

Available compression:

- None
- Gzip
- Deflate

Processing metadata and hashes are written to the build manifest.

Sensitive transform material is not included in the generated Markdown report.

## Providers

### File

Uses an existing local file as input.

### External

Imports an artifact already created by another tool and records its producer
and source provenance.

Mifa does not automatically invoke external generators.

## Operational Techniques

| Alias | Runtime | Architectures | Validation |
| --- | --- | --- | --- |
| `native` | Native | x64, x86 | runtime-tested |
| `command` | Native | x64, x86 | runtime-tested |
| `local-dll` | Native | x64, x86 | runtime-tested |
| `script` | Script | x64, x86 | runtime-tested |
| `managed` | Managed | x64, x86 | build-tested |

The managed workflow requires an appropriate .NET runtime on the Windows host
for managed DLL execution.

## Installation

On Kali:

~~~bash
sudo apt update
sudo apt install -y python3 python3-venv mingw-w64

git clone https://github.com/T4riiiiq/mifa.git
cd mifa

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
~~~

## Interactive Usage

Start Mifa with:

~~~bash
python3 mifa.py
~~~

Main interface:

~~~text
[1] Build
[2] Builds
[3] Techniques
[0] Exit
~~~

A successful build automatically performs preflight validation and generates
a report.

## CLI Usage

List techniques:

~~~bash
python3 mifa.py techniques
~~~

Build the native process launcher:

~~~bash
python3 mifa.py build \
  --technique native \
  --arch x64
~~~

Build the command wrapper:

~~~bash
python3 mifa.py build \
  --technique command \
  --arch x64
~~~

List previous builds:

~~~bash
python3 mifa.py builds
~~~

Inspect a build:

~~~bash
python3 mifa.py show K-0001
~~~

Run preflight:

~~~bash
python3 mifa.py preflight K-0001
~~~

Generate or refresh its report:

~~~bash
python3 mifa.py report K-0001
~~~

## Build Layout

Each build receives an immutable-style identifier:

~~~text
builds/
└── K-0001/
    ├── input/
    ├── source/
    ├── output/
    ├── build.json
    └── REPORT.md
~~~

Central report copies are written under:

~~~text
reports/
~~~

The manifest records:

- Build identifier
- Technique
- Architecture
- Configuration
- Provider provenance
- Input metadata
- Processing metadata
- Generated sources
- Compiler
- Compiler command
- Artifact path
- Artifact size
- SHA-256

## Preflight

Preflight checks the generated artifact before transfer.

Current checks include:

- Build status
- Artifact existence
- SHA-256 integrity
- PE architecture
- Expected architecture
- Payload round-trip state when applicable

## Development Checks

~~~bash
python3 -m unittest discover -s tests -v
git diff --check
~~~

## Scope

Mifa is designed for controlled security labs and authorized environments.

It does not automatically fingerprint endpoint security products, select
security-control adaptations, disable security controls, or perform automatic
mutation loops.

Inspection and prototype material is maintained separately from the operational
framework.
