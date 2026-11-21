"""Unit tests for the Python analysis helpers (python -m unittest discover tests)."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


vo = load("scripts/audio-analysis/voiceover.py", "voiceover")
ra = load("scripts/reference-analysis/analyze_reference.py", "analyze_reference")


class Numbers(unittest.TestCase):
    def test_values(self):
        self.assertEqual(vo.number_value("fifty-eight"), 58)
        self.assertEqual(vo.number_value("24 ,000"), 24000)
        self.assertEqual(vo.number_value("$5 .86"), 5.86)
        self.assertIsNone(vo.number_value("Malcolm"))

    def test_mismatch_classes(self):
        self.assertIn("benign", vo.classify({"script": "fifty-eight", "heard": "58"}))
        self.assertIn("number_differs", vo.classify({"script": "1956", "heard": "1965"}))
        self.assertIn("benign", vo.classify({"script": "Malcom", "heard": "Malcolm"}))
        self.assertNotIn("benign", vo.classify({"script": "refused", "heard": "accepted"}))


class Alignment(unittest.TestCase):
    def test_align_interpolates_skipped_words(self):
        script = "the ship left newark carrying boxes".split()
        asr = [{"w": w, "s": i * 0.5, "e": i * 0.5 + 0.4} for i, w in enumerate("the ship left newark boxes".split())]
        times, how, mism = vo.align(script, asr, 3.0)
        self.assertEqual(how[4], "missing")
        self.assertTrue(times[3][1] <= times[4][0] <= times[5][0])
        self.assertTrue(any(m["kind"].startswith("not heard") for m in mism))


class Cuts(unittest.TestCase):
    def test_hard_cut_detection(self):
        content = [0, 1, 1, 2, 40, 1, 1, 1, 2, 1, 1, 1, 35, 1]
        self.assertEqual(ra.detect_cuts(content, 30), [4, 12])

    def test_cuts_closer_than_min_shot_merge(self):
        content = [0, 1, 1, 2, 40, 1, 1, 1, 2, 1, 35, 1]   # 6 frames apart at 30 fps = 0.2 s < 0.25 s
        self.assertEqual(ra.detect_cuts(content, 30), [4])

    def test_motion_labels(self):
        self.assertTrue(ra.classify_motion(0.003, 0, 0, 0.1).startswith("push-in"))
        self.assertEqual(ra.classify_motion(0, 0, 0, 0.05), "static")


if __name__ == "__main__":
    unittest.main()
