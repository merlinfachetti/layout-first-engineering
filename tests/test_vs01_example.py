"""Static checks for the VS-01 example (RFC-0002). Offline, no browser, standard library only.

The example ships with proposals for G1–G4 and no decisions. These tests make sure that what a
person reviews is exactly what the ledger points to, and that the app exposes the IDs the
future E2E test (TEST-003 to TEST-005) relies on.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "vs01-leituras"
sys.path.insert(0, str(ROOT / "engine"))

from lfe import contracts, gates, ledger, workspace  # noqa: E402

# The contract between app/index.html and the E2E test. Also documented in DEMO_README.md.
E2E_IDS = {
    "reading-form", "reading-title", "reading-submit", "reading-error", "storage-error",
    "reading-status", "reading-list", "reading-summary", "empty-state",
}
VIEWPORTS = {(390, 844), (1280, 800)}
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".jsonl", ".md"}


def example_files():
    return sorted(p for p in EXAMPLE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def load_json(rel):
    return json.loads((EXAMPLE / rel).read_text(encoding="utf-8"))


class Elements(HTMLParser):
    """Collect every start tag with its attributes."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def by_id(self):
        return {a["id"]: (t, a) for t, a in self.tags if "id" in a}


def parse_html(rel):
    parser = Elements()
    parser.feed((EXAMPLE / rel).read_text(encoding="utf-8"))
    return parser


class ContractsAndHashes(unittest.TestCase):
    def setUp(self):
        self.state = workspace.load_state(EXAMPLE)

    def test_contract_documents_are_valid(self):
        for rel, kind in ((".lfe/state.json", "state"), (".lfe/baselines/DESIGN-001.json", "baseline"),
                          (".lfe/requirements.json", "requirements")):
            with self.subTest(rel):
                self.assertEqual(contracts.validate_file(EXAMPLE / rel, expected=kind), [])

    def test_every_artifact_matches_the_disk(self):
        self.assertEqual(set(self.state["artifacts"]), {"DIR-001", "DESIGN-001", "SCOPE-001", "ADR-001"})
        for art_id, art in self.state["artifacts"].items():
            with self.subTest(art_id):
                digest, problems = workspace.artifact_digest(EXAMPLE, art["path"])
                self.assertEqual(problems, [])
                self.assertEqual(digest, art["sha256"])

    def test_listed_files_are_hashed_and_exist(self):
        for rel in (".lfe/directions/DIR-001.json", ".lfe/baselines/DESIGN-001.json"):
            for entry in load_json(rel)["files"]:
                with self.subTest(entry["path"]):
                    self.assertFalse(contracts.unsafe_path(entry["path"]))
                    self.assertEqual(workspace.file_digest(EXAMPLE / entry["path"]), entry["sha256"])

    def test_directions_offer_two_options_with_tradeoffs(self):
        doc = load_json(".lfe/directions/DIR-001.json")
        self.assertEqual([o["id"] for o in doc["options"]], ["A", "B"])
        for option in doc["options"]:
            with self.subTest(option["id"]):
                self.assertTrue((EXAMPLE / option["path"]).is_file())
                for key in ("gains", "costs", "bestWhen"):
                    self.assertTrue(option["tradeoffs"][key])
                html = (EXAMPLE / option["path"]).read_text(encoding="utf-8")
                self.assertIn("Trade-offs da direção", html)


class LedgerAndGates(unittest.TestCase):
    def setUp(self):
        self.state = workspace.load_state(EXAMPLE)
        self.entries = ledger.read(EXAMPLE)  # raises LEDGER_TAMPERED if the chain is broken

    def test_ledger_holds_only_agent_proposals(self):
        # Proposals only: approvals are human (or simulated by `lfe demo` in a separate copy).
        self.assertTrue(self.entries)
        for entry in self.entries:
            self.assertEqual((entry["kind"], entry["channel"]), ("proposal", "agent"))
        self.assertEqual(sorted({e["gate"] for e in self.entries}), ["G1", "G2", "G3", "G4"])

    def test_latest_proposal_of_each_gate_binds_the_current_revisions(self):
        latest = {}
        for entry in self.entries:
            latest[entry["gate"]] = entry  # older proposals stay in the history, superseded
        for gate, entry in sorted(latest.items()):
            for item in entry["scope"]["artifacts"]:
                with self.subTest(gate=gate, artifact=item["id"]):
                    current = self.state["artifacts"][item["id"]]
                    self.assertEqual((item["revision"], item["sha256"]), (current["revision"], current["sha256"]))

    def test_gates_are_proposed_and_production_is_locked(self):
        self.assertEqual(self.state["mode"], "project")
        self.assertEqual(gates.cache_problems(self.state, self.entries), [])
        results = gates.evaluate(EXAMPLE, self.state, self.entries)
        self.assertEqual({g: r["status"] for g, r in results.items()}, {
            "G1": "proposed", "G2": "proposed", "G3": "proposed", "G4": "proposed",
            "G5": "not_started", "G6": "not_started"})
        self.assertEqual(gates.stage_problems(results, "S1"), [])
        self.assertTrue(gates.stage_problems(results, "S6"))


