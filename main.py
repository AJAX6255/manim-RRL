import os
import hashlib
import subprocess
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manim-rrl")

app = FastAPI(title="manim-RRL Astrophysics Simulator")

# Ensure required folders exist
os.makedirs("static", exist_ok=True)
os.makedirs("media", exist_ok=True)

class RenderRequest(BaseModel):
    period: float
    metallicity: float
    amplitude: float
    mode: str
    distance: float

@app.post("/api/render")
def render_animation(req: RenderRequest):
    # Validate parameters
    if req.period < 0.1 or req.period > 2.0:
        raise HTTPException(status_code=400, detail="Period must be between 0.1 and 2.0 days.")
    if req.metallicity < -3.0 or req.metallicity > 0.5:
        raise HTTPException(status_code=400, detail="Metallicity must be between -3.0 and 0.5 dex.")
    if req.amplitude < 0.1 or req.amplitude > 2.0:
        raise HTTPException(status_code=400, detail="Amplitude must be between 0.1 and 2.0 mag.")
    if req.mode not in ["RRab", "RRc"]:
        raise HTTPException(status_code=400, detail="Mode must be 'RRab' or 'RRc'.")
    if req.distance < 10 or req.distance > 10000:
        raise HTTPException(status_code=400, detail="Distance must be between 10 and 10000 parsecs.")

    # Calculate parameter hash
    param_str = f"{req.period:.2f}_{req.metallicity:.2f}_{req.amplitude:.2f}_{req.mode}_{req.distance:.0f}"
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    output_filename = f"rrl_{param_hash}"
    
    # Path where Manim will write the file (using low quality 480p15)
    manim_output_dir = os.path.join("media", "videos", "animator", "480p15")
    video_path = os.path.join(manim_output_dir, f"{output_filename}.mp4")
    
    logger.info(f"Requested render with hash {param_hash} for parameters: {param_str}")
    
    if os.path.exists(video_path):
        logger.info(f"Found cached video at {video_path}")
        return {
            "status": "success",
            "video_url": f"/media/videos/animator/480p15/{output_filename}.mp4",
            "cached": True
        }
        
    logger.info(f"Cached video not found. Starting Manim render...")
    
    # Set env vars to pass parameters to the Manim script
    env = os.environ.copy()
    env["RRL_PERIOD"] = str(req.period)
    env["RRL_METALLICITY"] = str(req.metallicity)
    env["RRL_AMPLITUDE"] = str(req.amplitude)
    env["RRL_MODE"] = req.mode
    env["RRL_DISTANCE"] = str(req.distance)
    
    # Command: run manim in low quality (-ql) and warn logging only (-v WARNING)
    # Using uv run ensures it executes in our virtual environment context
    cmd = [
        "uv", "run", "manim",
        "-ql",
        "-v", "WARNING",
        "animator.py", "RRStarPulsation",
        "-o", output_filename
    ]
    
    try:
        # Run subprocess
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Manim render completed successfully.")
        
        # Verify file exists after render
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Manim reported success, but output file {video_path} was not found.")
            
        return {
            "status": "success",
            "video_url": f"/media/videos/animator/480p15/{output_filename}.mp4",
            "cached": False
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Manim render failed with exit code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise HTTPException(
            status_code=500,
            detail=f"Manim rendering failed: {e.stderr or e.stdout}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during render: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint: serves index.html
@app.get("/")
def get_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>manim-RRL Backend Running</h1><p>Frontend assets not found yet.</p>")

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount media directory to serve the rendered videos
app.mount("/media", StaticFiles(directory="media"), name="media")

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    uvicorn.run("main:app", host=host, port=port, reload=reload)
