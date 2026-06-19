---
doc: Email drafting + mail-merge + the LEGALESE style mode
id: EXP-PILOT-EMAIL
squad: Experience / Output
status: Draft (sponsor-specified 2026-06-19) — guides the pilot skill + a mail-merge generator
relates: PILOT_SYSTEM_DESIGN.md, D23 (names), D28 (deterministic, data-derived), ADR-0006
---

# Email drafting + mail merge

A pilot capability with agent involvement: **draft the structure → sponsor approves → generate the
mail-merge template + recipients data from the governed records.** Because the actual sends are
mail-merged from the sealed data, **every email is fully accurate, always** — no hand-typed prices,
suppliers, lots, or dates.

## Workflow

1. **Draft structure.** The pilot drafts the email's STRUCTURE (purpose, recipients, the merge
   fields it will pull, the body skeleton with `{{merge_field}}` placeholders, the tone/mode). It
   shows this to the sponsor for **approval** — nothing sends or finalizes until the structure is
   approved.
2. **Approve.** The sponsor edits/approves the draft structure.
3. **Generate mail merge.** On approval, the pilot generates a **mail-merge template** (the approved
   body with merge fields) + a **recipients data file** (one row per recipient — supplier/buyer
   contact + the exact merge values pulled from the governed store: their awarded lots, prices,
   volumes, DCs, round, dates — names not keys, D23). The pair drops into the run's `outputs/`
   (normalized name, e.g. `NN_round2_invite_mailmerge.docx` + `NN_round2_invite_recipients.csv`),
   committed to the vault.
4. **Send** is the sponsor's action (their mail client / merge), so the human stays in the loop;
   the pilot only produces accurate, approved, data-merged artifacts.

Typical emails: round invitations ("action needed — Round 2 bids due"), award notifications
(per-supplier "here is what you've been awarded" — mail-merged off the frozen award), exception/
negotiation correspondence. Merge values are **deterministic and data-derived** (D28) — pulled from
the sealed records, never improvised.

## Style modes

The draft adopts a **style mode** the sponsor selects. Default is a clear, courteous business voice.
The sponsor can invoke **LEGALESE MODE** (verbatim spec below) for controlled commercial
correspondence — e.g. responding to a counterpart pushing on a settled decision.

### LEGALESE MODE (sponsor-specified, verbatim)

> On "legalese," use a controlled commercial response: neutral, procedural, brief, non-defensive.
> Anchor to process, not opinion. Disclose only what supports the position. Do not volunteer facts,
> calculations, motives, approvals, timelines, alternatives, or precedent. Do not validate or debate
> counterpart, third-party, or competitive claims. Do not imply review, escalation, flexibility, or
> reconsideration unless instructed. Use declarative wording. Structure: acknowledgment, principle,
> application, disposition, close. Objective: preserve position, optionality, and a defensible record.

**Operationalized** — in LEGALESE MODE the pilot:
- Writes in five beats: **acknowledgment → principle → application → disposition → close.**
- Stays neutral, procedural, brief, non-defensive; declarative wording; anchors to **process**.
- Discloses **only** what supports the position; volunteers **no** facts, calculations, motives,
  approvals, timelines, alternatives, or precedent.
- Does **not** validate or debate the counterpart's/third-party/competitive claims; does **not**
  imply review, escalation, flexibility, or reconsideration unless the sponsor instructs it.
- Preserves position, optionality, and a defensible record.
- Still mail-merge-accurate: any figure that appears is a sealed merge value, not an improvisation —
  but legalese mode discloses sparingly, so most figures are simply omitted unless they support the
  position.

The pilot always shows the draft for approval before any mail-merge artifact is generated.
