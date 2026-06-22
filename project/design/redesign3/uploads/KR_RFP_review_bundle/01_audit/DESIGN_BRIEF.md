# Design-Session Brief — Kroger Produce RFP Platform

A one-page orientation for an external UX/UI design session (e.g. Claude Design). Pair it with the
three inputs in this bundle: the **As-Built Specification** (`07_…`, ground truth), the **screenshots**
(what the web is today), and the **output files** (the Excel artifacts — the richness to bring on-screen).

## What we're building
An enterprise **Kroger produce RFP / sourcing** web app — today a **single-operator** tool that runs a
sourcing cycle end to end (setup → bids → analysis → award → post-award → comms). Thesis: **AI-generated,
not AI-managed** — the system *recommends and prepares*; a human *asserts* every governed decision
(award, adjustment, send), and every assertion is audit-evented.

## Form factor & stack (what output we expect)
- **Responsive web app, desktop-first.** It's an analyst/buyer tool used at a desk, data-dense. Baseline
  viewport **1440px** (the screenshots are 1440px); should degrade gracefully narrower, but mobile is not
  a priority.
- **Stack:** Next.js (app router) + React 18 + TypeScript + **Tailwind CSS**; FastAPI backend (JSON API).
  Designs should produce **React + Tailwind-compatible** output. Claude Design can export to **Vercel**,
  which is the natural frontend host (see platform note below).
- **Not** mobile-native, not desktop-native, not a spreadsheet replacement — a governed web console.

## Hosting platform (status)
**Not vendor-locked yet** — and it does **not** change the UI/UX design (same Next.js app wherever it
runs). The decided *shape*, optimized for longevity via portability (and explicitly **not Azure**):
a containerized **managed PaaS + managed Postgres**, with the **Next.js frontend on Vercel** (which also
makes a Claude-Design → deploy handoff trivial). So for design purposes: target a **standard responsive
web app**; the host is an infra detail settled later.

## The screens today (6, + a bonus state) — see `/screens`
Login (+2FA) · Dashboard/runs list · Run detail (kanban) · Bid intake · **Alignment** (run analysis,
compare 7 scenario lenses, freeze) · **Awards** (frozen award + record post-award adjustment).

## The single biggest design question (gap G-I)
The **alignment/comparison workbench lives only in Excel** today (the `04_…alignment` output file — ~18
tabs: a **Supplier Comparison centerpiece**, a live **Custom Scenario builder**, expandable **drill-downs**,
Lowest-Cost Check, Coverage, Detailed Scoring, Landed & Hidden Costs, Incumbent Retention, Share &
Relationships, Negotiation Dynamics, a pivot-ready data tab). The **web alignment screen surfaces only a
thin slice** (a 7-lens comparison table + a per-cell detail + freeze). **The core ask: design how that
analytical workbench comes onto the screen** — that's the highest-value surface to get right.

## Surfaces that don't exist yet (design net-new)
Capacity check (E-38, built but not surfaced), comms draft review/send (E-37), sign-off, close-out, the
documents/generate-send surface. The audit's gap register (§Exec, §20) is the authoritative list.

## Design constraints to honor
- **Decision-support framing** — the UI *recommends*; the human selects/asserts. No language or affordance
  that implies the system auto-decides (engine output is labelled accordingly).
- **Governed actions are deliberate** — freeze, adjustment, (future) sign-off/send are explicit, confirmed,
  audit-evented steps, not casual clicks.
- **Names, not keys** — everything user-facing renders human names; surrogate IDs stay hidden.
- This is advisory input — per governance it is **not canonical**; it feeds the Phase-4 consolidation review.
