import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-review.py"
SPEC = importlib.util.spec_from_file_location("prepare_review", SCRIPT)
prepare_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = prepare_review
SPEC.loader.exec_module(prepare_review)


class PrepareReviewHelpersTest(unittest.TestCase):
    def test_parse_numstat_counts_text_and_binary_changes(self):
        numstat = "10\t2\tsrc/app.py\n-\t-\tassets/logo.png\n0\t4\tREADME.md\n"

        self.assertEqual(prepare_review.parse_numstat(numstat), (10, 6, 2, 1))

    def test_safe_patch_name_preserves_useful_path_context(self):
        patch_name = prepare_review.safe_patch_name("src/topo review/helpers.py")

        self.assertEqual(patch_name, "src__topo_review__helpers.py")

    def test_safe_patch_name_never_returns_empty_name(self):
        self.assertEqual(prepare_review.safe_patch_name("!!!"), "_")


if __name__ == "__main__":
    unittest.main()
