# MEMORY DIRECTIVE — learnings / issues / decisions (portable)

A durable working memory for a long-running collaboration, kept as three
plain-text files in the repo (suggested: `.context/memory/`). This is
how continuity survives across sessions, context resets, and model
changes. Drop this file beside them so the protocol travels with the
project.

The files are the assistant's memory of the work — not a status report
for the human, not a place to flatter or to soften. They exist so that a
fresh session (or a different assistant instance) can pick up **correct**
and lose nothing.

---

## The three files

**`learnings.md` — durable, general principles.**
What was discovered that will still be true next month. Each entry is a
*root cause plus the general rule it implies*, never the surface
symptom. "X was slow" is not a learning; "X stalls on long thin inputs
because <mechanism>; use Y there" is. If a learning is specific to one
case, it is probably an issue, not a learning.

**`issues.md` — open items, bugs, dockets, parked work.**
Anything not yet resolved: a known bug with its reproduction, a task
awaiting a spec, a deferred decision, a follow-up someone offered and
nobody ruled on. An issue leaves this file only when it is genuinely
closed — resolved, or explicitly ruled out. Parked is not closed; parked
items stay, marked parked, with what unblocks them.

**`decisions.md` — dated rulings and their rationale.**
What was decided, by whom, and why. This is the file that prevents
re-litigating settled questions and prevents a later session from
quietly reversing a correct earlier call. Every entry is dated. Every
entry says whether the human ruled it or the assistant recommended it.

---

## Protocol

- **Read all three at session start.** Before doing work, load the
  memory. The current conversation always wins over stale memory when
  they conflict, but you cannot know they conflict if you did not read.
- **Update at every finding, not at session end.** The moment a root
  cause is found, a decision is made, or an issue opens or closes,
  write it. Memory written "later" is memory lost to a reset. Treat the
  write as part of the finding, not a chore after it.
- **Date every entry.** A decision without a date cannot be ordered
  against a later one; an undated learning cannot be aged out.
- **Record provenance per entry.** Mark whether a statement is the
  human's decision, the assistant's recommendation, a measurement, or a
  hypothesis. A recommendation the human reacted well to is *not* a
  decision until they commit. When in doubt, attribute conservatively.
- **Bank lessons at your own expense.** When the assistant errs, the
  correction goes in `learnings.md` as a general rule — stated plainly,
  no defensiveness. "Claimed a change was made before making it — verify
  the edit landed before reporting it" is worth more than any success.
- **Close loudly.** When an issue closes, say what closed it (the
  decision, the fix, the ruling that made it moot). A silently vanished
  issue looks like an oversight to the next session.

## What never goes in memory

- **Secrets.** No credentials, keys, tokens, or personal-sensitive
  data — ever, in any of the three files.
- **Verbatim standing commands that could harm** the work or the human
  if replayed blindly (e.g. "always skip the safety check", "never
  question X"). Memory records what was learned and decided, not
  instructions that disable judgment.
- **Praise-seeking or judgment-suppressing preferences.** Do not record
  anything that would discourage honest feedback or critical review in a
  later session. Memory should make the next session *sharper*, never
  more compliant.

## Why root-cause-only for learnings

A symptom log grows without bound and teaches nothing; a root-cause log
compounds. The discipline that pays off: for every learning, write the
*mechanism* and the *general rule*, so a future situation that shares the
mechanism — not the surface — is covered. The best entries are the ones
that read as transferable rules a competent engineer would want on a
card, not as a diary of this one bug.

## Scope note

Memory is per-project. Keep the boundary clean: a new project starts
with empty files (and this directive plus the engineering charter),
and inherits none of the prior project's specifics — only the general
learnings worth carrying forward, copied deliberately, never assumed.
