document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const btnPlayPause = document.getElementById("btn-play-pause");
    const videoProgress = document.getElementById("video-progress");
    const video = document.getElementById("star-video");
    const loadingOverlay = document.getElementById("loading-overlay");

    // State variables (default parameters for the initial video)
    const period = 0.60;
    const feh = -1.50;
    const amplitude = 0.80;
    const distance = 1000;
    const mode = "RRab";

    // Sync the progress text with the video player's progress
    function syncProgress() {
        if (!video.duration || video.paused) return;

        // Video is 8 seconds long and represents exactly 2 periods (0.0 to 2.0 phase)
        const duration = video.duration;
        const currentTime = video.currentTime;
        const phase = (currentTime / duration) * 2.0;

        videoProgress.textContent = `Phase: ${phase.toFixed(3)}`;
    }

    // Use requestAnimationFrame for smooth UI sync
    let animFrameId = null;
    function startSyncLoop() {
        function tick() {
            syncProgress();
            animFrameId = requestAnimationFrame(tick);
        }
        tick();
    }

    function stopSyncLoop() {
        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
            animFrameId = null;
        }
    }

    // Video play/pause handling
    btnPlayPause.addEventListener("click", () => {
        if (video.paused) {
            video.play();
            btnPlayPause.textContent = "⏸ Pause";
            startSyncLoop();
        } else {
            video.pause();
            btnPlayPause.textContent = "▶ Play";
            stopSyncLoop();
        }
    });

    video.addEventListener("play", () => {
        btnPlayPause.textContent = "⏸ Pause";
        startSyncLoop();
    });

    video.addEventListener("pause", () => {
        btnPlayPause.textContent = "▶ Play";
        stopSyncLoop();
    });

    // Render/Load Animation
    async function loadInitialVideo() {
        // Show loading state
        if (loadingOverlay) {
            loadingOverlay.classList.remove("hidden");
        }

        const payload = {
            period: period,
            metallicity: feh,
            amplitude: amplitude,
            mode: mode,
            distance: distance
        };

        try {
            const response = await fetch("/api/render", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Server error during rendering");
            }

            const data = await response.json();
            
            // Load and play new video
            video.src = data.video_url;
            video.muted = true;
            video.load();
            video.play().catch(err => {
                console.warn("Autoplay was blocked by browser policy:", err);
                btnPlayPause.textContent = "▶ Play";
            });
            
            // Hide loading state
            if (loadingOverlay) {
                loadingOverlay.classList.add("hidden");
            }

        } catch (error) {
            console.error("Render failed:", error);
            if (loadingOverlay) {
                loadingOverlay.classList.add("hidden");
            }
        }
    }

    // Trigger initial video load
    loadInitialVideo();
});
