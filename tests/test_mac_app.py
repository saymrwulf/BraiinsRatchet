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
        self.assertIn("mirror|reality", text)
        self.assertIn("app_visual_state.md", text)
        self.assertIn("pkill -x BraiinsRatchetMac", text)
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
        self.assertIn("<key>LSMinimumSystemVersion</key>", text)
        self.assertIn("<string>26.0</string>", text)
        self.assertIn("iconutil -c icns", text)

    def test_native_app_targets_tahoe_sdk(self):
        manifest = ROOT / "macos" / "BraiinsRatchet" / "Package.swift"
        text = manifest.read_text()

        self.assertIn("swift-tools-version: 6.2", text)
        self.assertIn(".macOS(.v26)", text)

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
        self.assertIn("Flight Deck", text)
        self.assertIn("Who Owns Control", text)
        self.assertIn("Start Forever Engine", text)
        self.assertIn("Hashflow", text)
        self.assertIn("Bid Lab", text)
        self.assertIn("Evidence", text)
        self.assertNotIn("Controlled Automation", text)
        self.assertNotIn("./scripts/ratchet pipeline", text)

    def test_swift_app_uses_native_dashboard_not_raw_terminal_as_primary_ui(self):
        source = ROOT / "macos" / "BraiinsRatchet" / "Sources" / "BraiinsRatchetMac" / "BraiinsRatchetApp.swift"
        text = source.read_text()

        self.assertIn("NavigationSplitView", text)
        self.assertIn("FlightDeckApp", text)
        self.assertIn("FlightDeckView", text)
        self.assertIn("HashfieldBackdrop", text)
        self.assertIn("ReactorLens", text)
        self.assertIn("HashflowView", text)
        self.assertIn("RatchetMapView", text)
        self.assertIn("BidLabView", text)
        self.assertIn("EvidenceVaultView", text)
        self.assertIn("RealityMirrorView", text)
        self.assertIn("RealityHUD", text)
        self.assertIn("RenderedReality", text)
        self.assertIn("RealitySnapshotWriter", text)
        self.assertIn("AppStatePayload", text)
        self.assertIn("EngineStatusPayload", text)
        self.assertIn("loadAppState", text)
        self.assertIn("repoRootURL", text)
        self.assertIn("Start Forever Engine", text)
        self.assertIn("glassEffect", text)
        self.assertIn("GlassEffectContainer", text)
        self.assertIn(".buttonStyle(.glass", text)
        self.assertIn("backgroundExtensionEffect", text)
        self.assertIn("searchable", text)
        self.assertIn("Flight Deck", text)
        self.assertIn("Reality Mirror", text)
        self.assertIn("BED: Backstage Evidence Deck", text)
        self.assertIn("app_visual_state.md", text)
        self.assertIn("app_visual_state.json", text)
        self.assertIn("Bid Lab", text)
        self.assertNotIn("MissionControlView", text)
        self.assertNotIn("MiningStackView", text)
        self.assertNotIn("StrategyLabView", text)
        self.assertNotIn("Do This Now", text)
        self.assertNotIn("Automation Gate", text)
        self.assertNotIn("confirmationDialog", text)
        self.assertNotIn("showAutomationApproval", text)
