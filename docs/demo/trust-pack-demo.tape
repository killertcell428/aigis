# Aigis `trust-pack` demo — VHS tape
# Produces a clean, reproducible GIF of the "pip install → IT approval pack" flow.
#
# Prerequisites:
#   - charmbracelet/vhs  (https://github.com/charmbracelet/vhs)  →  `brew install vhs` / see repo
#   - ttyd, ffmpeg (vhs installs/uses these)
#
# Render:
#   vhs docs/demo/trust-pack-demo.tape
#   → writes docs/demo/trust-pack-demo.gif
#
# Then reference it in README.md, e.g.:
#   <img src="https://raw.githubusercontent.com/killertcell428/aigis/master/docs/demo/trust-pack-demo.gif" width="700" />

Output docs/demo/trust-pack-demo.gif

Set Shell      "bash"
Set FontSize   16
Set Width      1200
Set Height     760
Set Theme      "Dracula"
Set TypingSpeed 45ms
Set Padding    24

# --- Setup: a clean demo project (kept off-screen-fast) ---
Hide
Type "cd $(mktemp -d) && clear" Enter
Sleep 500ms
Show

# --- 1. The pitch line ---
Type "# Your company won't approve Claude Code? Answer IT in 3 commands." Enter
Sleep 1500ms

# --- 2. Install (already cached; shows the one-liner) ---
Type "pip install pyaigis" Enter
Sleep 2s

# --- 3. Turn on guardrails + audit log for Claude Code ---
Type "aigis init --agent claude-code --policy enterprise" Enter
Sleep 2500ms

# --- 4. Generate the IT-approval pack from the live config ---
Type "aigis trust-pack --lang both --format html" Enter
Sleep 3s

# --- 5. Show what landed on the security team's desk ---
Type "ls aigis-trust-pack/" Enter
Sleep 2500ms

# --- 6. Prove the audit log can't be silently tampered with ---
Type "aigis audit verify" Enter
Sleep 3s

Type "# That folder + the verify command IS the IT approval kit." Enter
Sleep 2500ms
