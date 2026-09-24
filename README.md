# Mifa

Mifa is a Kali-side operational build framework designed to reduce repetitive
payload preparation, technique configuration, compilation, and reporting work.

## Design

Mifa remains on Kali.

Generated artifacts are transferred to the target environment when required.

The project focuses only on operational workflows.

Inspection, compatibility experiments, Windows internals labs, and prototype
work are maintained separately in `mifa-framework`.

## Planned Workflow

Input / Payload
      |
      v
Payload Provider
      |
      v
Architecture
      |
      v
Technique
      |
      v
Compatibility Validation
      |
      v
Source Generation
      |
      v
Compilation
      |
      v
Final Artifact
      |
      v
Build Manifest + Report Data

## Planned Interface

- Build
- Payloads
- Techniques
- Builds
- Report
- Verify

## Version

0.1.0
