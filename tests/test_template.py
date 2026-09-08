from pathlib import Path
import unittest

class TemplateTest(unittest.TestCase):
    def test_scientific_outputs_disabled(self):
        text = (Path(__file__).resolve().parents[1] / "config/default.yaml").read_text()
        self.assertIn("scientific_outputs_enabled: false", text)

if __name__ == "__main__":
    unittest.main()
