"""End-to-end tests of the VS-01 app in a real browser (Playwright, Chromium).

TEST-003 (FR-001..FR-003), TEST-004 (FR-004, FR-005) and TEST-005 (UX-001), as declared in
.lfe/requirements.json. Without Playwright the whole module is skipped; `lfe run --requires
python:playwright` then records `not_executed`, never `pass`.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover - depends on the environment
    raise unittest.SkipTest(f"playwright not installed: {exc}")

APP = Path(__file__).resolve().parents[1] / "app"
KEY = "lfe-vs01:readings:v1"
VIEWPORTS = {"mobile": {"width": 390, "height": 844}, "desktop": {"width": 1280, "height": 800}}
BREAK_STORAGE = "Storage.prototype.setItem = () => { throw new DOMException('quota', 'QuotaExceededError'); };"


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = partial(SimpleHTTPRequestHandler, directory=str(APP))
        handler.log_message = lambda *args: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}/index.html"
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()

    def open(self, viewport="desktop", init_script=None):
        context = self.browser.new_context(viewport=VIEWPORTS[viewport])
        self.addCleanup(context.close)
        if init_script:
            context.add_init_script(init_script)
        page = context.new_page()
        page.goto(self.url)
        return page

    def stored(self, page):
        return page.evaluate(f"JSON.parse(localStorage.getItem('{KEY}') || 'null')")

    def error_text(self, page, selector="#reading-error"):
        # The app writes messages ~50 ms after clearing them, so screen readers re-announce
        # the same sentence; wait for the text instead of reading it immediately.
        page.wait_for_function(f"document.querySelector('{selector}').textContent.trim().length > 0", timeout=3000)
        return page.inner_text(selector).strip()

    def titles(self, page):
        return [t.strip() for t in page.locator("#reading-list li.entry").all_inner_texts()]


class Test003AddPersistMark(Browser):
    """FR-001 add with required title · FR-002 persist · FR-003 mark and unmark as read."""

    def test_fr001_add_trims_clears_and_refocuses(self):
        page = self.open()
        page.fill("#reading-title", "  Cartas a um relojoeiro  ")
        page.press("#reading-title", "Enter")
        self.assertIn("Cartas a um relojoeiro", self.titles(page)[0])
        self.assertEqual(page.input_value("#reading-title"), "")
        self.assertEqual(page.evaluate("document.activeElement.id"), "reading-title")
        self.assertEqual(self.stored(page)[0]["title"], "Cartas a um relojoeiro")

    def test_fr002_reading_survives_reload_with_contract_shape(self):
        page = self.open()
        page.fill("#reading-title", "A cidade sob a serra")
        page.click("#reading-submit")
        page.reload()
        self.assertIn("A cidade sob a serra", self.titles(page)[0])
        item = self.stored(page)[0]
        self.assertEqual(set(item), {"id", "title", "done", "createdAt"})

    def test_fr003_mark_and_unmark_persist(self):
        page = self.open()
        page.fill("#reading-title", "Atlas das cozinhas vazias")
        page.press("#reading-title", "Enter")
        page.check("#reading-list li.entry input.entry-check")
        page.reload()
        self.assertTrue(page.is_checked("#reading-list li.entry input.entry-check"))
        self.assertTrue(self.stored(page)[0]["done"])
        page.uncheck("#reading-list li.entry input.entry-check")
        page.reload()
        self.assertFalse(self.stored(page)[0]["done"])


class Test004Errors(Browser):
    """FR-004 refuse empty titles · FR-005 storage failures are visible, nothing is faked."""

    def test_fr004_blank_title_is_refused_and_announced(self):
        page = self.open()
        page.fill("#reading-title", "   ")
        page.press("#reading-title", "Enter")
        self.assertIsNone(self.stored(page))
        self.assertEqual(page.get_attribute("#reading-title", "aria-invalid"), "true")
        self.assertEqual(page.get_attribute("#reading-error", "aria-live"), "assertive")
        self.assertTrue(self.error_text(page))
        self.assertTrue(page.is_visible("#reading-error"))

    def test_fr005_write_failure_keeps_list_and_title(self):
        page = self.open(init_script=BREAK_STORAGE)
        page.fill("#reading-title", "Livro que não pode ser salvo")
        page.press("#reading-title", "Enter")
        self.assertTrue(self.error_text(page, "#storage-error"))
        self.assertTrue(page.is_visible("#storage-error"))
        self.assertEqual(page.get_attribute("#storage-error", "role"), "alert")
        self.assertEqual(self.titles(page), [])
        self.assertEqual(page.input_value("#reading-title"), "Livro que não pode ser salvo")

    def test_fr005_unreadable_data_is_reported_not_overwritten(self):
        page = self.open(init_script=f"localStorage.setItem('{KEY}', '{{quebrado');")
        self.assertTrue(page.is_visible("#storage-error"))
        page.fill("#reading-title", "Nova leitura")
        page.press("#reading-title", "Enter")
        self.assertEqual(page.evaluate(f"localStorage.getItem('{KEY}')"), "{quebrado")


class Test005Keyboard(Browser):
    """UX-001 add, see the error and mark as read with Tab/Enter/Space, focus ring visible."""

    def focus_ring(self, page):
        return page.evaluate("""() => { const s = getComputedStyle(document.activeElement);
            return (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none'; }""")

    def journey(self, viewport):
        page = self.open(viewport)
        page.keyboard.press("Tab")
        self.assertEqual(page.evaluate("document.activeElement.id"), "reading-title")
        self.assertTrue(self.focus_ring(page), f"no visible focus on the title field ({viewport})")
        page.keyboard.press("Enter")
        self.assertTrue(self.error_text(page))
        page.keyboard.type("Bordado para dias de chuva")
        page.keyboard.press("Enter")
        self.assertIn("Bordado para dias de chuva", self.titles(page)[0])
        for _ in range(10):
            page.keyboard.press("Tab")
            if page.evaluate("document.activeElement.classList.contains('entry-check')"):
                break
        self.assertTrue(page.evaluate("document.activeElement.classList.contains('entry-check')"))
        self.assertTrue(self.focus_ring(page), f"no visible focus on the checkbox ({viewport})")
        page.keyboard.press("Space")
        self.assertTrue(self.stored(page)[0]["done"])

    def test_ux001_keyboard_journey_mobile(self):
        self.journey("mobile")

    def test_ux001_keyboard_journey_desktop(self):
        self.journey("desktop")


if __name__ == "__main__":
    unittest.main()
