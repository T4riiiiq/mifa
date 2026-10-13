#ifndef MIFA_REFLECTIVE_H
#define MIFA_REFLECTIVE_H

/*
 * Mifa Reflective DLL ABI v1
 *
 * A DLL compatible with Mifa Reflective DLL Injection
 * must export a function named:
 *
 *     ReflectiveLoader
 *
 * The loader implementation belongs to the DLL.
 * Mifa validates the contract and invokes the exported
 * loader through the selected reflective technique.
 */

#define MIFA_REFLECTIVE_ABI_VERSION 1
#define MIFA_REFLECTIVE_REQUIRED_EXPORT "ReflectiveLoader"

#endif
