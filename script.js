// Global variable declaration for the Pannellum viewer instance
let viewer;
let currentDayIndex = 1; // This is the main declaration

// DOM Elements
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const closeSidebar = document.getElementById('close-sidebar');

// Toggle sidebar
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('active');
});

// Close sidebar when clicking the close button
closeSidebar.addEventListener('click', () => {
    sidebar.classList.remove('active');
});

// Close sidebar when clicking outside
window.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
        sidebar.classList.remove('active');
    }
});

// Prevent clicks inside sidebar from closing it
sidebar.addEventListener('click', (e) => {
    e.stopPropagation();
});

// Timeline item click handler
document.querySelectorAll('.timeline-item label').forEach(label => {
    label.addEventListener('click', (e) => {
        const item = label.closest('.timeline-item');
        item.classList.toggle('expanded');
    });
});

// Mock data for the timeline
const mockTimelineData = {
    1: {
        status: 'completed',
        title: 'Foundation Work',
        description: 'Site preparation and foundation work completed',
        progress: 100,
        findings: [
            '✓ Site cleared and leveled',
            '✓ Foundation poured and set',
            '✓ Initial drainage installed'
        ],
        insights: [
            { type: 'positive', title: 'On Schedule', message: 'Foundation work completed as planned' },
            { type: 'info', title: 'Next Steps', message: 'Begin framing work' }
        ]
    },
    2: {
        status: 'active',
        title: 'Framing',
        description: 'Structural framing in progress',
        progress: 45,
        findings: [
            '✓ 60% of wall framing complete',
            '✓ Roof trusses delivered',
            '⚠️ Safety check needed: Unsecured materials'
        ],
        insights: [
            { type: 'warning', title: 'Attention Needed', message: 'Safety inspection required' },
            { type: 'positive', title: 'Good Progress', message: 'Ahead of schedule by 2 days' }
        ]
    },
    3: {
        status: 'pending',
        title: 'Roofing',
        description: 'Roof installation',
        progress: 0,
        findings: [
            'Scheduled to start after framing completion',
            'Materials on order',
            'Crew assigned'
        ],
        insights: [
            { type: 'info', title: 'Upcoming', message: 'Scheduled to start in 3 days' }
        ]
    }
};

// Function to update the timeline with mock data
function updateTimeline(day) {
    const data = mockTimelineData[day] || mockTimelineData[1];
    const timelineItem = document.querySelector(`.timeline-item:nth-child(${day})`);
    
    if (timelineItem) {
        // Update status classes
        timelineItem.className = 'timeline-item ' + data.status;
        
        // Update progress bar
        const progressBar = timelineItem.querySelector('.progress');
        if (progressBar) {
            progressBar.style.width = `${data.progress}%`;
        }
        
        // Update status text
        const statusEl = timelineItem.querySelector('.timeline-status');
        if (statusEl) {
            if (data.status === 'completed') {
                statusEl.textContent = '✓ Completed';
            } else if (data.status === 'active') {
                statusEl.textContent = `In Progress (${data.progress}%)`;
            } else {
                statusEl.textContent = 'Pending';
            }
        }
        
        // Update findings
        const findingsContainer = timelineItem.querySelector('.ai-findings ul');
        if (findingsContainer) {
            findingsContainer.innerHTML = data.findings
                .map(item => `<li>${item}</li>`)
                .join('');
        }
    }
}

// Function to update insights panel
function updateInsights(day) {
    const data = mockTimelineData[day] || mockTimelineData[1];
    const insightsContainer = document.querySelector('.ai-insights');
    
    if (insightsContainer) {
        // Remove existing insights
        insightsContainer.innerHTML = `
            <h3>AI Insights</h3>
            ${data.insights.map(insight => `
                <div class="insight ${insight.type}">
                    <span class="insight-icon">
                        ${insight.type === 'positive' ? '📊' : 
                          insight.type === 'warning' ? '⚠️' : 'ℹ️'}
                    </span>
                    <div class="insight-content">
                        <h4>${insight.title}</h4>
                        <p>${insight.message}</p>
                    </div>
                </div>
            `).join('')}
        `;
    }
}

