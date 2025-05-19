"""Helper functions for eccodes."""

import eccodes


def release_handle(handle):
    if handle is not None:
        eccodes.codes_release(handle)
