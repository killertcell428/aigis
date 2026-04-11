"""Built-in safety specifications for common use cases.

Two specs are provided out of the box:

* **DEFAULT_SAFETY_SPEC** -- sensible defaults for a development
  environment: allows common dev tools, forbids credential files
  and destructive commands.
* **STRICT_SAFETY_SPEC** -- locked-down spec for read-heavy or
  audit-sensitive environments: only allows file reads and
  Markdown/text writes; blocks all shell, network, and hidden-file
  access.
"""

from __future__ import annotations

from aigis.safety.spec import EffectSpec, Invariant, SafetySpec

DEFAULT_SAFETY_SPEC = SafetySpec(
    name="default",
    version="1.0",
    allowed_effects=[
        EffectSpec("file:read", "*"),
        EffectSpec("file:write", "**/*.{py,js,ts,md,txt,yaml,json,toml,cfg}"),
        EffectSpec("shell:exec", "git *"),
        EffectSpec("shell:exec", "python *"),
        EffectSpec("shell:exec", "npm *"),
        EffectSpec("shell:exec", "pip *"),
        EffectSpec("network:fetch", "*.github.com"),
        EffectSpec("network:fetch", "*.pypi.org"),
    ],
    forbidden_effects=[
        EffectSpec("file:write", ".env*"),
        EffectSpec("file:write", "**/credentials*"),
        EffectSpec("file:write", "**/.ssh/*"),
        EffectSpec("file:write", "**/secrets*"),
        EffectSpec("shell:exec", "*rm -rf*"),
        EffectSpec("shell:exec", "*sudo*"),
        EffectSpec("shell:exec", "*mkfs*"),
        EffectSpec("network:send", "*pastebin*"),
        EffectSpec("network:send", "*webhook.site*"),
        EffectSpec("network:send", "*ngrok*"),
    ],
    invariants=[
        Invariant(
            "no_secrets_in_output",
            "check_no_secrets_in_output",
            "Output must not contain API keys or passwords",
        ),
        Invariant(
            "no_path_traversal",
            "check_path_traversal",
            "File paths must not contain directory traversal",
        ),
    ],
)

STRICT_SAFETY_SPEC = SafetySpec(
    name="strict",
    version="1.0",
    allowed_effects=[
        EffectSpec("file:read", "*"),
        EffectSpec("file:write", "**/*.{md,txt}"),
    ],
    forbidden_effects=[
        EffectSpec("shell:exec", "*"),
        EffectSpec("network:send", "*"),
        EffectSpec("network:fetch", "*"),
        EffectSpec("file:write", ".*"),
    ],
    invariants=[
        Invariant(
            "no_secrets_in_output",
            "check_no_secrets_in_output",
            "Output must not contain secrets",
        ),
        Invariant(
            "no_pii_in_output",
            "check_no_pii_in_output",
            "Output must not contain PII",
        ),
        Invariant(
            "no_path_traversal",
            "check_path_traversal",
            "No directory traversal",
        ),
    ],
)
