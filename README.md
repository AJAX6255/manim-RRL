# manim-RRL Astrophysics Simulator

An interactive astrophysics simulation that models and visualizes the pulsation, light curves, and radial velocity curves of RR Lyrae variable stars (RRab and RRc types) using Python, FastAPI, and Manim.

## Architecture Overview

- **Backend**: FastAPI web server (`main.py`) which manages REST requests and calls Manim as a subprocess (`animator.py`) to render custom video animations based on period, metallicity, amplitude, mode, and distance.
- **Frontend**: A sleek, responsive dashboard (`static/index.html`, `static/style.css`, `static/app.js`) to adjust physical parameters, trigger rendering, and view the simulated pulsation animations.
- **Tests & Diagnostics**: A Playwright-based testing script (`test.py`) that analyzes the page structure, z-index layering, and stacking contexts to output a detailed `stacking_report.json`.

---

## Local Setup & Development

### Prerequisites

1. **Python 3.13+**
2. **uv** (Fast Python package manager)
3. **System Packages for Manim**: Manim relies on several system libraries.
   - **Windows**: Install [FFmpeg](https://ffmpeg.org/) and add it to your PATH.
   - **macOS**: `brew install ffmpeg pango scipy`
   - **Linux**: `sudo apt-get install ffmpeg libpango1.0-dev`

### Installation

Sync all dependencies within a local virtual environment:

```bash
uv sync
```

### Running the Server

Start the FastAPI server locally:

- **Windows Shortcut**: Double-click `start_server.bat` or run `powershell ./start_server.ps1`
- **Manual Command**:
  ```bash
  uv run python main.py
  ```

Once running, navigate to `http://localhost:8000/` in your browser.

---

## Running DOM Diagnostics (Playwright)

To audit CSS stacking contexts, z-index hierarchy, and HTML elements:

1. Ensure the local server is running at `http://localhost:8000/`.
2. Install Playwright browsers:
   ```bash
   uv run playwright install chromium
   ```
3. Run the test script:
   ```bash
   uv run python test.py
   ```
4. Check the generated console output and the resulting `stacking_report.json`.

If testing a deployed version, set the `TEST_URL` environment variable:
```bash
# Windows (CMD)
set TEST_URL=https://your-deployed-service.run.app/
# PowerShell
$env:TEST_URL="https://your-deployed-service.run.app/"
# macOS/Linux
export TEST_URL="https://your-deployed-service.run.app/"

uv run python test.py
```

---

## Containerization

You can package the application into a Docker container. The included Dockerfile compiles all system packages for Manim Community and runs the FastAPI server.

### 1. Build the Docker Image
```bash
docker build -t manim-rrl .
```

### 2. Run the Container Locally
```bash
docker run -p 8000:8000 -e PORT=8000 manim-rrl
```
Open `http://localhost:8000/` to verify it works.

---

## Google Cloud Run Deployment

Google Cloud Run is an ideal serverless environment for running this application.

### 1. Deploy Using Google Cloud Build & Cloud Run
Ensure you have the [Google Cloud SDK](https://cloud.google.com/sdk) installed and authenticated.

Run the following command in the root directory to build and deploy the application:

```bash
gcloud run deploy manim-rrl \
  --source . \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2
```

> [!IMPORTANT]
> **Performance Configuration**: Manim rendering is CPU and memory-intensive. We recommend deploying Cloud Run with at least **2 CPU cores** and **2 GiB of memory** (configured in the command above) to ensure quick, stable rendering.

### Ephemeral Caching Notice
The server stores rendered video files in the `./media` directory inside the container. Since Cloud Run instances are ephemeral and scale down to zero when idle:
- Generated videos will be lost when container instances are recycled.
- The next request for the same parameters will trigger a re-render.
- If you require persistent caching, configure a GCS bucket and mount it as a Cloud Storage volume at `/app/media` (or configure `main.py` to write/read from a Cloud Storage client).
