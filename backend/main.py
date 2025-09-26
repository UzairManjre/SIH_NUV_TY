
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import Dict, Any, List
import os
import tempfile
import logging
from validator import validate_image
from analysis import detect_objects, segment_road_surface
from progress_tracker import save_analysis, load_previous_analysis, calculate_progress
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

class AnalysisMetadata(BaseModel):
    activity_type: str
    location_stretch: str

@app.post("/analyze-progress/")
async def analyze_progress(
    image: UploadFile = File(...),
    metadata: str = Form(...)
):
    try:
        logger = logging.getLogger(__name__)
        logger.info("Received new analysis request")
        
        # Parse metadata
        try:
            logger.debug(f"Parsing metadata: {metadata}")
            analysis_metadata = AnalysisMetadata(**json.loads(metadata))
            logger.info(f"Activity type: {analysis_metadata.activity_type}, Location: {analysis_metadata.location_stretch}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid metadata format: {e}")
            raise HTTPException(status_code=400, detail="Invalid metadata format. Must be valid JSON.")
        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            raise HTTPException(status_code=400, detail=f"Error in metadata: {str(e)}")

        # Read image
        try:
            logger.info(f"Reading image: {image.filename}, size: {image.size if hasattr(image, 'size') else 'unknown'}")
            contents = await image.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Empty image file")
                
            pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
            logger.info(f"Image loaded successfully. Size: {pil_image.size}, Mode: {pil_image.mode}")
        except Exception as e:
            logger.error(f"Error reading image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

        # 1. Validate input (CLIP)
        try:
            logger.info(f"Starting validation for activity: {analysis_metadata.activity_type}")
            is_valid = validate_image(pil_image, analysis_metadata.activity_type)
            logger.info(f"Validation result: {is_valid}")
            
            if not is_valid:
                error_msg = f"Image validation failed. The image does not appear to show '{analysis_metadata.activity_type}' content."
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=400,
                    detail=error_msg,
                )
            logger.info("Image validation passed")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error during image validation: {str(e)}"
            )

        # 2. CV Analysis (YOLO and Segmentation)
        try:
            detected_equipment = detect_objects(pil_image)
            road_surface_segmentation = segment_road_surface(pil_image)
        except Exception as e:
            logger.error(f"Error during CV analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during CV analysis: {e}")

        # 3. Progress Tracking
        progress_report = {}
        previous_analysis = load_previous_analysis(analysis_metadata.location_stretch)
        if previous_analysis:
            previous_segmentation = previous_analysis.get("road_surface_segmentation", {})
            progress_report = calculate_progress(previous_segmentation, road_surface_segmentation)

        # 4. Report Generation
        final_report = {
            "location_stretch": analysis_metadata.location_stretch,
            "activity_type": analysis_metadata.activity_type,
            "stage_of_work": max(road_surface_segmentation, key=road_surface_segmentation.get),
            "percent_completion": road_surface_segmentation, # This can be improved
            "detected_equipment": detected_equipment,
            "progress_since_last_report": progress_report,
            "observed_issues": [], # Placeholder
            "recommendations": [], # Placeholder
            "filename": image.filename,
        }

        # Save the new analysis
        save_analysis(analysis_metadata.location_stretch, final_report)

        return final_report

    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        print(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        error_msg = f"Error during analysis: {str(e)}"
        print(error_msg)
        # For development, include the full error in the response
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

    # 2. CV Analysis (YOLO and Segmentation)
    try:
        detected_equipment = detect_objects(pil_image)
        road_surface_segmentation = segment_road_surface(pil_image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during CV analysis: {e}")

    # 3. Progress Tracking
    progress_report = {}
    previous_analysis = load_previous_analysis(analysis_metadata.location_stretch)
    if previous_analysis:
        previous_segmentation = previous_analysis.get("road_surface_segmentation", {})
        progress_report = calculate_progress(previous_segmentation, road_surface_segmentation)

    # 4. Report Generation
    final_report = {
        "location_stretch": analysis_metadata.location_stretch,
        "activity_type": analysis_metadata.activity_type,
        "stage_of_work": max(road_surface_segmentation, key=road_surface_segmentation.get),
        "percent_completion": road_surface_segmentation, # This can be improved
        "detected_equipment": detected_equipment,
        "progress_since_last_report": progress_report,
        "observed_issues": [], # Placeholder
        "recommendations": [], # Placeholder
        "filename": image.filename,
    }

    # Save the new analysis
    save_analysis(analysis_metadata.location_stretch, final_report)

    return final_report


@app.post("/generate-3d-model/")
async def generate_3d_model(images: List[UploadFile] = File(...)):
    with tempfile.TemporaryDirectory() as temp_dir:
        image_paths = []
        for image in images:
            image_path = os.path.join(temp_dir, image.filename)
            with open(image_path, "wb") as buffer:
                buffer.write(await image.read())
            image_paths.append(image_path)

        # Placeholder for running OpenDroneMap
        # In a real implementation, you would run the ODM command here.
        # For example:
        # command = f"docker run -it --rm -v {temp_dir}:/code/images opendronemap/odm --project-path /code"
        # print(f"Running ODM with command: {command}")

        print(f"Saved {len(images)} images to {temp_dir}. ODM processing would start here.")

    return {"message": f"Received {len(images)} images for 3D model generation. Processing started in the background."}


