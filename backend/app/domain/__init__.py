"""Domain packages — one per logical layer = per PostgreSQL schema (PLAN §2).

Layers: ref norm cyc bid eng awd perf audit. `ref` is wired end-to-end as the reference
pattern; the other seven are present-but-empty stubs whose models.py name their target tables.
"""
