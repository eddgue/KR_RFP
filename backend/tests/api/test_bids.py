"""Bids + run-input-chain API: auth gate, the full input chain end to end, flexible propose/confirm.

Integration (real Postgres + a temp vault): the runs + bids routers wrap PilotService with
`isolate_db=False`, so they share the rolled-back test session and provision no per-run DB. The
`vault_root` fixture redirects the routers' vault to a temp dir; `client` shares the test session.
The setup + bid fixture files are built with the SAME synthetic builders the pilot tests use
(reused from `tests.pilot.test_pilot_cycle_e2e`) so the routes exercise the real ingest path.
"""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from app.output.types import CycleView
from tests.pilot.test_pilot_cycle_e2e import _build_filled_setup, _fill_bid_template

AUTH = "/api/v1/auth"
RUNS = "/api/v1/runs"
BIDS = "/api/v1/bids"

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _login(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        f"{AUTH}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    assert resp.status_code == 200


def _create_run(client) -> str:  # type: ignore[no-untyped-def]
    created = client.post(
        RUNS, json={"commodity": "Field Tomatoes", "label": "Bids E2E", "rehearsal": False}
    )
    assert created.status_code == 201
    return created.json()["slug"]


def _ingest_setup(client, slug: str) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        f"{RUNS}/{slug}/setup",
        files={"file": ("setup.xlsx", _build_filled_setup(), _XLSX)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cycle_id"]
    assert set(body["kanban"]) == {"Done", "Doing", "Next", "Waiting on you"}


def _generate_template(client, slug: str, round_no: int = 1) -> str:  # type: ignore[no-untyped-def]
    resp = client.post(f"{RUNS}/{slug}/rounds/{round_no}/template")
    assert resp.status_code == 200, resp.text
    return resp.json()["filename"]


def _build_messy_supplier_file(view: CycleView) -> bytes:
    """A supplier's own messy sheet — odd headers, shuffled order, no keys (8 priced rows)."""

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["Quarterly Produce Quote (supplier's own format)"])
    ws.append(["Vendor", "Warehouse", "Product Line", "All-In Price", "Weekly Cases"])
    for dc in view.dcs:
        for lot in view.lots:
            for sup in view.suppliers:
                price = 11.50 if "Green Valley" in sup.name else 11.20
                ws.append([sup.name, dc.name, lot.name, price, 600])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# auth gate
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_bids_import_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """POST /bids/import with no session is a 401 (every bids route is authenticated)."""

    resp = client.post(
        f"{BIDS}/import",
        data={"run": "x", "round": 1, "mode": "strict"},
        files={"file": ("b.xlsx", b"x", _XLSX)},
    )
    assert resp.status_code == 401


@pytest.mark.integration
def test_bids_list_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """GET /bids with no session is a 401."""

    resp = client.get(BIDS, params={"run": "x", "round": 1})
    assert resp.status_code == 401


@pytest.mark.integration
def test_run_files_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """GET /runs/{slug}/files with no session is a 401."""

    assert client.get(f"{RUNS}/x/files").status_code == 401


# --------------------------------------------------------------------------- #
# the full input chain, end to end
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_input_chain_e2e(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """create → download setup → ingest setup → gen template → strict import → list bids."""

    _login(client, seed_user)
    slug = _create_run(client)

    # The created run carries the setup workbook in inputs/ — it lists and downloads.
    files = client.get(f"{RUNS}/{slug}/files")
    assert files.status_code == 200
    listing = files.json()
    setup_name = next(f["name"] for f in listing if f["name"].endswith("setup_kickoff.xlsx"))
    assert all(f["kind"] in ("input", "output") for f in listing)
    assert all(f["size_bytes"] > 0 for f in listing)

    dl = client.get(f"{RUNS}/{slug}/files/{setup_name}")
    assert dl.status_code == 200
    assert dl.headers["content-type"] == _XLSX
    assert "attachment" in dl.headers["content-disposition"]
    assert setup_name in dl.headers["content-disposition"]
    assert dl.content[:2] == b"PK"  # a real xlsx (zip) payload

    # Ingest the filled setup → a governed cycle.
    _ingest_setup(client, slug)

    # Generate the Round 1 bid template; it lands in inputs/ and is downloadable.
    template_name = _generate_template(client, slug, 1)
    assert template_name == "02_round1_bid_template.xlsx"
    names = [f["name"] for f in client.get(f"{RUNS}/{slug}/files").json()]
    assert template_name in names
    tmpl = client.get(f"{RUNS}/{slug}/files/{template_name}")
    assert tmpl.status_code == 200

    # Fill the template synthetically and import it strict (key-validated).
    filled = _fill_bid_template(tmpl.content)
    imported = client.post(
        f"{BIDS}/import",
        data={"run": slug, "round": 1, "mode": "strict"},
        files={"file": (template_name, filled, _XLSX)},
    )
    assert imported.status_code == 200, imported.text
    body = imported.json()
    assert body["ingested"] == 8  # 2 DCs × 2 lots × 1 TF × 2 suppliers
    assert set(body["kanban"]) == {"Done", "Doing", "Next", "Waiting on you"}

    # List the round's bids — 8 rows at the identity grain, with the reviewer-friendly columns.
    listed = client.get(BIDS, params={"run": slug, "round": 1})
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 8
    sample = rows[0]
    for field in (
        "bid_line_id",
        "supplier_id",
        "dc_id",
        "lot_id",
        "item_id",
        "tf_id",
        "currency_code",
        "submitted_all_in_case",
        "fob_case",
        "volume_minimum_cases",
        "validity_status",
        "is_scoreable",
        "is_awardable",
    ):
        assert field in sample
    assert sample["currency_code"] == "USD"
    assert sample["is_scoreable"] is True
    assert sample["submitted_all_in_case"] is not None


# --------------------------------------------------------------------------- #
# flexible: propose (writes nothing) then confirm (ingests)
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_flexible_propose_then_confirm(client, seed_user, vault_root, db_session) -> None:  # type: ignore[no-untyped-def]
    """confirm=false returns a proposal + writes nothing; confirm=true ingests via strict path."""

    from app.cycle.loader import load_cycle

    _login(client, seed_user)
    slug = _create_run(client)
    setup = client.post(
        f"{RUNS}/{slug}/setup", files={"file": ("s.xlsx", _build_filled_setup(), _XLSX)}
    )
    cycle_id = setup.json()["cycle_id"]

    # Build a messy supplier sheet against the persisted cycle's known names. The client shares the
    # rolled-back test session (the get_db override yields `db_session`), so this read sees it.
    view = load_cycle(db_session, cycle_id)
    messy = _build_messy_supplier_file(view)

    files_before = {f["name"] for f in client.get(f"{RUNS}/{slug}/files").json()}

    # confirm=false → a proposal, nothing written, nothing ingested.
    proposed = client.post(
        f"{BIDS}/import",
        data={"run": slug, "round": 1, "mode": "flexible", "confirm": "false"},
        files={"file": ("raw.xlsx", messy, _XLSX)},
    )
    assert proposed.status_code == 200, proposed.text
    proposal = proposed.json()["proposal"]
    assert proposal["is_confident"] is True
    assert proposal["sheet_name"]
    assert proposal["header_row"] == 2
    assert set(proposal["mappings"]) >= {"supplier", "dc", "lot", "all_in", "volume"}
    assert proposal["mappings"]["dc"]["confidence"] == "high"
    assert proposal["summary"]

    # No new file was written by the propose call, and no bids were ingested.
    files_after = {f["name"] for f in client.get(f"{RUNS}/{slug}/files").json()}
    assert files_after == files_before
    assert client.get(BIDS, params={"run": slug, "round": 1}).json() == []

    # confirm=true → normalized file written + ingested via the strict key-validated path.
    confirmed = client.post(
        f"{BIDS}/import",
        data={"run": slug, "round": 1, "mode": "flexible", "confirm": "true"},
        files={"file": ("raw.xlsx", messy, _XLSX)},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["ingested"] == 8
    assert len(client.get(BIDS, params={"run": slug, "round": 1}).json()) == 8


# --------------------------------------------------------------------------- #
# download the whole run folder as a zip (skeleton + files)
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_download_run_archive_zip(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """GET /runs/{slug}/archive streams a zip carrying the folder skeleton + the run's files."""

    import zipfile

    _login(client, seed_user)
    slug = _create_run(client)

    resp = client.get(f"{RUNS}/{slug}/archive")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert f"{slug}.zip" in resp.headers["content-disposition"]

    names = zipfile.ZipFile(io.BytesIO(resp.content)).namelist()
    # The empty-folder skeleton is present (a drop target each) ...
    assert f"{slug}/inputs/" in names
    assert f"{slug}/outputs/" in names
    assert f"{slug}/memory/" in names
    # ... alongside the created run's setup workbook + RUN.md manifest.
    assert any(n.endswith("setup_kickoff.xlsx") for n in names)
    assert any(n.endswith("RUN.md") for n in names)


# --------------------------------------------------------------------------- #
# isolation: two parallel runs never see each other's bids (the shared-DB guarantee)
# --------------------------------------------------------------------------- #
def _import_round1(client, slug: str) -> None:  # type: ignore[no-untyped-def]
    """Run a slug through ingest setup → template → strict import of 8 synthetic bid lines."""

    _ingest_setup(client, slug)
    template_name = _generate_template(client, slug, 1)
    tmpl = client.get(f"{RUNS}/{slug}/files/{template_name}")
    filled = _fill_bid_template(tmpl.content)
    imported = client.post(
        f"{BIDS}/import",
        data={"run": slug, "round": 1, "mode": "strict"},
        files={"file": (template_name, filled, _XLSX)},
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["ingested"] == 8


@pytest.mark.integration
def test_two_runs_do_not_cross_contaminate(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Two parallel runs stay isolated: each lists only its own bids, never the other run's.

    The web app shares ONE database (isolate_db=False); isolation is enforced by scoping every bid
    query to the run's own cycle_id + round_id. Both runs ingest the same synthetic bids, but each
    bid_line gets a fresh id per ingest — so a stable per-run count of 8 (never 16) AND disjoint
    id sets prove neither run can see the other's rows. A scoping regression would surface here as
    16 rows or overlapping ids.
    """

    _login(client, seed_user)

    slug_a = _create_run(client)
    slug_b = _create_run(client)
    assert slug_a != slug_b

    _import_round1(client, slug_a)
    _import_round1(client, slug_b)

    rows_a = client.get(BIDS, params={"run": slug_a, "round": 1}).json()
    rows_b = client.get(BIDS, params={"run": slug_b, "round": 1}).json()

    assert len(rows_a) == 8  # A lists only its own 8 — not the 16 now in the shared DB
    assert len(rows_b) == 8
    ids_a = {r["bid_line_id"] for r in rows_a}
    ids_b = {r["bid_line_id"] for r in rows_b}
    assert ids_a and ids_b
    assert ids_a.isdisjoint(ids_b)  # no bid line appears in both runs' lists


# --------------------------------------------------------------------------- #
# guards: path-traversal, unknown run, gate-before-setup, bad mode
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_download_path_traversal_refused(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A traversal / non-plain filename is a clean 404, never a read outside the run folder."""

    _login(client, seed_user)
    slug = _create_run(client)
    # Encoded traversal attempts resolve to a 404, not the secrets above the run folder.
    for bad in ("..%2f..%2fconftest.py", "%2e%2e%2f%2e%2e%2fNOTES.md", "nope.xlsx"):
        resp = client.get(f"{RUNS}/{slug}/files/{bad}")
        assert resp.status_code == 404, (bad, resp.status_code)


@pytest.mark.integration
def test_unknown_run_404_everywhere(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """An unknown run slug is a 404 on files, setup, template, import, and list."""

    _login(client, seed_user)
    ghost = "no-such-run-20260101-abcdef"
    assert client.get(f"{RUNS}/{ghost}/files").status_code == 404
    assert client.get(f"{RUNS}/{ghost}/files/x.xlsx").status_code == 404
    assert (
        client.post(f"{RUNS}/{ghost}/setup", files={"file": ("s.xlsx", b"x", _XLSX)}).status_code
        == 404
    )
    assert client.post(f"{RUNS}/{ghost}/rounds/1/template").status_code == 404
    imp = client.post(
        f"{BIDS}/import",
        data={"run": ghost, "round": 1, "mode": "strict"},
        files={"file": ("b.xlsx", b"x", _XLSX)},
    )
    assert imp.status_code == 404
    assert client.get(BIDS, params={"run": ghost, "round": 1}).status_code == 404


@pytest.mark.integration
def test_template_before_setup_is_gated(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Generating a template before setup ingest is a clean 400 (gate_required), not a 500."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.post(f"{RUNS}/{slug}/rounds/1/template")
    assert resp.status_code == 400
    assert resp.json()["code"] == "gate_required"


@pytest.mark.integration
def test_import_before_setup_is_gated(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Importing bids before a cycle exists is a clean 400 (gate_required)."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.post(
        f"{BIDS}/import",
        data={"run": slug, "round": 1, "mode": "strict"},
        files={"file": ("b.xlsx", b"x", _XLSX)},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "gate_required"


@pytest.mark.integration
def test_import_bad_mode_is_422(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """An unknown mode fails request validation (422) before any work."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.post(
        f"{BIDS}/import",
        data={"run": slug, "round": 1, "mode": "bogus"},
        files={"file": ("b.xlsx", b"x", _XLSX)},
    )
    assert resp.status_code == 422
