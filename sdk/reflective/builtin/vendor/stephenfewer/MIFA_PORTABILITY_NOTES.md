# Mifa portability changes

This directory contains vendored source from Stephen Fewer's
ReflectiveDLLInjection project.

The upstream revision is recorded in `UPSTREAM_COMMIT`.

Local changes are limited to compiler/platform portability for the
Mifa MinGW-w64 build:

- normalized the Winsock header filename for case-sensitive hosts;
- added GCC-compatible return-address handling;
- added GCC-compatible rotate handling;
- normalized inline linkage for GCC;
- cleaned the legacy ARM preprocessor branch syntax.

The original license is preserved in `LICENSE.txt`.