// API call to analyze progress with the backend
async function analyzeProgress(day) {
    try {
        // Get the current panorama image
        const panorama = panoramaImages[day];
        if (!panorama) {
            throw new Error(`No panorama image found for day ${day}`);
        }

        // Create form data
        const formData = new FormData();
        
        // Fetch the image
        const response = await fetch(panorama.url);
        const blob = await response.blob();
        
        // Add image to form data
        formData.append('image', blob, `day_${day}.jpg`);
        
        // Add metadata
        const metadata = {
            activity_type: 'construction',
            location_stretch: `Site Day ${day}`,
            timestamp: new Date().toISOString()
        };
        formData.append('metadata', JSON.stringify(metadata));
        
        // Make the API request
        const apiResponse = await fetch('http://localhost:8001/analyze-progress/', {
            method: 'POST',
            body: formData
        });
            
        // Handle the response
        if (!apiResponse.ok) {
            let errorDetails = '';
            try {
                const errorData = await apiResponse.json();
                errorDetails = errorData.detail || JSON.stringify(errorData);
            } catch (e) {
                errorDetails = await apiResponse.text();
            }
            throw new Error(`API request failed with status ${apiResponse.status}: ${errorDetails}`);
        }
            
        const data = await apiResponse.json();
        
        // Transform the backend response to match our frontend format
        return {
            success: true,
            day: day,
            analysis: {
                status: 'completed',
                title: `Day ${day} Analysis`,
                description: 'AI analysis of construction progress',
                progress: Math.round((data.percent_completion?.building || 0) * 100),
                findings: Object.entries(data.detected_equipment || {}).map(
                    ([item, count]) => `✓ Detected ${count} ${item}${count > 1 ? 's' : ''}`
                ),
                insights: [
                    { 
                        type: 'info', 
                        title: 'Progress', 
                        message: `Building progress: ${Math.round((data.percent_completion?.building || 0) * 100)}%` 
                    },
                    ...((data.observed_issues || []).map(issue => ({
                        type: 'warning',
                        title: 'Issue Detected',
                        message: issue
                    })))
                ]
            }
        };
    } catch (error) {
        console.error('Error analyzing progress:', error);
        // If it's a validation error, provide a more user-friendly message
        if (error.message.includes('Image validation failed') || 
            error.message.includes('does not appear to show')) {
            throw new Error('The image does not appear to be a construction site. Please upload an image of a construction site.');
        }
        
        // Fall back to mock data if the API call fails
        return {
            success: false,
            day: day,
            error: error.message,
            analysis: mockTimelineData[day] || mockTimelineData[1]
        };
    }
}

// Function to load analysis for a specific day
async function loadDayAnalysis(day) {
    try {
        // Show loading state
        const statusMessages = document.getElementById('status-messages');
        if (statusMessages) {
            statusMessages.innerHTML = '<p class="status-message">Analyzing progress...</p>';
            statusMessages.style.display = 'block';
        }
        
        // Make the API call to analyze progress
        const response = await analyzeProgress(day);
        
        if (response.success) {
            // Update the UI with the analysis
            updateTimeline(day);
            updateInsights(day);
            
            // Update metrics
            updateMetrics(day);
            
            // Show success message
            if (statusMessages) {
                statusMessages.innerHTML = `
                    <p class="status-message success">
                        ✓ Analysis complete for Day ${day}
                    </p>
                `;
                // Hide the message after 3 seconds
                setTimeout(() => {
                    statusMessages.style.display = 'none';
                }, 3000);
            }
        } else {
            // Show error message but still update with available data
            if (statusMessages) {
                statusMessages.innerHTML = `
                    <p class="status-message error">
                        ⚠️ Using cached data: ${response.error}
                    </p>
                `;
                // Hide the message after 5 seconds
                setTimeout(() => {
                    statusMessages.style.display = 'none';
                }, 5000);
            }
            
            // Still update with the mock data
            updateTimeline(day);
            updateInsights(day);
            updateMetrics(day);
        }
    } catch (error) {
        console.error('Error loading analysis:', error);
        const statusMessages = document.getElementById('status-messages');
        if (statusMessages) {
            statusMessages.innerHTML = '<p class="status-message error">Error loading analysis. Please try again.</p>';
        }
    }
}

