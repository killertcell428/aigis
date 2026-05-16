"""Fuzz the main `aigis.scan()` entry point.

Goal: detect crashes, ReDoS, encoding errors, or unhandled exceptions when
arbitrary byte sequences are fed through the detector pipeline.
"""
import sys

import atheris

with atheris.instrument_imports():
    import aigis


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    # Pull a Unicode string of arbitrary length; atheris handles surrogates.
    text = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
    try:
        aigis.scan(text)
    except (UnicodeError, ValueError):
        # Input-shape exceptions are expected and not bugs.
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
