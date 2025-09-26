// Global variable declaration for the Pannellum viewer instance
let viewer;

// --- 1. CONFIGURATION (UNCHANGED) ---
const panoramaImages = {
    1: { name: 'Day 1 (Foundation)', url: 'images/day_1.jpg', volume: '450 m³'},
    2: { name: 'Day 7 (Framing)', url: 'images/day_7.jpg', volume: '310 m³'},
    3: { name: 'Day 14 (Roofing)', url: 'images/day_14.jpg', volume: '150 m³'}
};

// --- Utility function to remove temporary hotspots (UNCHANGED) ---
function removeHotspots(className) {
    if (!viewer) return;
    const hs = viewer.getContainer().querySelectorAll(`.${className}`);
    hs.forEach(h => h.remove());
}


// --- 2. INITIALIZATION AND ASYNCHRONOUS CALLBACK ---

// Define the function that holds ALL the event listeners and logic
function setupApplicationLogic() {
    
    // --- DOM Elements & State Variables ---
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const dateLabel = document.getElementById('current-date-label');
    const designToggle = document.getElementById('design-toggle');
    const viewerContainer = document.querySelector('.viewer-container'); 
    const quantifyBtn = document.getElementById('quantify-btn');
    const quantifyStatus = document.getElementById('quantify-status');
    const safetyToggle = document.getElementById('safety-toggle');
    const annotateBtn = document.getElementById('annotate-btn');
    const annotationStatus = document.getElementById('annotation-status');

    let currentDayIndex = 1; 
    const maxDayIndex = Object.keys(panoramaImages).length;

    console.log("Prev Button Element:", prevBtn);
    console.log("Next Button Element:", nextBtn);

    prevBtn.onclick = () => console.log('Prev button clicked');
    nextBtn.onclick = () => console.log('Next button clicked'); 


    // --- 3. FEATURE 1: PROGRESS BUTTONS LOGIC ---
    
    function updatePanoView() {
        const newPano = panoramaImages[currentDayIndex];
        
        // This viewer.load is now 100% safe to call
        viewer.load(newPano.url); 
        document.querySelectorAll('.status-message').forEach(el => el.textContent = '');

        dateLabel.textContent = newPano.name;
        
        prevBtn.disabled = (currentDayIndex === 1);
        nextBtn.disabled = (currentDayIndex === maxDayIndex);

        // Reset overlays and pins for a clean view on date change
        safetyToggle.checked = false;
        viewerContainer.classList.remove('heatmap-active');
        removeHotspots('pin-safety-warning'); 

        designToggle.checked = false;
        viewerContainer.style.backgroundImage = "none";
        viewerContainer.style.opacity = "1";
    }

    // Set initial state for buttons
    prevBtn.disabled = true;

    // Event listener for the NEXT button
    nextBtn.addEventListener('click', function() {
        if (currentDayIndex < maxDayIndex) {
            currentDayIndex++;
            updatePanoView();
        }
    });

    // Event listener for the PREVIOUS button
    prevBtn.addEventListener('click', function() {
        if (currentDayIndex > 1) {
            currentDayIndex--;
            updatePanoView();
        }
    });


    // --- 4. FEATURE 4: DESIGN OVERLAY TOGGLE LOGIC ---
    designToggle.addEventListener('change', function() {
        if (this.checked) {
            viewerContainer.style.backgroundImage = "url('images/overlay.png')";
            viewerContainer.style.backgroundSize = "cover"; 
            viewerContainer.style.opacity = "0.6"; 
        } else {
            viewerContainer.style.backgroundImage = "none";
            viewerContainer.style.opacity = "1";
        }
    });


    // --- 5. FEATURE 5: VOLUMETRIC MEASUREMENT LOGIC ---
    quantifyBtn.addEventListener('click', function() {
        quantifyStatus.textContent = 'Processing 3D Model Data...';
        removeHotspots('pin-volumetric');

        setTimeout(() => {
            const volume = panoramaImages[currentDayIndex].volume;

            quantifyStatus.textContent = `✅ Volumetric Analysis Complete: ${volume} of Material Remaining.`;
            
            viewer.addHotSpot({
                "pitch": -10, "yaw": 60, "text": `Stockpile Volume: ${volume}`,
                "URL": "#", "cssClass": "pin-volumetric"
            });
            
        }, 800);
    });


    // --- 6. FEATURE 6: SAFETY VIOLATION HEATMAP LOGIC ---
    safetyToggle.addEventListener('change', function() {
        if (this.checked) {
            viewerContainer.classList.add('heatmap-active');
            
            viewer.addHotSpot({
                "pitch": 15, "yaw": -10, "text": "High Risk: Unbarricaded Edge (AI Detected).",
                "URL": "#", "cssClass": "pin-safety-warning"
            });
            viewer.addHotSpot({
                "pitch": -5, "yaw": 80, "text": "AI Flag: Worker not wearing required PPE.",
                "URL": "#", "cssClass": "pin-safety-warning"
            });
        } else {
            viewerContainer.classList.remove('heatmap-active');
            removeHotspots('pin-safety-warning');
        }
    });


    // --- 7. FEATURE 2: REMOTE ANNOTATION LOGIC ---
    let isAnnotating = false;

    function handlePanoramaClick(event) {
        if (isAnnotating) {
            const pitch = viewer.getPitch();
            const yaw = viewer.getYaw();
            
            annotationStatus.textContent = "✅ Pin dropped! Custom issue logged: 'Needs immediate follow-up'.";
            
            viewer.addHotSpot({
                "pitch": pitch,
                "yaw": yaw,
                "text": "New PM Note: Issue Flagged by Remote User!",
                "URL": "#",
                "cssClass": "pin-new" 
            });
            
            isAnnotating = false;
            annotateBtn.textContent = "📍 Add Inspection Pin";
            
            viewer.getContainer().style.cursor = 'grab';
            viewer.getContainer().removeEventListener('click', handlePanoramaClick);
        }
    }

    annotateBtn.addEventListener('click', function() {
        if (!isAnnotating) {
            isAnnotating = true;
            this.textContent = "Click on the 360 View to Drop Pin...";
            annotationStatus.textContent = "Annotation mode active. Click anywhere in the 360 viewer.";
            
            viewer.getContainer().style.cursor = 'crosshair';
            viewer.getContainer().addEventListener('click', handlePanoramaClick);
        } else {
            isAnnotating = false;
            annotateBtn.textContent = "📍 Add Inspection Pin";
            viewer.getContainer().style.cursor = 'grab';
            viewer.getContainer().removeEventListener('click', handlePanoramaClick);
            annotationStatus.textContent = "Annotation cancelled.";
        }
    });
} // End of setupApplicationLogic()


// This executes the logic immediately after the DOM is fully loaded.
window.onload = function() {
    // Initialize the viewer inside the onload function
    viewer = pannellum.viewer('panorama', {
        "type": "equirectangular",
        "panorama": panoramaImages[1].url,
        "autoLoad": true,
        "compass": true,
        "autoRotate": -2,
        // *** KEY CHANGE *** Use the scene change event as a reliable trigger
        "onload": setupApplicationLogic, 
        "hotSpots": [
            {
                "pitch": 0, "yaw": -50, "text": "Critical Issue: Concrete pouring delayed by 2 days.",
                "URL": "#", "cssClass": "pin-critical"
            }
        ]
    });
};