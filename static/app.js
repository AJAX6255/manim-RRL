document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const btnPlayPause = document.getElementById("btn-play-pause");
    const videoProgress = document.getElementById("video-progress");
    const video = document.getElementById("star-video");
    const loadingOverlay = document.getElementById("loading-overlay");

    // Sync the progress text with the video player's progress
    function syncProgress() {
        if (!video.duration || video.paused) return;

        // Video represents exactly 2 periods (0.0 to 2.0 phase)
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

    // Try to autoplay video on load
    video.play().catch(err => {
        console.warn("Autoplay was blocked by browser policy:", err);
        btnPlayPause.textContent = "▶ Play";
    });
});
