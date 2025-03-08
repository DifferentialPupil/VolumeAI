import os
import numpy as np
from vision_agent.tools import *
from vision_agent.tools.planner_tools import judge_od_results
from typing import *
from pillow_heif import register_heif_opener
register_heif_opener()
import vision_agent as va
from vision_agent.tools import register_tool

from typing import Any, Dict, List
import numpy as np
from vision_agent.tools import (
    load_image,
    save_image,
    overlay_segmentation_masks
)

# This tool was obtained from calling get_tool_for_task previously:
from vision_agent.tools import countgd_sam2_instance_segmentation

def process_junk_image(image_path: str) -> Dict[str, Any]:
    """
    Processes an image of junk items, detects objects, estimates volumes,
    overlays segmentation masks, and returns a summary of volumes.

    Parameters
    ----------
    image_path : str
        The path or URL to the input image.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing:
          - 'detections': The list of detected objects with labels and scores
          - 'object_volumes': A dictionary of object types to a list of volumes
          - 'total_volume': The total estimated volume (m³)
          - 'volume_range': A (min, max) tuple for the overall volume uncertainty
          - 'output_image': The file path where the overlaid image is saved
    """

    # 1. Load the image
    image = load_image(image_path)

    # 2. Detect objects with instance segmentation
    # Prompt includes the potential junk categories
    prompt = "trash bag, wooden debris, construction debris, garbage, pipe"
    detections = countgd_sam2_instance_segmentation(prompt, image)

    # 3. Compute approximate volumes
    # For simplicity, use a reference dimension approach:
    #   - Standard trash bag ~0.125 m^3
    #   - (We apply a basic scaled bounding-box approach)
    #   - More advanced methods may incorporate actual depth/camera calibration
    object_volumes = {}
    reference_volume = 0.125  # cubic meters for a standard trash bag, used as a base reference

    # Gather average bounding box size for any "trash bag" to establish scale
    trash_bag_bboxes = [
        det["bbox"] for det in detections if det["label"] == "trash bag"
    ]
    if trash_bag_bboxes:
        avg_bag_width = np.mean([(b[2] - b[0]) for b in trash_bag_bboxes])
    else:
        avg_bag_width = 0.2  # fallback guess

    def estimate_volume(bbox: List[float], label: str, score: float) -> Dict[str, float]:
        # Basic bounding box volume estimate using relative scale
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        # We'll treat depth as similar to width:
        depth = width

        # Scale factor is ratio of box volume to reference trash bag bounding volume
        bag_vol_ratio = (width * height * depth) / (avg_bag_width ** 3 if avg_bag_width else 1e-3)

        # Base volume
        base_volume = bag_vol_ratio * reference_volume

        # Adjust for object type
        if label == "pipe":
            base_volume *= 0.25  # pipes are hollow
        elif label == "wooden debris":
            base_volume *= 0.5   # wooden debris is often flat boards, half the volume
        elif label == "construction debris":
            base_volume *= 0.7   # has void spaces
        elif label == "garbage":
            base_volume *= 1.0   # assume similar to trash bag
        elif label == "trash bag":
            base_volume *= 1.0   # same reference

        # Detection confidence modifies uncertainty
        # We'll define min/max range around base_volume based on the detection score
        # (1 - score) * 50% max deviation
        uncertainty_factor = (1 - score) * 0.5
        min_vol = base_volume * (1 - uncertainty_factor)
        max_vol = base_volume * (1 + uncertainty_factor)

        return {
            "volume": base_volume,
            "min_volume": min_vol,
            "max_volume": max_vol
        }

    overall_min = 0.0
    overall_max = 0.0
    total = 0.0
    count = 0

    for det in detections:
        label = det["label"]
        if label not in object_volumes:
            object_volumes[label] = []
        vol_info = estimate_volume(det["bbox"], label, det["score"])
        object_volumes[label].append(vol_info["volume"])
        overall_min += vol_info["min_volume"]
        overall_max += vol_info["max_volume"]
        total += vol_info["volume"]
        count += 1

    # 4. Overlay masks on the original image
    result_image = overlay_segmentation_masks(image, detections)

    # 5. Save the resulting image to disk
    output_path = "junk_output.png"
    save_image(result_image, output_path)

    # Combine results
    summary = {
        "detections": detections,
        "object_volumes": object_volumes,
        "total_volume": total,
        "volume_range": (overall_min, overall_max),
        "output_image": output_path
    }

    return summary
