
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

# Load the CLIP model and processor
# This will download the model on the first run
model_name = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(model_name)
model = CLIPModel.from_pretrained(model_name)

def validate_image(image: Image.Image, activity_type: str) -> bool:
    """
    Validates if the image content matches the activity type using CLIP.

    Args:
        image: The image to validate.
        activity_type: The expected activity type (e.g., 'asphalt laying').

    Returns:
        True if the image and text are similar, False otherwise.
    """
    # Prepare the inputs
    inputs = processor(
        text=[f"a photo of {activity_type}", "a photo of a different activity"],
        images=image,
        return_tensors="pt",
        padding=True
    )

    # Get the similarity scores
    with torch.no_grad():
        outputs = model(**inputs)
    
    # The logits_per_image are the similarity scores between the image and each text description
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)

    # Check if the probability of the correct description is the highest
    # This is a simple way to check for a match. 
    # A more robust way would be to check if the probability is above a certain threshold.
    return torch.argmax(probs) == 0

