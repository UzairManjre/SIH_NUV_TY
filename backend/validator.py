from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the CLIP model and processor
# This will download the model on the first run
try:
    model_name = "openai/clip-vit-base-patch32"
    logger.info(f"Loading CLIP model: {model_name}")
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    logger.info("CLIP model loaded successfully")
except Exception as e:
    logger.error(f"Error loading CLIP model: {str(e)}")
    raise

def validate_image(image: Image.Image, activity_type: str) -> bool:
    """
    Validates if the image content matches the activity type using CLIP.

    Args:
        image: The image to validate.
        activity_type: The expected activity type (e.g., 'construction').

    Returns:
        True if the image and text are similar, False otherwise.
    """
    try:
        logger.info(f"Starting validation for activity: {activity_type}")
        
        # Define construction-related prompts
        construction_prompts = [
            f"a photo of {activity_type}",
            "a photo of a construction site",
            "a photo of a building under construction",
            "a photo of construction equipment"
        ]
        
        # Add a non-construction prompt for comparison
        negative_prompt = "a photo of a natural landscape"
        
        # Prepare the inputs
        text_prompts = construction_prompts + [negative_prompt]
        
        logger.debug(f"Using prompts: {text_prompts}")
        
        # Process the image and text
        inputs = processor(
            text=text_prompts,
            images=image,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        # Get the similarity scores
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Calculate probabilities
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        
        # Calculate the average probability for construction-related prompts
        construction_probs = probs[0, :-1].mean().item()
        non_construction_prob = probs[0, -1].item()
        
        # Calculate confidence score (how much more likely is it construction vs not)
        confidence = construction_probs / (construction_probs + non_construction_prob)
        
        # Set a threshold (0.6 means 60% confidence it's construction-related)
        threshold = 0.6
        is_valid = confidence > threshold
        
        logger.info(
            f"Validation results - "
            f"Construction confidence: {confidence:.2f}, "
            f"Threshold: {threshold}, "
            f"Is valid: {is_valid}"
        )
        logger.debug(f"All probabilities: {probs.tolist()}")
        
        return is_valid
    except Exception as e:
        print(f"Error in validate_image: {str(e)}")
        # Fail validation if error occurs
        return False
