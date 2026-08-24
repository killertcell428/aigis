# Aigis v2.0 demo — role profiles (VHS tape)
#
# Shows the one thing v2.0 is about: a role written once as six capabilities,
# and *both* enforcement layers generated from that single file.
#
#   aigis profile show   → what this role can and cannot do, in plain language
#   aigis profile build  → writes aigis-policy.yaml (hook) + .claude/settings.json (Claude Code)
#   cat settings.json    → the Claude Code side that came out of it
#
# Prerequisites: charmbracelet/vhs (+ ttyd, ffmpeg). See https://github.com/charmbracelet/vhs
# Render locally:  vhs docs/demo/aigis-profile.tape   →   docs/demo/aigis-profile.gif
# In CI:           .github/workflows/demo-gif.yml (workflow_dispatch, tape input).
#
# Embed (README / release notes):
#   <img src="https://raw.githubusercontent.com/killertcell428/aigis/master/docs/demo/aigis-profile.gif" width="760" />

Output docs/demo/aigis-profile.gif

Set Shell       "bash"
Set FontSize    16
Set Width       1200
Set Height      760
Set Theme       "Dracula"
Set TypingSpeed 18ms
Set Padding     20

# Work in a scratch dir, but carry the starter profiles in with us. Rendered from
# the repo root, so profiles/ is present; cd-ing away without copying would leave
# the demo with nothing to build.
Hide
Type "TMP=$(mktemp -d) && cp -r profiles $TMP/ && cd $TMP && clear" Enter
Sleep 400ms
Show

# 1. What this role may do — stated in words, not rule syntax. This is the part a
#    department head or an approver actually reads.
Type "aigis profile show profiles/marketing.json" Enter
Sleep 2600ms

Type "clear" Enter
Sleep 200ms

# 2. One file in, two enforcement layers out. Trimmed to the summary; the full
#    run also lists every rule that could not be expressed as a Claude Code
#    permission, which is too long to read in a clip.
Type "aigis profile build profiles/marketing.json 2>&1 | head -13" Enter
Sleep 2800ms

Type "clear" Enter
Sleep 200ms

# 3. The Claude Code side of that output — the outer gate, generated rather than
#    hand-written. `shell: none` became a Bash deny; `packages: none` became the
#    install denials.
Type "head -10 .claude/settings.json" Enter
Sleep 3000ms
