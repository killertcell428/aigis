"""Fuzz `aigis.scan_messages()` with synthesized OpenAI-style message lists.

scan_messages() handles multi-turn structure (role/content), which is a richer
attack surface than plain scan() — role spoofing, content-type confusion,
nested encoding inside assistant turns, etc.
"""
import sys

import atheris

with atheris.instrument_imports():
    import aigis


_ROLES = ("system", "user", "assistant", "tool", "function", "")


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    n = fdp.ConsumeIntInRange(0, 12)
    messages: list[dict] = []
    for _ in range(n):
        role_idx = fdp.ConsumeIntInRange(0, len(_ROLES) - 1)
        # Bound per-message content so a single huge string doesn't dominate.
        chunk = fdp.ConsumeUnicodeNoSurrogates(min(2048, fdp.remaining_bytes()))
        messages.append({"role": _ROLES[role_idx], "content": chunk})
    try:
        aigis.scan_messages(messages)
    except (UnicodeError, ValueError, TypeError, KeyError):
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
