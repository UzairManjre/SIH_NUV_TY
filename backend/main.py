
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
import json
from typing import Dict, Any, List
import os
import tempfile
from validator import validate_image
from analysis import detect_objects, segment_road_surface
from progress_tracker import save_analysis, load_previous_analysis, calculate_progress
from PIL import Image
import io

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

class AnalysisMetadata(BaseModel):
    activity_type: str
    location_stretch: str

@app.post("/analyze-progress/")
async def analyze_progress(
    metadata: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        metadata_dict = json.loads(metadata)
        analysis_metadata = AnalysisMetadata(**metadata_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata format: {e}")

    image_bytes = await image.read()
    pil_image = Image.open(io.BytesIO(image_bytes))

    # 1. Validate input (CLIP)
    try:
        is_valid = validate_image(pil_image, analysis_metadata.activity_type)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed. Image does not appear to show '{analysis_metadata.activity_type}'.",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during validation: {e}")

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


