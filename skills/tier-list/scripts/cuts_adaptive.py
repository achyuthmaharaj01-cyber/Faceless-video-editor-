"""Adaptive cut detection (PySceneDetect AdaptiveDetector) on a downscaled copy.
Usage: python -I cuts_adaptive.py video.mp4 out_times.json"""
import sys, json
from scenedetect import open_video, SceneManager
from scenedetect.detectors import AdaptiveDetector
v = open_video(sys.argv[1]); sm = SceneManager(); sm.auto_downscale = False; sm.downscale = 4
sm.add_detector(AdaptiveDetector(adaptive_threshold=3.0, min_scene_len=6, min_content_val=12.0))
sm.detect_scenes(v, frame_skip=1)
cuts = [s[0].get_seconds() for s in sm.get_scene_list()][1:]
json.dump({"cuts": [round(c, 3) for c in cuts]}, open(sys.argv[2], "w")); print(len(cuts))
