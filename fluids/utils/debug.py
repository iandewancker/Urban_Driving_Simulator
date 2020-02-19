from __future__ import print_function
import sys

SUPRESS_OUTPUT = True


def fluids_print(s, **kwargs):
    if SUPRESS_OUTPUT:
        return
    print("[FLUIDS] " + str(s), **kwargs)


def fluids_assert(cond, em=None):
    if not cond:
        fluids_print("Error: " + em)
        exit(1)
