from pathlib import Path
import unittest

from braiins_ratchet.cli import build_parser


ROOT = Path(__file__).resolve().parents[1]


class MacAppPackagingTest(unittest.TestCase):
    def test_ratchet_wrapper_has_native_app_command(self):
        wrapper = ROOT / "scripts" / "ratchet"
        text = wrapper.read_text()

        self.assertIn("app|mac-app", text)
        self.assertIn("cmd_app", text)
        self.assertIn("app-state", text)
        self.assertIn("engine", text)
        self.assertNotIn("swift run BraiinsRatchetMac", text)

    def test_python_cli_exposes_structured_app_state(self):
        args = build_parser().parse_args(["app-state"])

        self.assertEqual(args.func.__name__, "cmd_app_state")

        engine_args = build_parser().parse_args(["engine", "status"])
        self.assertEqual(engine_args.func.__name__, "cmd_engine")

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

    def test_start_here_is_app_first_and_not_pipeline_first(self):
        text = (ROOT / "START_HERE.md").read_text()

        self.assertIn("This project now has one normal operator entry point", text)
        self.assertIn("./scripts/ratchet app", text)
        self.assertIn("The app is the control room", text)
        self.assertIn("Who Owns Control", text)
        self.assertIn("Start Forever Engine", text)
        self.assertIn("Mining Stack", text)
        self.assertIn("Strategy Lab", text)
        self.assertIn("Evidence Vault", text)
        self.assertNotIn("Controlled Automation", text)
        self.assertNotIn("./scripts/ratchet pipeline", text)

    def test_swift_app_uses_native_dashboard_not_raw_terminal_as_primary_ui(self):
        source = ROOT / "macos" / "BraiinsRatchet" / "Sources" / "BraiinsRatchetMac" / "BraiinsRatchetApp.swift"
        text = source.read_text()

        self.assertIn("NavigationSplitView", text)
        self.assertIn("MissionControlView", text)
        self.assertIn("MiningStackView", text)
        self.assertIn("RatchetPathView", text)
        self.assertIn("StrategyLabView", text)
        self.assertIn("EvidenceVaultView", text)
        self.assertIn("AppStatePayload", text)
        self.assertIn("EngineStatusPayload", text)
        self.assertIn("loadAppState", text)
        self.assertIn("Start Forever Engine", text)
        self.assertIn("Who Owns Control", text)
        self.assertIn("Mining Stack", text)
        self.assertIn("Strategy Lab", text)
        self.assertIn("Current Decision", text)
        self.assertNotIn("Do This Now", text)
        self.assertNotIn("Automation Gate", text)
        self.assertNotIn("confirmationDialog", text)
        self.assertNotIn("showAutomationApproval", text)
