
from ultralytics import YOLO
from PIL import Image
import numpy as np
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
from torch import nn

# Load the YOLOv8 model
# This will download the model on the first run
yolo_model = YOLO("yolov8n.pt")

# Load the SegFormer model
# This will download the model on the first run
seg_image_processor = SegformerImageProcessor.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")
seg_model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")

def detect_objects(image: Image.Image) -> dict:
    """
    Detects objects in an image using YOLOv8.

    Args:
        image: The image to analyze.

    Returns:
        A dictionary containing the counts of detected objects.
    """
    # Run the model on the image
    results = yolo_model(image)

    # Get the detected class names and their counts
    names = yolo_model.names
    detected_objects = {names[int(c)]: 0 for r in results for c in r.boxes.cls}
    for r in results:
        for c in r.boxes.cls:
            detected_objects[names[int(c)]] += 1

    return detected_objects

def segment_road_surface(image: Image.Image) -> dict:
    """
    Performs semantic segmentation on the road surface using SegFormer.

    Args:
        image: The image to analyze.

    Returns:
        A dictionary with the percentage of the image covered by each class.
    """
    inputs = seg_image_processor(images=image, return_tensors="pt")
    outputs = seg_model(**inputs)
    logits = outputs.logits.cpu()

    upsampled_logits = nn.functional.interpolate(
        logits,
        size=image.size[::-1],
        mode="bilinear",
        align_corners=False,
    )

    pred_seg = upsampled_logits.argmax(dim=1)[0]
    
    # For now, we will just return the raw segmentation mask.
    # In the future, we can map the labels to the desired classes.
    
    # Calculate the percentage of each class
    total_pixels = pred_seg.shape[0] * pred_seg.shape[1]
    unique, counts = np.unique(pred_seg, return_counts=True)
    percentages = {seg_model.config.id2label[i]: count / total_pixels for i, count in zip(unique, counts)}

    return percentages

