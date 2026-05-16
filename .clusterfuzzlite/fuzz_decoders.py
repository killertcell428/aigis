"""Fuzz the decoder layer.

Decoders (base64, hex, url, rot13, invisible-tag stripping, confusables) are
attack surface — adversarial inputs try to smuggle payloads past detection by
double-encoding or using malformed encodings. Crashes here turn into bypasses.
"""
import sys

import atheris

with atheris.instrument_imports():
    from aigis import decoders


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
    try:
        decoders.normalize_confusables(text)
        decoders.strip_emojis(text)
        decoders.decode_base64_payloads(text)
        decoders.decode_hex_payloads(text)
        decoders.decode_url_encoding(text)
        decoders.decode_rot13(text)
        decoders.detect_invisible_tags(text)
        decoders.strip_invisible_tags(text)
        decoders.decode_all(text)
    except (UnicodeError, ValueError):
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
