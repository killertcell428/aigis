# Role profiles

A profile answers "who may do what" for one group of people, as a combination of
six capabilities. `aigis profile build` turns it into both layers at once — the
Aigis policy and Claude Code's own permission settings — so the two cannot drift.

```bash
aigis profile show  profiles/marketing.json            # what it allows and blocks
aigis profile build profiles/marketing.json            # write policy + settings
aigis profile build profiles/marketing.json --managed  # managed-settings.json form
```

## The six axes

| Axis | Values |
|---|---|
| `web` | `none` · `read` |
| `files` | `none` · `read` · `workspace` · `unrestricted` |
| `shell` | `none` · `unrestricted` |
| `git` | `none` · `local` · `push` |
| `packages` | `none` · `unrestricted` |
| `mcp` | `none` · `approved` · `unrestricted` |

**An axis you leave out gets the most restrictive value.** Silence does not grant
capability, so a half-written profile fails closed rather than open.

## The three files here are starting points, not answers

They encode assumptions about what "marketing" or "design" means, and those
assumptions are probably wrong for your company. Copy one, change it, and keep it
in your own repository. The Mercari write-up that prompted this design says the
same thing about its own settings: they reflect one company's business, data, and
size, and copying them unexamined is the mistake.

What is *not* adjustable is the baseline underneath — credential files, SSH keys,
`rm -rf`, piping a download into a shell. No combination of capabilities weakens
it.

## Why there is no "ask the user" option

Earlier drafts had `shell: allowlist`, which would have meant "these commands are
fine, prompt for the rest". It was removed on purpose. A prompt only protects
someone who can judge it; in practice a non-engineer either approves everything,
which defeats the prompt, or refuses everything, which stops the work. So the
capability layer emits allow and deny only, and the judgement happens here — once,
with context, for the whole group — rather than mid-task for each person.

The same reasoning removed `packages: approved`. Deciding whether a specific npm
package is acceptable is not a question to put in front of someone who is trying
to finish something else.
