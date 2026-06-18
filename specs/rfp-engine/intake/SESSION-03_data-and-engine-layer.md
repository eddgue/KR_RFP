# Data + Engine Layer

**Date:** 2026-06-17
**Source:** Real iTrade feeds (6 commodity pulls), Ed's normalization Norm sheet, 8 supplier bids (3 onion, 5 tomato), the HO booking guide, the tomato R3 Analysis file, and three RD2 Allocation models (Sweet Potato, Hybrid Onion, Colored Potato).

This session covers everything between the setup file and the award: how bids arrive, how they normalize, how they become a comparable number, how scenarios get built, and how the award and booking guide come out. The headline: **Ed has already built the whole engine in Excel, across three generations. The newest Allocation model is the target architecture. The system productizes it and parameterizes the parts he forks by hand.**

---

## 1. The iTrade feed (the transactional spine)

iTrade is not a price series. It is **every PO receipt**, one row per line. The standard export ("Data" sheet, 43 columns) carries:

- **Identity:** Commodity desc, SubCommodity desc (the anchor), DC No/Name, UPC, Case Size, weights, ship pack qty.
- **Vendor / origin:** Vendor Name, Shipping Address, State, Zip = **ship-from, not grow-origin**.
- **Cost components:** Final Price (FOB), Freight, Total Case Cost with Freight (delivered), Cross Dock charges, Total Cross-Dock. Plus a `Routing` field (Delivered / FOB / …).
- **Performance:** Quantity Shipped, Quantity Received, QC Reject Qty, and the date chain (creation, ship request, shipped, received).
- **Fiscal:** Year/Period/Week (Kroger fiscal) alongside calendar dates. Both calendars, confirmed.
- **Flags:** Zero Cost Flag, Zero Qty Flag, Canceled Item, plus computed COGs (qty × case cost).

**One feed, two jobs.** iTrade is the source for both historical awarded cost *and* the supplier scorecard. Every scorecard metric (fill rate, on-time, DC rejection, cost/case, age at receipt) is derivable from these columns. KCMS stays separate for scan movement and margin.

**Importer rules (the mess is real):**
- Trust the flags first (Zero Cost, Zero Qty, Canceled) as the first validation gate.
- Sanity-check date spans. One real row shows received two months after shipped — age-at-receipt math has to reject that, not compute it.
- Key off the commodity/subcom codes inside the data, never the filename. The "614 Garlic Herbs" file contained tomatoes; two files were duplicate pulls under generic names.
- Handle template variants: a 43-col "Data" format and a 51-col "Query/Calendar" format both exist.

---

## 2. Normalization (the bridge: UPC → lot)

Bids and receipts arrive at **UPC**. Awards happen at **lot**. Normalization is the hinge, and Ed already built the decomposition logic (the "Norm" sheet).

**What it does:** take the raw item (UPC, subcom, case size, description) and decompose the description into a fixed attribute set, then recompose into a canonical lot.

**Attribute taxonomy (universal core + per-category extensions):**
- Universal: ORGANIC, COLOR, SIZE, PACK.
- Tomato extensions: VARIETY, PROCESS (field / hothouse / on-vine).
- Onion extensions: PACK TYPE (bulk / bag / RPC / carton), STORAGE.
- (Confirm per category as new commodities onboard.)

Output: `LOT FINAL`, e.g. "PREMIUM SNACKING 9OZ", "ORGANIC GRAPE 10OZ", "FIELD BEEFSTAKE 17LB".

**Current form:** a fragile chain of XLOOKUP/TRIM/SUBSTITUTE/LEFT/TEXTJOIN across pasted tables, per-file, per-commodity, rebuilt each cycle. A "LOST DESCRIPTION" column already handles the unresolved case by hand.