class BaselineAndScope(unittest.TestCase):
    def setUp(self):
        self.baseline = load_json(".lfe/baselines/DESIGN-001.json")
        self.scope = load_json(".lfe/requirements.json")

    def test_baseline_shape(self):
        b = self.baseline
        self.assertEqual((b["medium"], b["fidelity"], b["mediumDecisionId"]), ("local-html", "static-layout", "DEC-002"))
        screen = b["screens"][0]
        self.assertEqual(screen["screenId"], "UI-001")
        self.assertEqual({(v["width"], v["height"]) for v in screen["viewports"]}, VIEWPORTS)
        self.assertTrue({"default", "empty", "error"} <= set(screen["states"]))

    def test_previews_match_the_declared_viewports(self):
        previews = [f["path"] for f in self.baseline["files"] if f["path"].endswith(".png")]
        self.assertIn(self.baseline["screens"][0]["preview"]["path"], previews)
        sizes = set()
        for rel in previews:
            with self.subTest(rel):
                head = (EXAMPLE / rel).read_bytes()[:24]
                self.assertEqual(head[:8], b"\x89PNG\r\n\x1a\n")
                size = struct.unpack(">II", head[16:24])
                self.assertIn(size, VIEWPORTS)
                self.assertIn(f"{size[0]}x{size[1]}", rel)
                sizes.add(size)
        self.assertEqual(sizes, VIEWPORTS)

    def test_prototype_offers_every_state(self):
        html = (EXAMPLE / "prototype/index.html").read_text(encoding="utf-8")
        for state in ("default", "empty", "error", "storage-error"):
            self.assertIn(f'href="?state={state}"', html)

    def test_scope_covers_rfc_0002(self):
        items = {i["id"]: i for i in self.scope["items"]}
        tests = {t["id"]: t for t in self.scope["tests"]}
        self.assertTrue({"FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "UX-001"} <= set(items))
        self.assertEqual(set(tests), {f"TEST-00{n}" for n in range(1, 7)})
        self.assertEqual({t["id"]: t["kind"] for t in tests.values()}, {
            "TEST-001": "unit", "TEST-002": "contract", "TEST-003": "e2e",
            "TEST-004": "e2e", "TEST-005": "e2e", "TEST-006": "manual-review"})
        screens = {s["screenId"] for s in self.baseline["screens"]}
        for item in items.values():
            with self.subTest(item["id"]):
                self.assertEqual(item["status"], "proposed")
                self.assertTrue(set(item["uiRefs"]) <= screens)  # R-02
                self.assertTrue(item["testRefs"])


class AppMarkup(unittest.TestCase):
    def setUp(self):
        self.parser = parse_html("app/index.html")
        self.ids = self.parser.by_id()

    def test_e2e_ids_exist(self):
        self.assertEqual(E2E_IDS - set(self.ids), set())

    def test_title_field_has_an_associated_label(self):
        labels = [a for t, a in self.parser.tags if t == "label" and a.get("for") == "reading-title"]
        self.assertEqual(len(labels), 1)
        tag, attrs = self.ids["reading-title"]
        self.assertEqual(tag, "input")
        self.assertIn("reading-error", attrs.get("aria-describedby", "").split())
        # The app validates and announces errors itself (FR-004) instead of the browser bubble.
        self.assertIn("novalidate", self.ids["reading-form"][1])

    def test_live_regions(self):
        self.assertIn(self.ids["reading-error"][1].get("aria-live"), ("polite", "assertive"))
        self.assertEqual(self.ids["storage-error"][1].get("role"), "alert")
        self.assertEqual(self.ids["reading-status"][1].get("role"), "status")

    def test_page_language_and_local_script(self):
        html = [a for t, a in self.parser.tags if t == "html"][0]
        self.assertEqual(html.get("lang"), "pt-BR")
        scripts = [a.get("src") for t, a in self.parser.tags if t == "script"]
        self.assertEqual(scripts, ["app.js"])

    def test_storage_key_and_item_shape(self):
        js = (EXAMPLE / "app/app.js").read_text(encoding="utf-8")
        self.assertIn('"lfe-vs01:readings:v1"', js)
        for field in ("id:", "title:", "done:", "createdAt:"):
            self.assertIn(field, js)
        self.assertNotIn("innerHTML", js)  # titles are user text: textContent only

    def test_reduced_motion_and_focus_styles(self):
        css = (EXAMPLE / "app/styles.css").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn(":focus-visible", css)


class Tokens(unittest.TestCase):
    def setUp(self):
        self.doc = load_json("prototype/tokens.json")

    def leaves(self, node=None, path=(), inherited=None):
        node = self.doc if node is None else node
        inherited = node.get("$type", inherited)
        if "$value" in node:
            yield path, node, inherited
            return
        for key, child in node.items():
            if not key.startswith("$"):
                yield from self.leaves(child, path + (key,), inherited)

    def resolve(self, value, depth=0):
        match = re.fullmatch(r"\{([^}]+)\}", value) if isinstance(value, str) else None
        if not match:
            return value
        self.assertLess(depth, 5, "alias chain too long")
        node = self.doc
        for key in match.group(1).split("."):
            node = node[key]
        return self.resolve(node["$value"], depth + 1)

    def test_every_token_has_a_type_and_resolves(self):
        count = 0
        for path, node, kind in self.leaves():
            with self.subTest(".".join(path)):
                self.assertIsNotNone(kind)
                self.resolve(node["$value"])
                count += 1
        self.assertGreater(count, 30)

    def test_css_mirrors_the_semantic_colors(self):
        sources = {
            "app/styles.css": (EXAMPLE / "app/styles.css").read_text(encoding="utf-8"),
            "prototype/index.html": (EXAMPLE / "prototype/index.html").read_text(encoding="utf-8"),
        }
        for path, node, kind in self.leaves(self.doc["color"], ("color",)):
            name = "--" + "-".join(path)
            value = self.resolve(node["$value"]).lower()
            for source, text in sources.items():
                with self.subTest(name, source=source):
                    self.assertIn(f"{name}: {value};", text)


class Hygiene(unittest.TestCase):
    ABSOLUTE = re.compile(r"(/Users/|/home/|/private/|/tmp/|[A-Za-z]:\\\\|file://)")
    REMOTE = re.compile(r"""(?:src|href)\s*=\s*["'](?:https?:)?//|url\(\s*["']?(?:https?:)?//""", re.I)

    def test_no_absolute_paths(self):
        for path in example_files():
            if path.suffix in TEXT_SUFFIXES:
                with self.subTest(path.relative_to(EXAMPLE).as_posix()):
                    self.assertIsNone(self.ABSOLUTE.search(path.read_text(encoding="utf-8")))

    def test_contract_paths_are_relative(self):
        state = load_json(".lfe/state.json")
        for art in state["artifacts"].values():
            self.assertFalse(contracts.unsafe_path(art["path"]))

    def test_pages_load_nothing_from_the_network(self):
        for rel in ("app/index.html", "app/styles.css", "app/app.js", "prototype/index.html",
                    "directions/A-editorial.html", "directions/B-biblioteca.html"):
            with self.subTest(rel):
                text = (EXAMPLE / rel).read_text(encoding="utf-8")
                self.assertIsNone(self.REMOTE.search(text))
                self.assertNotIn("fetch(", text)
                self.assertNotIn("XMLHttpRequest", text)

    def test_manifest_is_honest_about_status(self):
        manifest = load_json("project.json")
        self.assertEqual(manifest["id"], load_json(".lfe/state.json")["projectId"])
        self.assertEqual(manifest["status"], "draft")
        self.assertEqual(manifest["tests"]["e2e"]["status"], "pending")
        self.assertFalse(manifest["lfe"]["approvalsIncluded"])

    def test_demo_readme_documents_e2e_ids_and_limits(self):
        readme = (EXAMPLE / "DEMO_README.md").read_text(encoding="utf-8")
        self.assertIn("## Limites", readme)
        for element_id in E2E_IDS:
            self.assertIn(f"#{element_id}", readme)


if __name__ == "__main__":
    unittest.main()
