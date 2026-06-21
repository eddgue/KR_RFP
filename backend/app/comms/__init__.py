"""Supplier communications (E-37) — deterministic template-merge email drafts.

The buyer authors plain-text email templates with `[#PlaceholderName]` placeholders; this package
PARSES and FILLS them from governed data (a mail-merge, NOT AI). `merge` is the pure engine; the
per-touchpoint field resolvers + the draft surface build on top.
"""