// Function to update metrics
function updateMetrics(day) {
    const metrics = {
        1: { progress: '25% Complete', schedule: 'On Schedule', risk: 'No Issues' },
        2: { progress: '50% Complete', schedule: '+2 Days Ahead', risk: '1 Safety Alert' },
        3: { progress: '75% Complete', schedule: 'On Schedule', risk: 'No Issues' }
    };
    
    const metric = metrics[day] || metrics[1];
    
    // Update metric cards
    document.querySelector('.metric-progress .data-point').textContent = metric.progress;
    document.querySelector('.metric-schedule .data-point').textContent = metric.schedule;
    document.querySelector('.metric-risk .data-point').textContent = metric.risk;
}

// Configuration for panorama images
const panoramaImages = {
    1: { name: 'Day 1 (Foundation)', url: 'images/day_1.jpg' },
    2: { name: 'Day 2 (Framing)', url: 'images/day_2.jpg' },
    3: { name: 'Day 3 (Roofing)', url: 'images/day_3.jpg' }
};

// Utility function to update the viewer with the current panorama
function updatePanoView() {
    const newPano = panoramaImages[currentDayIndex];
    
    // Update the viewer with the new panorama
    if (viewer) {
        viewer.destroy();
    }
    
    // Initialize the viewer with the current panorama
    viewer = pannellum.viewer('panorama', {
        type: 'equirectangular',
        panorama: newPano.url,
        autoLoad: true,
        compass: true,
        autoRotate: -2
    });
    
    // Update the date label
    document.getElementById('current-date-label').textContent = newPano.name;
    
    // Update button states
    document.getElementById('prev-btn').disabled = (currentDayIndex === 1);
    document.getElementById('next-btn').disabled = (currentDayIndex === Object.keys(panoramaImages).length);
    
    // Load analysis for the current day
    loadDayAnalysis(currentDayIndex);
}


// --- 2. INITIALIZATION AND ASYNCHRONOUS CALLBACK ---

// Function to update the UI when the day changes
function updateUIForDay(dayIndex) {
    // Update metrics based on the day
    const progressElement = document.querySelector('.metric-progress .data-point');
    const scheduleElement = document.querySelector('.metric-schedule .data-point');
    const riskElement = document.querySelector('.metric-risk .data-point');
    
    // Example metrics that change based on the day
    const metrics = [
        { progress: '25% Complete', schedule: 'On Schedule', risk: '2 Critical Alerts' },
        { progress: '50% Complete', schedule: '+1 Day Ahead', risk: '1 Critical Alert' },
        { progress: '75% Complete', schedule: 'On Schedule', risk: 'No Critical Alerts' }
    ];
    
    const index = Math.min(dayIndex - 1, metrics.length - 1);
    const metric = metrics[index] || metrics[metrics.length - 1];
    
    if (progressElement) progressElement.textContent = metric.progress;
    if (scheduleElement) scheduleElement.textContent = metric.schedule;
    if (riskElement) riskElement.textContent = metric.risk;
}


// currentDayIndex is already declared at the top

// Initialize the application when the window loads
window.onload = function() {
    // Set up event listeners
    document.getElementById('prev-btn').addEventListener('click', function() {
        if (currentDayIndex > 1) {
            currentDayIndex--;
            updatePanoView();
        }
    });

    document.getElementById('next-btn').addEventListener('click', function() {
        if (currentDayIndex < Object.keys(panoramaImages).length) {
            currentDayIndex++;
            updatePanoView();
        }
    });

    // Initialize the first panorama and load initial data
    updatePanoView();
    
    // Initialize all timeline items
    Object.keys(mockTimelineData).forEach(day => {
        updateTimeline(day);
    });
    
    // Load initial insights
    updateInsights(currentDayIndex);
    updateMetrics(currentDayIndex);
};