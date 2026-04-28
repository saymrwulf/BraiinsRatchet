from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def test_user_guide_covers_full_autoresearch_loop(self):
        text = (ROOT / "docs" / "USER_GUIDE.md").read_text()

        self.assertIn("# Braiins Ratchet User Guide", text)
        self.assertIn("The Story", text)
        self.assertIn("Sense", text)
        self.assertIn("Price", text)
        self.assertIn("Watch", text)
        self.assertIn("Mature", text)
        self.assertIn("Adapt", text)
        self.assertIn("Immediate", text)
        self.assertIn("Midterm", text)
        self.assertIn("Longterm", text)
        self.assertIn("Potential Findings", text)
        self.assertIn("manual_canary", text)
        self.assertIn("manual_bid", text)
        self.assertIn("observe", text)
        self.assertIn("never places, modifies, or cancels Braiins orders", text)

    def test_operator_guide_covers_architecture_and_host_recovery(self):
        text = (ROOT / "docs" / "OPERATOR_GUIDE.md").read_text()

        self.assertIn("# Braiins Ratchet Operator Guide", text)
        self.assertIn("System Architecture", text)
        self.assertIn("Tech Stack", text)
        self.assertIn("SwiftUI", text)
        self.assertIn(".macOS(.v26)", text)
        self.assertIn("Python standard library only", text)
        self.assertIn("SQLite durable state", text)
        self.assertIn("Switching To Another macOS Host", text)
        self.assertIn("State Recovery", text)
        self.assertIn("data/ratchet.sqlite*", text)
        self.assertIn("reports/EXPERIMENT_LOG.md", text)
        self.assertIn("git clone -b master", text)
        self.assertIn("owner token", text.lower())

    def test_readme_and_wrapper_expose_guides(self):
        readme = (ROOT / "README.md").read_text()
        start_here = (ROOT / "START_HERE.md").read_text()
        wrapper = (ROOT / "scripts" / "ratchet").read_text()

        self.assertIn("docs/USER_GUIDE.md", readme)
        self.assertIn("docs/OPERATOR_GUIDE.md", readme)
        self.assertIn("./scripts/ratchet guide", readme)
        self.assertIn("./scripts/ratchet operator-guide", readme)
        self.assertIn("./scripts/ratchet guide", start_here)
        self.assertIn("./scripts/ratchet operator-guide", start_here)
        self.assertIn("guide|user-guide|explain", wrapper)
        self.assertIn("operator-guide|operator", wrapper)


if __name__ == "__main__":
    unittest.main()
