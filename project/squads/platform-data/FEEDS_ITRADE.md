---
doc: iTrade Feed — Structure & Importer Mapping (E-08)
id: PD-FEEDS-01
version: 1.0
status: Draft (derived from a real export)
created: 2026-06-18
owner: Platform & Data squad
source: reference/samples/itrade_by_commodity_with_calendar_A.xlsx (real export, QUARANTINED — gitignored)
data_handling: STRUCTURE ONLY. Column headers are schema, not sensitive. No data-row values are recorded here.
---

# iTrade Feed — Structure & Importer Mapping

Derived from a **real iTrade export** the sponsor provided (2026-06-18). The raw file is quarantined under `reference/samples/` (gitignored, ADR-0001); only the structure is recorded here. This firms up epic **E-08** (the `perf.itrade_receipt` importer) and confirms the "one feed, two jobs" design (historical cost **and** the supplier scorecard both derive from this feed).

## Observed shape

- **One sheet: `Data`. 43 columns. ~113,986 rows.** This is the "43-column Data format" named in intake Session 3. (A 51-column "Query/Calendar" variant also exists per Session 3 — still outstanding; the importer must detect and handle both.)
- Two identical files were uploaded (same md5) — a duplicate; one retained.
- Scale note: ~114k receipt rows in a single commodity-group pull validates the "single-digit-thousand bids/cycle, low-tens-of-thousands of receipt rows" sizing — modest, system-of-record scale.

## Column → `perf.itrade_receipt` mapping (43 columns, grouped)

| # | Source column (real header) | Maps to (model field) | Group |
|---|---|---|---|
| 1 | Cas Fyt Com Cct Dsc Tx | commodity_desc → `ref.commodity` (resolve) | identity |
| 2 | Cas Fyt Sub Com Cct Dsc Tx | subcommodity_desc → `ref.subcommodity` (**the anchor**) | identity |
| 3 | PO Number | po_number | lineage |
| 4 | PO Purchase Order # | po_purchase_order_no | lineage |
| 5 | PO Creation Date | po_creation_date | date chain |
| 6 | PO Arrival Date | po_arrival_date | date chain |
| 7 | Date Receiver Indicated Received | received_date | date chain |
| 8 | PO Ship Date Request | ship_date_request | date chain |
| 9 | Date P200 FINAL sent | p200_final_sent_date | date chain |
| 10 | Date Shipped Indicated | ship_date_indicated | date chain |
| 11 | Date Shipped Recorded | ship_date_recorded | date chain |
| 12 | DC No | dc_no → `ref.dc` | identity |
| 13 | DC Name | dc_name (resolve/validate) | identity |
| 14 | Lin No | line_no | lineage |
| 15 | Cas Siz Tx | case_size (raw) | identity |
| 16 | Item Gross Weight | item_gross_weight | identity |
| 17 | Cas Net Wgt Am | case_net_weight | identity |
| 18 | Shp Pak Qy | ship_pack_qty | identity |
| 19 | Whs Shp Pak Qy | warehouse_ship_pack_qty | identity |
| 20 | Cas Upc No | upc → `ref.item` (alias resolve) | identity |
| 21 | Warehouse Description | warehouse_desc | identity |
| 22 | Vendor Name | supplier (→ `ref.supplier_alias` resolve) | vendor/origin |
| 23 | Vendor Shipping Address | ship_from_address | vendor/origin |
| 24 | State | **ship_from_state** (≠ grow-origin — never auto-derive) | vendor/origin |
| 25 | Zip | **ship_from_zip** (freight-proxy via `ref.zip_centroid`) | vendor/origin |
| 26 | Routing | routing (Delivered / FOB / …) | vendor/origin |
| 27 | Quantity Received by Buyer | qty_received | performance |
| 28 | Quantity Shipped by Shipper | qty_shipped | performance |
| 29 | QC Reject Qty | qc_reject_qty | performance |
| 30 | Final Price | **final_price_fob** (FOB) | cost |
| 31 | Field Buying Office | field_buying_office | lineage |
| 32 | Freight | freight | cost |
| 33 | Total Case Cost with Freight | total_w_freight (delivered) | cost |
| 34 | Cross Dock charges | xdock_charges | cost |
| 35 | Total Cross-Dock | total_xdock | cost |
| 36 | Canceled Item | flag_canceled | flag |
| 37 | Zero Cost Flag | flag_zero_cost | flag |
| 38 | Zero Qty Flag | flag_zero_qty | flag |
| 39 | Year/Period/Week | fiscal_ypw (composite) | fiscal |
| 40 | Year | fiscal_year | fiscal |
| 41 | Period | period | fiscal |
| 42 | Week of Year | week_of_year | fiscal |
| 43 | COGs | cogs | cost |

**Coverage:** the real export carries every field the brief's `perf.itrade_receipt` models, plus a **fuller 7-date chain** (cols 5–11) and **both shipped & received quantities** (27–28) — which is exactly what the scorecard derivations need. No column is unmapped.

## Importer rules confirmed (E-08), from Session 3 + the real headers

1. **Flag-first validation.** Cols 36–38 (Canceled / Zero Cost / Zero Qty) are the first gate — exclude/flag before any math.
2. **Date-span sanity.** The 7-date chain (cols 5–11) enables age-at-receipt and impossible-span rejection (e.g. received-before-shipped, or received months after shipped). Reject from age math; persist with an ingestion-issue code, never silently compute.
3. **Key off codes, not filename.** Resolve on cols 1–2 (commodity / subcommodity) — the file name is unreliable (intake: a "Garlic Herbs" file contained tomatoes).
4. **Two origins kept separate.** Cols 24–25 (State/Zip) are **ship-from**, never grow-origin (which is supplier-stated at bid). Distance is a freight proxy via `ref.zip_centroid` (col 25). (ADR-0006 / gap G7.)
5. **Template variants.** Detect 43-col "Data" vs the 51-col "Query/Calendar" variant by header signature; map both to one `perf.itrade_receipt` grain.
6. **Identity resolution.** Vendor Name → supplier alias (col 22); UPC → item alias (col 20); unresolved → quarantine, never guess (KEEP the as-built alias+quarantine machinery).

## One feed, two jobs (confirmed by the columns)

- **Historical awarded cost** = cost columns (30, 32–35, 43) at the receipt grain.
- **Supplier scorecard** (two frozen snapshots, kickoff + sign-off) **derives entirely from this feed**: fill rate & adjusted fill (27 vs 28), on-time (date chain 7–11), DC rejection & rejected qty (29), cost/case (30/43), age at receipt (received_date − ship_date). No separate scorecard feed is needed — matches the prep workbooks' `Scorecard` + `Scorecard (Signoff)` tabs.

## Outstanding for the feed

- The **51-column "Query/Calendar"** variant (to confirm the extra 8 columns).
- **KCMS** (subcommodity + GTIN grain) — distinct feed; the kickoff prep workbooks contain `KCMS (subcomm) Export` + `KCMS (GTIN) Export` tabs (Product squad analyzing).
- A **golden v3 input/output pair** is still the top ask — this iTrade feed proves the *importer*, not yet the *engine reproduction*.

## Action

Feeds E-08 (itrade_receipt importer) directly. The `perf.itrade_receipt` columns in the M0 baseline should be reconciled to this real header set; the importer is a Phase B deliverable and a prerequisite of the real-data pilot (E-13).
