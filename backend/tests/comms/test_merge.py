"""The deterministic `[#Name]` template-merge engine (E-37) — pure, no DB."""

from __future__ import annotations

from app.comms.merge import merge, placeholders


def test_fills_known_placeholders() -> None:
    result = merge("Hi [#SupplierName], welcome.", {"SupplierName": "Acme Produce"})
    assert result.text == "Hi Acme Produce, welcome."
    assert result.used == ("SupplierName",)
    assert result.missing == ()


def test_repeated_placeholder_filled_everywhere_listed_once() -> None:
    result = merge("[#X] and [#X] again", {"X": "Z"})
    assert result.text == "Z and Z again"
    assert result.used == ("X",)
    assert result.missing == ()


def test_missing_placeholder_is_left_in_place_and_reported() -> None:
    # A visible hole, never a silent blank — so a draft can't go out with an invisible gap.
    result = merge("Bids due [#DueDate].", {})
    assert result.text == "Bids due [#DueDate]."
    assert result.missing == ("DueDate",)
    assert result.used == ()


def test_none_or_empty_value_counts_as_missing() -> None:
    result = merge("[#A]/[#B]", {"A": "", "B": None})  # type: ignore[dict-item]
    assert result.text == "[#A]/[#B]"
    assert set(result.missing) == {"A", "B"}
    assert result.used == ()


def test_mixed_used_and_missing() -> None:
    result = merge(
        "Hi [#SupplierName], round [#RoundNumber] closes [#DueDate].",
        {"SupplierName": "Acme", "RoundNumber": "2"},
    )
    assert result.text == "Hi Acme, round 2 closes [#DueDate]."
    assert result.used == ("SupplierName", "RoundNumber")
    assert result.missing == ("DueDate",)


def test_plain_text_passes_through_unchanged() -> None:
    result = merge("No placeholders here.", {"Unused": "x"})
    assert result.text == "No placeholders here."
    assert result.used == ()
    assert result.missing == ()


def test_non_token_brackets_are_left_untouched() -> None:
    # Only the exact `[#Name]` shape is a token; `[plain]`, `[#]`, and `[# spaced]` are not.
    template = "[plain] [#] [# spaced] [#Good]"
    result = merge(template, {"Good": "ok"})
    assert result.text == "[plain] [#] [# spaced] ok"
    assert result.used == ("Good",)
    assert result.missing == ()


def test_adjacent_tokens() -> None:
    result = merge("[#A][#B]", {"A": "1", "B": "2"})
    assert result.text == "12"


def test_placeholders_lists_distinct_names_in_first_seen_order() -> None:
    assert placeholders("[#B] [#A] [#B] [#C]") == ["B", "A", "C"]
    assert placeholders("no tokens") == []
