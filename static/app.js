document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements - Sliders
    const inputPeriod = document.getElementById("input-period");
    const inputFeh = document.getElementById("input-feh");
    const inputAmplitude = document.getElementById("input-amplitude");
    const inputDistance = document.getElementById("input-distance");
    const inputModes = document.getElementsByName("input-mode");

    // DOM Elements - Value Displays
    const valPeriod = document.getElementById("val-period");
    const valFeh = document.getElementById("val-feh");
    const valAmplitude = document.getElementById("val-amplitude");
    const valDistance = document.getElementById("val-distance");

    // DOM Elements - Stats
    const statMv = document.getElementById("stat-mv");
    const statAppMv = document.getElementById("stat-app-mv");
    const statModulus = document.getElementById("stat-modulus");
    const statLuminosity = document.getElementById("stat-luminosity");
    const stripStatus = document.getElementById("strip-status");

    // DOM Elements - Action & Display
    const btnRender = document.getElementById("btn-render");
    const btnPlayPause = document.getElementById("btn-play-pause");
    const videoProgress = document.getElementById("video-progress");
    const video = document.getElementById("star-video");
    const loadingOverlay = document.getElementById("loading-overlay");
    const badgeCache = document.getElementById("badge-cache");

    // SVG elements
    const starIndicator = document.getElementById("star-indicator");
    const starLoopPath = document.getElementById("star-loop-path");

    // State variables
    let period = parseFloat(inputPeriod.value);
    let feh = parseFloat(inputFeh.value);
    let amplitude = parseFloat(inputAmplitude.value);
    let distance = parseFloat(inputDistance.value);
    let mode = "RRab"; // Default

    // Setup input listeners
    inputPeriod.addEventListener("input", (e) => {
        period = parseFloat(e.target.value);
        valPeriod.textContent = `${period.toFixed(2)} d`;
        
        // Auto-suggest mode based on period to be user-friendly
        if (period < 0.40) {
            setMode("RRc");
        } else if (period > 0.45) {
            setMode("RRab");
        }
        
        updateDerivedProperties();
    });

    inputFeh.addEventListener("input", (e) => {
        feh = parseFloat(e.target.value);
        valFeh.textContent = `${feh.toFixed(2)} dex`;
        updateDerivedProperties();
    });

    inputAmplitude.addEventListener("input", (e) => {
        amplitude = parseFloat(e.target.value);
        valAmplitude.textContent = `${amplitude.toFixed(2)} mag`;
        updateDerivedProperties();
    });

    inputDistance.addEventListener("input", (e) => {
        distance = parseFloat(e.target.value);
        valDistance.textContent = `${distance} pc`;
        updateDerivedProperties();
    });

    inputModes.forEach(radio => {
        radio.addEventListener("change", (e) => {
            if (e.target.checked) {
                mode = e.target.value;
                updateDerivedProperties();
            }
        });
    });

    function setMode(newMode) {
        mode = newMode;
        inputModes.forEach(radio => {
            radio.checked = (radio.value === newMode);
        });
    }

    // Physical calculations and UI updates
    function updateDerivedProperties() {
        // Absolute Magnitude MV using Period-Luminosity-Metallicity relation
        let mv = 0.0;
        if (mode === "RRab") {
            mv = -1.5 * Math.log10(period) + 0.17 * feh + 0.82;
        } else {
            mv = -1.5 * Math.log10(period) + 0.17 * feh + 0.52;
        }

        // Apparent Magnitude mV: mV = MV + 5 log10(d) - 5
        const m_v = mv + 5 * Math.log10(distance) - 5;
        const modulus = 5 * Math.log10(distance) - 5;

        // Luminosity relative to Sun: L/L_sun = 10^((M_sun - M_star)/2.5), M_sun = 4.83
        const luminosity = Math.pow(10, (4.83 - mv) / 2.5);

        // Update DOM elements
        statMv.textContent = `${mv >= 0 ? "+" : ""}${mv.toFixed(2)}`;
        statAppMv.textContent = m_v.toFixed(2);
        statModulus.textContent = modulus.toFixed(2);
        statLuminosity.textContent = luminosity.toFixed(1);

        // Instability Strip Check
        // RRc typical: P < 0.45, RRab typical: P > 0.4
        let inStrip = true;
        let warningMsg = "✓ Inside Instability Strip";
        
        if (mode === "RRab" && period < 0.38) {
            inStrip = false;
            warningMsg = "⚠ P too short for fundamental mode (RRab)";
        } else if (mode === "RRc" && period > 0.48) {
            inStrip = false;
            warningMsg = "⚠ P too long for overtone mode (RRc)";
        }

        if (inStrip) {
            stripStatus.textContent = warningMsg;
            stripStatus.classList.remove("warning");
        } else {
            stripStatus.textContent = warningMsg;
            stripStatus.classList.add("warning");
        }

        // Update the SVG loop position and size based on parameters
        updateHRDiagramStatic(mv);
    }

    // Update HR diagram elements when parameters change (static view)
    function updateHRDiagramStatic(mv) {
        // Map mv to SVG Y coordinate
        // Axis range: -0.5 (Y=50) to +1.0 (Y=230)
        // Y = 50 + (mv - (-0.5)) / (1.5) * 180
        const yCenter = 50 + ((mv - (-0.5)) / 1.5) * 180;
        
        // Map average temperature to X coordinate
        // In RR Lyrae, longer period means cooler star (further right)
        // Approximate average temp: RRc: ~7100K, RRab: ~6400K.
        // Let's create a linear relation between Period and Temp:
        // Temp range: 7500K to 6000K
        const avgTemp = 7400 - (period - 0.2) * 1400; // 0.2d -> 7400K, 1.2d -> 6000K
        // Axis range: 8000K (X=80) to 5600K (X=380)
        // X = 80 + (8000 - temp) / 2400 * 300
        const xCenter = 80 + ((8000 - avgTemp) / 2400) * 300;

        // Scale loop size by amplitude
        const rx = 15 + amplitude * 25;
        const ry = 8 + amplitude * 12;

        starLoopPath.setAttribute("cx", xCenter);
        starLoopPath.setAttribute("cy", yCenter);
        starLoopPath.setAttribute("rx", rx);
        starLoopPath.setAttribute("ry", ry);
        
        // If video is not playing, set dot to center of loop
        if (video.paused) {
            starIndicator.setAttribute("cx", xCenter);
            starIndicator.setAttribute("cy", yCenter);
        }
    }

    // Light Curve Profile function matching Python animator.py
    function getLightCurveOffset(phase) {
        const p = phase % 1.0;
        if (mode === "RRab") {
            const val = (
                0.5 * Math.sin(2 * Math.PI * p - 1.57)
                + 0.22 * Math.sin(4 * Math.PI * p - 2.8)
                + 0.10 * Math.sin(6 * Math.PI * p - 3.8)
                + 0.04 * Math.sin(8 * Math.PI * p - 4.8)
            );
            return -val * amplitude;
        } else {
            const val = 0.45 * Math.sin(2 * Math.PI * p - 1.57);
            return -val * amplitude;
        }
    }

    // Sync the SVG indicator with the video player's progress
    function syncSVGIndicator() {
        if (!video.duration || video.paused) return;

        // Video is 8 seconds long and represents exactly 2 periods (0.0 to 2.0 phase)
        const duration = video.duration;
        const currentTime = video.currentTime;
        const phase = (currentTime / duration) * 2.0;

        videoProgress.textContent = `Phase: ${phase.toFixed(3)}`;

        // Get coordinates of the loop center
        const cx = parseFloat(starLoopPath.getAttribute("cx"));
        const cy = parseFloat(starLoopPath.getAttribute("cy"));
        const rx = parseFloat(starLoopPath.getAttribute("rx"));
        const ry = parseFloat(starLoopPath.getAttribute("ry"));

        // Calculate phase-based offsets
        // Loop moves in a counter-clockwise loop in the H-R diagram
        // Temperature (x) leads brightness (y)
        const theta = phase * 2 * Math.PI;
        
        // Let's compute actual physical coordinates:
        // x represents temperature, y represents magnitude
        // For RRab, the temperature cycle is asymmetric.
        // We can model this asymmetry directly:
        const xOffset = -rx * Math.sin(theta);
        
        // Brightness (y-axis) is related to magnitude.
        // Magnitude decreases upwards (brighter is lower Y coordinate)
        const yOffset = -ry * Math.cos(theta - 0.5); // Add a small phase shift for realistic loop

        starIndicator.setAttribute("cx", cx + xOffset);
        starIndicator.setAttribute("cy", cy + yOffset);

        // Animate color based on brightness
        // Map brightness to dot fill color: yellow-orange (cool) to light-blue (hot)
        const normBrightness = (getLightCurveOffset(phase) / (1.0 * amplitude) + 0.5); // -0.5..0.5 to 0..1
        
        // Color transition
        let r, g, b;
        if (normBrightness < 0.5) {
            // Cool phase (Orange-Red: 255, 94, 19) to Medium
            const t = normBrightness * 2;
            r = Math.round(255 - t * (255 - 230));
            g = Math.round(94 + t * (200 - 94));
            b = Math.round(19 + t * (100 - 19));
        } else {
            // Medium to Hot phase (Light-Blue: 212, 240, 255)
            const t = (normBrightness - 0.5) * 2;
            r = Math.round(230 + t * (212 - 230));
            g = Math.round(200 + t * (240 - 200));
            b = Math.round(100 + t * (255 - 100));
        }
        starIndicator.setAttribute("fill", `rgb(${r}, ${g}, ${b})`);
    }

    // Use requestAnimationFrame for smooth UI sync
    let animFrameId = null;
    function startSyncLoop() {
        function tick() {
            syncSVGIndicator();
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

    // Render Animation Trigger
    btnRender.addEventListener("click", async () => {
        // Show loading state
        loadingOverlay.classList.remove("hidden");
        btnRender.disabled = true;
        btnRender.querySelector(".spinner").classList.remove("hidden");
        btnRender.querySelector(".btn-text").textContent = "Rendering...";

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
            
            // Update cache badge
            if (badgeCache) {
                if (data.cached) {
                    badgeCache.textContent = "Pre-rendered (Cached)";
                    badgeCache.style.borderColor = "var(--accent-secondary)";
                } else {
                    badgeCache.textContent = "Newly Rendered";
                    badgeCache.style.borderColor = "var(--color-success)";
                    badgeCache.style.color = "var(--color-success)";
                }
            }

            // Load and play new video
            video.src = data.video_url;
            video.muted = true;
            video.load();
            video.play().catch(err => {
                console.warn("Autoplay was blocked by browser policy. User interaction required:", err);
                btnPlayPause.textContent = "▶ Play";
            });
            
            // Hide loading state
            loadingOverlay.classList.add("hidden");
            btnRender.disabled = false;
            btnRender.querySelector(".spinner").classList.add("hidden");
            btnRender.querySelector(".btn-text").textContent = "Generate Manim Animation";

        } catch (error) {
            console.error("Render failed:", error);
            alert(`Rendering Failed:\n${error.message}`);
            
            loadingOverlay.classList.add("hidden");
            btnRender.disabled = false;
            btnRender.querySelector(".spinner").classList.add("hidden");
            btnRender.querySelector(".btn-text").textContent = "Generate Manim Animation";
        }
    });

    // Initialize UI on load
    updateDerivedProperties();

    // Trigger initial render (uses default parameters to pre-cache)
    btnRender.click();
});
