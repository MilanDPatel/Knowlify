import importlib.util
from pathlib import Path
import sys
import json
from manim import Scene, Mobject

# ===============================================================
#  TIMELINE LAYOUT ANALYZER (Manim CE 0.19.x)
#  - Captures object positions at EVERY animation checkpoint
#  - Detects collisions across the entire timeline
# ===============================================================

class TimelineCapturingScene(Scene):
    """Captures layout at multiple animation checkpoints."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeline_snapshots = []
        self.current_time = 0
        
    def play(self, *args, **kwargs):
        """Capture layout BEFORE animation plays."""
        self._capture_snapshot(f"before_play_{len(self.timeline_snapshots)}")
        # Don't actually play, just update time
        duration = kwargs.get('run_time', 1.0)
        self.current_time += duration
        
    def wait(self, duration=1, **kwargs):
        """Capture layout after wait."""
        self.current_time += duration
        self._capture_snapshot(f"after_wait_{len(self.timeline_snapshots)}")
        
    def add(self, *mobjects):
        """Capture layout when objects are added."""
        super().add(*mobjects)
        self._capture_snapshot(f"after_add_{len(self.timeline_snapshots)}")
        
    def remove(self, *mobjects):
        """Capture layout when objects are removed."""
        super().remove(*mobjects)
        self._capture_snapshot(f"after_remove_{len(self.timeline_snapshots)}")
    
    def _capture_snapshot(self, label):
        """Capture current layout state."""
        snapshot = {
            "time": self.current_time,
            "label": label,
            "mobjects": []
        }
        
        for mobj in self.mobjects:
            info = self._extract_mobject_info(mobj)
            if info:
                snapshot["mobjects"].append(info)
                # Also capture submobjects
                self._capture_submobjects(mobj, snapshot["mobjects"])
        
        self.timeline_snapshots.append(snapshot)
    
    def _capture_submobjects(self, parent, mobject_list):
        """Recursively capture submobject positions."""
        for child in parent.submobjects:
            info = self._extract_mobject_info(child)
            if info:
                mobject_list.append(info)
            self._capture_submobjects(child, mobject_list)
    
    def _extract_mobject_info(self, mobj: Mobject):
        """Extract bounding box data."""
        try:
            left = float(mobj.get_left()[0])
            right = float(mobj.get_right()[0])
            bottom = float(mobj.get_bottom()[1])
            top = float(mobj.get_top()[1])
            width = right - left
            height = top - bottom
            center = [float(x) for x in mobj.get_center()]
            
            return {
                "id": id(mobj),
                "type": type(mobj).__name__,
                "left": left,
                "bottom": bottom,
                "right": right,
                "top": top,
                "width": width,
                "height": height,
                "center": center,
                "visible": True
            }
        except Exception:
            return None


def load_scene_from_file(script_path):
    """Load Scene class from script file."""
    script_path = Path(script_path).resolve()
    spec = importlib.util.spec_from_file_location("generated_scene", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generated_scene"] = module
    spec.loader.exec_module(module)
    
    scene_classes = [
        obj for obj in module.__dict__.values()
        if isinstance(obj, type) and issubclass(obj, Scene) and obj is not Scene
    ]
    
    if not scene_classes:
        raise ValueError("No Scene subclass found in script.")
    
    return scene_classes[0]


def extract_timeline_layout(script_path: str):
    """Extract layout at multiple timeline points."""
    SceneClass = load_scene_from_file(script_path)
    
    # Create scene with timeline tracking
    scene = SceneClass()
    scene.__class__ = type("TrackedScene", (TimelineCapturingScene,), {})
    
    # Initialize tracking
    scene.timeline_snapshots = []
    scene.current_time = 0
    
    # Run construct
    scene.construct()
    
    return scene.timeline_snapshots


def detect_collisions(timeline_data):
    """Detect overlaps across all timeline snapshots."""
    all_collisions = []
    
    for snapshot in timeline_data:
        time = snapshot["time"]
        mobjects = snapshot["mobjects"]
        
        # Check each pair for overlap
        for i, obj1 in enumerate(mobjects):
            for obj2 in mobjects[i+1:]:
                # Skip if same object or empty objects
                if obj1["width"] < 0.01 or obj1["height"] < 0.01:
                    continue
                if obj2["width"] < 0.01 or obj2["height"] < 0.01:
                    continue
                
                # Check bounding box overlap
                x_overlap = not (obj1["right"] < obj2["left"] or obj2["right"] < obj1["left"])
                y_overlap = not (obj1["top"] < obj2["bottom"] or obj2["top"] < obj1["bottom"])
                
                if x_overlap and y_overlap:
                    # Calculate overlap area
                    overlap_width = min(obj1["right"], obj2["right"]) - max(obj1["left"], obj2["left"])
                    overlap_height = min(obj1["top"], obj2["top"]) - max(obj1["bottom"], obj2["bottom"])
                    overlap_area = overlap_width * overlap_height
                    
                    all_collisions.append({
                        "time": time,
                        "snapshot_label": snapshot["label"],
                        "object1": {
                            "type": obj1["type"],
                            "center": obj1["center"],
                            "size": [obj1["width"], obj1["height"]]
                        },
                        "object2": {
                            "type": obj2["type"],
                            "center": obj2["center"],
                            "size": [obj2["width"], obj2["height"]]
                        },
                        "overlap_area": overlap_area
                    })
    
    return all_collisions


if __name__ == "__main__":
    test_file = "temp_generated_scene.py"
    timeline = extract_timeline_layout(test_file)
    collisions = detect_collisions(timeline)
    
    print("=== TIMELINE SNAPSHOTS ===")
    print(json.dumps(timeline, indent=2))
    
    print("\n=== DETECTED COLLISIONS ===")
    if collisions:
        print(f"Found {len(collisions)} collision(s):")
        print(json.dumps(collisions, indent=2))
    else:
        print("No collisions detected!")