**System form:** store three things per item — raw (UPC + description), decomposed attributes, and LOT FINAL. The system proposes attributes from the description (Ed's logic as rules), the human confirms the unsure ones, the mapping sticks. Storing attributes (not just the lot) lets you regroup later (all organic, all field-process) without re-mapping. Raw underneath, normalized on top, nothing overwritten.

**Why this is critical:** the analysis engine currently matches bids across suppliers with a **string-concatenation key** (`=TRIM(product)&TRIM(DC)`). If two suppliers word the same product differently, the keys miss and the comparison silently misaligns. Replacing the concat key with the normalized lot is the difference between a comparison you can trust and one you eyeball.

---

## 3. Bid intake (multi-template, one grain)

Bids arrive at UPC × DC × timeframe, but the **format varies by category**:

- **Tomato bid:** one flat sheet. Supplier, DC, product, UPC, case size, ship pack, routing, timeframe volume, FOB Cost, Delivered Cost. Standardized template across all suppliers.
- **Onion bid ("Hybrid"):** a 9-tab workbook. FOB on one tab, Delivery Charge on a separate tab, RPC vs carton, case-shipping logistics, and a Program Details tab carrying the **PBA terms** (Cost Structure, Food Safety, Service Level) with penalties, rewards, and supplier Yes/No acceptance.

**Design consequence:** the bid-line table absorbs different intake shapes into **one destination grain** (supplier × lot × DC × period). The importer needs a **per-template mapping**, not one fixed parser. The destination is constant; the intake is not.

**Identity:** items carry KLN, UPC, and RMS Case SKU. All three resolve to one lot via the alias system.

**Both origins captured:** bids carry FOB Location *and* Growing Location, with Distance derived. Two-origin rule, confirmed in the bid itself.

**Completeness:** bids flag No Bid / Incomplete — the scoreable-vs-awardable gate, done today by formula.

---

## 4. The engine (bids → comparable number → scenario)

Ed has three generations. The newest (Allocation model) is the target.

**Architecture (from the Onion/Sweet Potato Allocation models):** a deliberate three-layer stack — **Raw data → Calcs → Outputs** — with a **Data cube** as the single consolidated fact store, a **Supplier mapping** alias layer, a **Controls** parameter panel, a **Baseline** scenario, multiple **scenario lenses**, and **CBS freight data** for the freight lane.

**The Controls panel = the setup file, parameterized.** Commodity × Horizon (Short / Long), commitment start/end, Weeks, Periods, Total cases, computed from dates. The kickoff setup feeds Controls feeds the scenario tools.

**The comparison (FOB sheet):** product × region down the side, every supplier across the top, MINIFS pulling each supplier's price and a Min column for best cost. This is standardization + leverage signal.

**The scenario tools:** each cell (DC × product) shows Baseline, Historical Cost, Incumbent, and **every supplier's all-in cost**, with **cost impact vs baseline**. The user picks suppliers; the tool sums premium and cost impact.

**Scenarios are a set of lenses, not one answer:** Baseline/incumbent, Minimum cost, "no discount," and supplier-excluded ("Excluding KEI"). The system carries scenario variants as first-class.

**Baselines:** Summary compares scenarios vs **STLY** (same time last year) and vs **Latest**. STLY is where the loaded fiscal calendar earns its keep — it maps this cycle's periods to the same periods a year ago.

---

## 5. The timeframe fork (the biggest single win)

When pricing runs timeframe-by-timeframe (Colored Potato), Ed **forks the entire engine per timeframe**: Data cube TF1/TF2, Scenario TF1/TF2, Baseline TF1/TF2, then a TF1-vs-TF2 comparison. Every timeframe doubles the workbook by hand.

**The system treats timeframe as a dimension in the data, not a reason to clone sheets.** One engine runs N timeframes. This is the largest efficiency gain in the build.

---

## 6. The output (award + booking guide)

The **booking guide** is the award table plus execution logistics, and Ed already builds it by hand (the old spec marked this NOT BUILT). It carries: awarded supplier per DC × item, **FOB Price**, **Routing Price** (the landed number), plus transit days, PO lead time, PO edit deadline, MOQ, cases per pallet, cases per load, RPC flag, weekly and total volume.

The system **generates** this from the award instead of Ed assembling it.

---

## 7. The correction that matters most

The old spec built an **exact minimum-cost solver** that awards by lowest cost. Ed's real scenario tool is **decision support**: it computes and compares every supplier's all-in cost and surfaces the min as a *reference*, then the human picks, because the real choice is cost plus supply security plus quality plus incumbent plus risk.

**Keep the human in the seat.** The engine computes, compares, and surfaces the minimum. It does not award. This resolves the split-award / is-the-solver-right question from Session 1.

---

## 8. Fragility (the governance argument, in the flesh)

- **String-concat match keys** → silent misalignment when descriptions differ. Fix: normalized lot as the key.
- **Live formulas everywhere** (SUMIFS, MINIFS, LET) → no audit, no freeze; a change erases the prior number. The Controls panel already shows #REF! errors from a deleted sheet. Two models contain a sheet literally named "delete." Fix: governed, sealed runs; corrections are new runs.
- **Rounds as separate sheets**, rebuilt by hand → make a round a record.
- **Suppliers as columns** → restructure to add one. Fix: suppliers as rows; the grid is generated.
- **Three incompatible generations** of tooling, rebuilt per category, forked per pricing structure → one parameterized engine.

---

## The chain, end to end (now complete)

Setup file (kickoff) → supplier refresh + RFI → bid release → **bid intake (multi-template)** → **normalization (UPC → lot)** → **Data cube (the fact store)** → **Controls (parameters)** → **FOB comparison (min + per-supplier)** → **scenario lenses (baseline / min / custom / exclude)** vs **STLY / Latest** → human selection → **award** → **booking guide (generated)** → contracting. Governed, frozen, layered, nothing overwritten, one engine across categories and timeframes.
