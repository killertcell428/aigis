# Demo assets

Reproducible recordings of Aigis in action. These are scripted (not hand-edited)
so anyone can regenerate the exact same asset.

## `trust-pack` demo (the launch GIF)

The 3-command "from `pip install` to an IT-approval pack" flow, plus
`aigis audit verify`.

### Option A — VHS (recommended, deterministic GIF)

[charmbracelet/vhs](https://github.com/charmbracelet/vhs) turns a text script
into a GIF. No manual recording, identical output every time.

```bash
# install vhs (macOS): brew install vhs   — see the vhs repo for Linux/Windows
vhs docs/demo/trust-pack-demo.tape
# → writes docs/demo/trust-pack-demo.gif
```

Then reference it from the README:

```markdown
<p align="center">
  <img src="https://raw.githubusercontent.com/killertcell428/aigis/master/docs/demo/trust-pack-demo.gif" alt="aigis trust-pack demo" width="700" />
</p>
```

Tweak `FontSize`, `Theme`, `Width/Height`, or `Sleep` timings in the
[`.tape`](./trust-pack-demo.tape) file to taste before rendering.

### Option B — asciinema (terminal recording)

If you prefer a real recording / asciinema embed:

```bash
asciinema rec trust-pack-demo.cast
# then run, in a fresh dir:
#   pip install pyaigis
#   aigis init --agent claude-code --signed-audit
#   aigis trust-pack --lang both --format html
#   ls aigis-trust-pack/
#   aigis audit verify
# Ctrl-D to stop. Convert to GIF with agg:  agg trust-pack-demo.cast trust-pack-demo.gif
```

### The raw command sequence (for any recorder, or a live demo)

```bash
cd "$(mktemp -d)"
pip install pyaigis
aigis init --agent claude-code --signed-audit   # guardrails + audit log ON
aigis trust-pack --lang both --format html           # → aigis-trust-pack/
ls aigis-trust-pack/                                  # the docs IT reviews
aigis audit verify                                    # tamper-evident proof
```

### Recording tips

- Keep it under ~20 seconds — the three commands + `audit verify` are the story.
- Lead with the problem line ("Your company won't approve Claude Code?").
- End on `aigis audit verify` — the "0 tampering detected" line is the strongest single frame.
- A still of the generated `aigis-trust-pack.html` (see [`../sample-trust-pack/`](../sample-trust-pack/))
  makes a good thumbnail / first frame for X and Show HN.
