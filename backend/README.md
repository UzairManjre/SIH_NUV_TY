
# Agentic AI for Road Construction Monitoring

This backend server provides an API for analyzing drone imagery of road construction sites.

## Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    -   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

Once the setup is complete, you can run the server with the following command:

```bash
uvicorn main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

## API Endpoints

-   `GET /`: Returns a welcome message.
-   `POST /analyze-progress/`: Analyzes a single image for progress.
-   `POST /generate-3d-model/`: Starts the 3D model generation process (placeholder).

### `/analyze-progress/`

This endpoint accepts a multipart form with two fields:

-   `metadata`: A JSON string with the following structure:
    ```json
    {
        "activity_type": "asphalt laying",
        "location_stretch": "KM-5.2 to KM-5.8, NH-48"
    }
    ```
-   `image`: The image file (JPEG/PNG).

### `/generate-3d-model/`

This endpoint accepts a multipart form with a field named `images` that can contain multiple image files.

**Note:** The 3D model generation with OpenDroneMap is a placeholder. To make it work, you need to have Docker installed and running, and the ODM docker image pulled.
