# reference/incoming/ — Direct-upload drop zone (raw, sensitive, temporary)

Upload real cycle data here **on this branch** (`claude/wizardly-pasteur-n4acb8`) via
GitHub's web UI ("Add file → Upload files"). This is the landing zone for files too
large for the chat.

## Important (data handling)
- Files here are **raw, sensitive commercial data** (real supplier bids, prices, emails).
- Uploading via GitHub **commits them** — they enter the repo and its history. This repo is
  private; that is the accepted trade-off for the convenience. (ADR-0001's quarantine rule
  otherwise keeps raw data out of the repo entirely — the chat split-upload route does that.)
- **Workflow once you've uploaded:** ping me. I then pull, map the *structure* (headers, tabs,
  templates, round shape), commit only **sanitized** derived artifacts (no real values), and
  `git rm` the raw files from the live tree. History retention can be purged later if needed.

## What to drop (priority order)
1. The **most complete single cycle** you have — all the rounds' **supplier bid workbooks**
   (.xlsx), plus that cycle's **kickoff** and any **award / booking guide** if available.
   (Field Tomatoes looks like a good candidate from what you've sent.)
2. A **smattering of others** — especially a category using the *other* bid template
   (tomato flat sheet ↔ onion 9-tab) to prove multi-template intake.
3. Supplier **emails (.eml)**, prior **booking guides**, **KCMS** exports — all welcome.

`.7z` / `.zip` are fine (I can extract both). Drop them in any structure; I'll sort it out.
