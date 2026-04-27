from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MacAppPackagingTest(unittest.TestCase):
    def test_ratchet_wrapper_has_native_app_command(self):
        wrapper = ROOT / "scripts" / "ratchet"
        text = wrapper.read_text()

        self.assertIn("app|mac-app", text)
        self.assertIn("cmd_app", text)
        self.assertNotIn("swift run BraiinsRatchetMac", text)

    def test_mac_app_builder_creates_bundle_contract(self):
        builder = ROOT / "scripts" / "build_mac_app"
        text = builder.read_text()

        self.assertTrue(builder.stat().st_mode & 0o111)
        self.assertIn("Braiins Ratchet.app", text)
        self.assertIn("CFBundlePackageType", text)
        self.assertIn("APPL", text)
        self.assertIn("CFBundleIconFile", text)
        self.assertIn("iconutil -c icns", text)

    def test_native_app_docs_use_packaged_launcher(self):
        docs = [
            ROOT / "README.md",
            ROOT / "START_HERE.md",
            ROOT / "macos" / "BraiinsRatchet" / "README.md",
        ]

        for path in docs:
            text = path.read_text()
            self.assertIn("./scripts/ratchet app", text)
            self.assertNotIn("swift run BraiinsRatchetMac", text)
