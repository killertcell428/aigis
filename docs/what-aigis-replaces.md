# What Aigis replaces in an AI-agent rollout

Bringing Claude Code into a company is not one task, it is seven. Most of them are
paid for as consulting today. This page says which ones a tool can take over,
which ones it cannot, and — column three — how much of that is actually built.

The third column exists because it is easy to write a positioning page that
describes the finished product. Where Aigis is not there yet, this page says so.

| Work in a rollout | Can Aigis replace it? | Status |
|---|---|---|
| **Permission design** — deciding who may run what | **Yes.** It reduces to a combination of capabilities (see below), not to bespoke judgement | Designed, not built. Today's four `--policy` profiles differ only by name |
| **Writing and distributing settings** | **Yes**, and more accurately than by hand | **Built** — `aigis settings` derives Claude Code's own permission rules from the Aigis policy |
| **Approval and steering-committee documents** | **Yes** | **Built** — `aigis trust-pack` generates the pack from live config |
| **Audit response and evidence** | **Yes** | **Built** — signed, hash-chained audit log plus `aigis audit verify` |
| **Discovery interviews** — working out who needs what | **Half.** The value of an interview is knowing what to ask, and that is a question list | Not built |
| **Organisational buy-in** | **No.** Someone has to sit in the room | Out of scope |
| **Training** | **No.** See the note below | Out of scope |

## Why permission design is replaceable

Because role names are not the unit of design. "Marketing" means one thing at a
company where marketers query the data warehouse and another where they write
copy — so a tool that ships a `marketing` profile ships someone else's
assumptions.

What is stable across companies is the set of things a person needs to be *able
to do*. Six axes cover it:

| Axis | Question it answers |
|---|---|
| `web` | May the agent fetch external content? |
| `files` | What may it read and write? |
| `shell` | May it run commands, and which? |
| `git` | May it commit, push, force-push? |
| `packages` | May it install dependencies? (the supply-chain surface) |
| `mcp` | May it connect external tools, and which? |

A role is then a combination, and the combination is what gets configured:

```
                 Marketing         Design/production   Engineering
                 (research +       (HTML, front-end,   (back-end
                  image gen)        no back-end)        included)
──────────────  ────────────────  ──────────────────  ─────────────────
web             read              read                read
files           documents only    project directory   all but protected
shell           none              npm run only        all but dangerous
git             none              commit, push        push; force = review
packages        none              approved only       unrestricted
mcp             approved only     approved only       unrestricted
```

Underneath sits a **baseline that no combination can weaken**: `.env`, `.ssh`,
credential files, `rm -rf`, piping a download into a shell. Those are denied
regardless of role. So the structure is two layers — a floor nobody can lower,
and a role-shaped layer above it.

This is what makes the work replaceable. A consultant designing permissions is,
in effect, filling in that table for each department. A tool can do the filling
in; it cannot do the deciding, which is why the interview column says "half".

## Why an interview is half-replaceable

Most of the value in a discovery interview is not the conversation, it is knowing
which questions to ask. That part is a list, and a list can ship with the tool —
a wizard that asks the six questions above, per department, produces the same
artefact a consultant's intake sheet produces.

What does not survive the translation is the follow-up: hearing "we don't really
use the terminal" and knowing to ask "then how does the monthly report get
generated?" That still needs a person.

## Why training is out of scope

Because the evidence says configuration alone does not hold. WINTICKET (CyberAgent)
ran a six-session course plus a certification exam for 24 non-engineers before
letting them use Claude Code, and paired it with distributed managed settings —
not one or the other. Their reasoning was that a permission dialog only protects
someone who can read it; otherwise approval fatigue sets in and people click
through.

Aigis generates the settings half of that. It does not teach anyone to read a
command, and shipping a module that claimed to would be the same kind of
overreach this project has been removing.

---

**Related:** [ROADMAP.md](../ROADMAP.md) for what is being built and what has been
dropped · [trust-pack.md](trust-pack.md) for the approval pack ·
[why-aigis.md](why-aigis.md) for how Aigis compares to other tools.
