// A queue to hold the files dropped by the user
let fileQueue = [];
// A map to store temporary object URLs for previews to avoid re-creating them and to manage memory
let filePreviews = new Map();

function printToOutput(text) {
    const outputArea = document.getElementById('output-area');
    outputArea.style.opacity = 0;
    setTimeout(() => {
        outputArea.textContent = text;
        outputArea.style.opacity = 1;
    }, 500);
}

window.onload = function () {
    eel.ui_ready();
};

// Function to clear all widgets from the interface
function clearAllWidgets() {
    // Find all elements with 'widget' class
    const widgets = document.querySelectorAll('.widget');
    
    // Animate each widget's disappearance before removal
    widgets.forEach(widget => {
        // First remove the 'active' class to trigger fade-out animation
        widget.classList.remove('active');
        
        // Wait for the fade-out animation to complete before removing from DOM
        setTimeout(() => {
            if (widget && widget.parentNode) {
                widget.parentNode.removeChild(widget);
            }
        }, 300); // Match this to your CSS transition time (300ms)
    });
    
    // Return the count of widgets that were cleared
    return widgets.length;
}

// Expose the function to eel so it can be called from Python
eel.expose(clearAllWidgets);
eel.expose(printToOutput);
eel.expose(updateBottomLeftOutput);

function getYouTubeVideoId(url) {
    try {
        // Decode URL to handle encoded characters like \u0026
        url = decodeURIComponent(url);

        // Regex to match various YouTube URL formats
        const regExp = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:v\/|embed\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regExp);

        const videoId = match ? match[1] : null;
        console.log("Extracted Video ID:", videoId); // Debugging
        return videoId;
    } catch (error) {
        console.error("Error extracting video ID:", error, url);
        return null;
    }
}

// Expose the createWidget function to eel
eel.expose(createWidget);
function createWidget(id, title, type, content, x = 100, y = 100) {
    return new Promise((resolve) => {
        const widget = new Widget(id, title, type, content, x, y);
        resolve(widget);
    });
}

class Widget {
    constructor(id, title, type, content, x, y) {
        this.element = this.createWidget(id, title, type, content);
        this.setPosition(x, y);
        this.setupDragging();
        this.setupResizing();
        this.setupRightClickClose(); // Add right-click event handler
        document.body.appendChild(this.element);
        this.autoSize();
        setTimeout(() => this.element.classList.add('active'), 10);
    }

    createWidget(id, title, type, content) {
        const widget = document.createElement('div');
        widget.className = 'widget';
        widget.id = id;

        const header = document.createElement('div');
        header.className = 'widget-header';

        const titleEl = document.createElement('div');
        titleEl.className = 'widget-title';
        titleEl.textContent = title;

        // We'll keep the close button but make it less visually prominent or remove it
        // Option 1: Keep but make less visible
        const closeBtn = document.createElement('div');
        closeBtn.style.display = 'none';

        // Option 2: Remove close button entirely
        // Uncomment the line below and comment out the closeBtn code above if you want to remove it completely
        // const closeBtn = document.createElement('div');

        header.appendChild(titleEl);
        header.appendChild(closeBtn);

        const contentEl = document.createElement('div');
        contentEl.className = `widget-content ${type}`;

        if (type === 'video') {
            const videoId = getYouTubeVideoId(content);
            if (videoId) {
                const iframe = document.createElement('iframe');
                iframe.src = `https://www.youtube.com/embed/${videoId}`;
                iframe.width = '100%';
                iframe.height = '100%';
                iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                iframe.allowFullscreen = true;
                contentEl.appendChild(iframe);
            } else {
                console.error("Invalid YouTube video ID:", content);
            }

        } else if (type === 'image') {
            const img = document.createElement('img');
            img.src = content;
            img.onload = () => this.autoSize();
            contentEl.appendChild(img);
        } else if (type === 'weather') {
            header.style.display = 'none'; // Hide the default widget header
            const data = content; // Python will send an object

            // Helper to map weather conditions from Python to an SVG icon
            function getWeatherIconSVG(condition) {
                const icons = {
                    'Clouds': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#94dfff" fill="none"><path d="M41.4 20.7A14.4 14.4 0 0 0 14.2 23a12.3 12.3 0 0 0-2.2 24.2h31.7a10.8 10.8 0 0 0 7.7-18.8 14.3 14.3 0 0 0-10-7.7z"/></svg>`,
                    'Rain': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#94dfff" fill="none"><path d="M41.4 20.7A14.4 14.4 0 0 0 14.2 23a12.3 12.3 0 0 0-2.2 24.2h31.7a10.8 10.8 0 0 0 7.7-18.8 14.3 14.3 0 0 0-10-7.7z"/><path d="M24.5 50v8M32.5 50v8M28.5 54v8" stroke-linecap="round" stroke-width="2"/></svg>`,
                    'Clear': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#ffe680" fill="none"><path d="M32 20.5a11.5 11.5 0 1 1-11.5 11.5A11.5 11.5 0 0 1 32 20.5m0-5v-6M45.9 18.1l4.2-4.2M52.5 32h6M45.9 45.9l4.2 4.2M32 52.5v6M18.1 45.9l-4.2 4.2M11.5 32h-6M18.1 18.1l-4.2-4.2" stroke-linecap="round"/></svg>`,
                    'Snow': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#fff" fill="none"><path d="M41.4 20.7A14.4 14.4 0 0 0 14.2 23a12.3 12.3 0 0 0-2.2 24.2h31.7a10.8 10.8 0 0 0 7.7-18.8 14.3 14.3 0 0 0-10-7.7z"/><path d="m24.5 50-3 3 3 3m3-6 3 3-3 3m5 0-3 3 3 3m3-6 3 3-3 3" stroke-linecap="round" stroke-width="2"/></svg>`,
                    'Drizzle': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#94dfff" fill="none"><path d="M41.4 20.7A14.4 14.4 0 0 0 14.2 23a12.3 12.3 0 0 0-2.2 24.2h31.7a10.8 10.8 0 0 0 7.7-18.8 14.3 14.3 0 0 0-10-7.7z"/><path d="M28.5 50v6M35.5 50v6" stroke-linecap="round" stroke-width="2"/></svg>`,
                    'Thunderstorm': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#ffeb3b" fill="none"><path d="M41.4 20.7A14.4 14.4 0 0 0 14.2 23a12.3 12.3 0 0 0-2.2 24.2h31.7a10.8 10.8 0 0 0 7.7-18.8 14.3 14.3 0 0 0-10-7.7z" stroke="#94dfff"/><path d="m30 48-4 7h12l-4 7" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
                    'default': `<svg viewBox="0 0 64 64" stroke-width="3" stroke="#94dfff" fill="none"><path d="M41.4 20.7A14.4 14.4 0 0 0 14.2 23a12.3 12.3 0 0 0-2.2 24.2h31.7a10.8 10.8 0 0 0 7.7-18.8 14.3 14.3 0 0 0-10-7.7z"/></svg>`
                };
                return icons[condition] || icons['default'];
            }

            // The entire widget's HTML structure is built here
            const weatherWidgetHTML = `
                <div class="weather-container">
                    <div class="weather-header-extra">
                        <svg class="weather-title-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg>
                        <div class="weather-title-text">${title}</div>
                        <svg class="weather-refresh-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-0.82 2.33-3.04 4-5.65 4c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14 .69 4.22 1.78L13 11h7V4l-2.65 2.35z"/></svg>
                    </div>
                    <div class="weather-main">
                        <div class="weather-temp-section">
                            <div class="weather-temperature">${data.temperature || 'N/A'}</div>
                            <div class="weather-location">${data.location || 'Unknown'}</div>
                            <div class="weather-description">${data.description || ''}</div>
                        </div>
                        <div class="weather-icon-section">
                            ${getWeatherIconSVG(data.main_condition)}
                        </div>
                    </div>
                    <div class="weather-details">
                        <div class="weather-detail-item">
                            <span class="detail-label">HUMIDITY</span>
                            <span class="detail-value">${data.humidity || 'N/A'}</span>
                        </div>
                        <div class="weather-detail-item">
                            <span class="detail-label">WIND</span>
                            <span class="detail-value">${data.wind || 'N/A'}</span>
                        </div>
                        <div class="weather-detail-item">
                            <span class="detail-label">FEELS LIKE</span>
                            <span class="detail-value">${data.feels_like || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            `;
            contentEl.innerHTML = weatherWidgetHTML;

            // Add click listener for the refresh icon
            const refreshIcon = contentEl.querySelector('.weather-refresh-icon');
            if (refreshIcon) {
                refreshIcon.onclick = () => {
                    console.log(`Refreshing weather for widget ${id}...`);
                    // Assumes a Python function `refresh_weather_data` exists.
                    if (typeof eel.refresh_weather_data === 'function') {
                        eel.refresh_weather_data(id);
                    }
                    refreshIcon.classList.add('rotating');
                    setTimeout(() => refreshIcon.classList.remove('rotating'), 1000);
                };
            }
        } else {
            contentEl.textContent = content;
        }

        const resizeHandle = document.createElement('div');
        resizeHandle.className = 'widget-resize';

        widget.appendChild(header);
        widget.appendChild(contentEl);
        widget.appendChild(resizeHandle);

        return widget;
    }

    // New method to handle right-click to close
    setupRightClickClose() {
        this.element.addEventListener('contextmenu', (e) => {
            e.preventDefault(); // Prevent default context menu
            this.close();
        });
    }

    autoSize() {
        const content = this.element.querySelector('.widget-content');
        const type = content.classList.contains('video') ? 'video' :
            content.classList.contains('image') ? 'image' :
            content.classList.contains('weather') ? 'weather' : 'text';

        if (type === 'video') {
            // Set default size for video widgets - reduced size as per request
            const width = Math.min(480, window.innerWidth * 0.8);
            const height = (width * 9) / 16; // 16:9 aspect ratio
            this.setSize(width + 30, height + 60);
        } else if (type === 'image') {
            const img = content.querySelector('img');
            if (img && img.naturalWidth && img.naturalHeight) {
                const ratio = img.naturalWidth / img.naturalHeight;
                let width = Math.min(img.naturalWidth, window.innerWidth * 0.8, 600); // Capped max width
                let height = width / ratio;

                if (height > window.innerHeight * 0.8) {
                    height = window.innerHeight * 0.8;
                    width = height * ratio;
                }
                this.setSize(width + 30, height + 60);
            }
        } else if (type === 'weather') {
            // Set a fixed, ideal size for the weather widget layout
            this.setSize(420, 230);
        } else { // Text widget
            const content = this.element.querySelector('.widget-content');
            const text = content.textContent;

            // Calculate font size based on text length
            const length = text.length;
            let fontSize;

            if (length > 200) {
                fontSize = '1.1em';
            } else if (length > 100) {
                fontSize = '1.6em';
            } else if (length > 50) {
                fontSize = '1.8em';
            } else {
                fontSize = '2em';
            }
            content.style.fontSize = fontSize;

            const calculator = document.createElement('div');
            calculator.className = 'size-calculator';
            calculator.textContent = content.textContent;
            calculator.style.fontSize = fontSize;
            document.body.appendChild(calculator);

            let width = Math.min(calculator.offsetWidth + 30, window.innerWidth * 0.9);
            let height = Math.min(calculator.offsetHeight + 70, window.innerHeight * 0.9);

            // Adjust width based on title length
            const titleElement = this.element.querySelector('.widget-title');
            const titleWidth = titleElement.scrollWidth;
            const headerPadding = parseInt(window.getComputedStyle(titleElement.parentElement).paddingLeft) * 2; // account for padding
            const headerWidth = this.element.querySelector('.widget-header').offsetWidth - headerPadding;


            if (titleWidth > headerWidth) {
                width = Math.max(width, titleWidth + 50); // Adjust padding as needed
            }


            document.body.removeChild(calculator);
            this.setSize(width, height);

        }
    }

    setPosition(x, y) {
        const maxX = window.innerWidth - this.element.offsetWidth;
        const maxY = window.innerHeight - this.element.offsetHeight;

        // Ensure widget stays within window bounds
        x = Math.max(0, Math.min(x, maxX));
        y = Math.max(0, Math.min(y, maxY));


        this.element.style.left = `${x}px`;
        this.element.style.top = `${y}px`;
    }

    setSize(width, height) {
        width = Math.max(200, Math.min(width, window.innerWidth * 0.9));
        height = Math.max(100, Math.min(height, window.innerHeight * 0.9));

        this.element.style.width = `${width}px`;
        this.element.style.height = `${height}px`;
    }

    setupDragging() {
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;

        const header = this.element.querySelector('.widget-header');
        // Allow dragging by the custom weather header as well
        const customHeader = this.element.querySelector('.weather-header-extra');
        const dragTarget = customHeader || header;


        const startDragging = (e) => {
            if (e.target.classList.contains('widget-close') ||
                e.target.classList.contains('widget-resize') ||
                e.target.classList.contains('weather-refresh-icon')) {
                return;
            }

            isDragging = true;
            this.element.classList.add('dragging');
            initialX = e.clientX - this.element.offsetLeft;
            initialY = e.clientY - this.element.offsetTop;
        };

        const drag = (e) => {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;

                // Call setPosition to handle boundary checks during drag
                this.setPosition(currentX, currentY);


            }
        };

        const stopDragging = () => {
            isDragging = false;
            this.element.classList.remove('dragging');
        };

        dragTarget.addEventListener('mousedown', startDragging);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', stopDragging);
    }

    setupResizing() {
        const resizeHandle = this.element.querySelector('.widget-resize');
        let isResizing = false;
        let initialWidth;
        let initialHeight;
        let initialX;
        let initialY;

        const startResizing = (e) => {
            isResizing = true;
            initialWidth = this.element.offsetWidth;
            initialHeight = this.element.offsetHeight;
            initialX = e.clientX;
            initialY = e.clientY;
        };

        const resize = (e) => {
            if (isResizing) {
                e.preventDefault();
                const width = initialWidth + (e.clientX - initialX);
                const height = initialHeight + (e.clientY - initialY);
                this.setSize(width, height);
            }
        };

        const stopResizing = () => {
            isResizing = false;
        };

        resizeHandle.addEventListener('mousedown', startResizing);
        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResizing);
    }

    close() {
        this.element.classList.remove('active');
        setTimeout(() => this.element.remove(), 300);
    }
}

// Handle the input field expansion
const textInputContainer = document.getElementById('text-input-container');
const textInput = document.getElementById('text-input');

textInputContainer.addEventListener('click', function() {
    if (!textInputContainer.classList.contains('active')) {
        textInputContainer.classList.add('active');
        textInput.focus();
    }
});

// Hide when focus is lost and input is empty, unless files are queued
textInput.addEventListener('blur', function() {
    if (textInput.value.trim() === '' && fileQueue.length === 0) {
        textInputContainer.classList.remove('active');
    }
});

function updateBottomLeftOutput(text) {
    const outputElement = document.getElementById('bottom-left-text');
    outputElement.textContent = text;
}

// ----- FILE HANDLING LOGIC -----

eel.expose(clearFrontendFileList);
function clearFrontendFileList() {
    console.log("Clearing frontend file list UI.");
    fileQueue = []; 
    updateFileListUI(); 
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

function setupSmoothDragDrop() {
  const wrapper = document.getElementById('chat-widget-wrapper');
  const container = document.getElementById('text-input-container');
  const dragOverlay = document.getElementById('drag-overlay');
  let dragCounter = 0;

  function showOverlay() {
    dragOverlay.classList.add('active');
    container.classList.add('dragover');
  }

  function hideOverlay() {
    dragOverlay.classList.remove('active');
    container.classList.remove('dragover');
  }

  wrapper.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
  });

  wrapper.addEventListener('dragenter', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter++;
    showOverlay();
  });

  wrapper.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter--;
    if (dragCounter === 0) hideOverlay();
  });

  wrapper.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter = 0;
    hideOverlay();

    const files = e.dataTransfer.files;
    if (files.length) {
      handleDroppedFiles(files);
    }
  });
}

// Replace old call with new function
window.addEventListener('DOMContentLoaded', () => {
  setupSmoothDragDrop();
});

async function handleDroppedFiles(files) {
    for (const file of files) {
        file.uniqueId = Date.now() + Math.random();
        fileQueue.push(file);
    }
    updateFileListUI();

    for (const file of files) {
        try {
            const base64Data = await fileToBase64(file);
            const fileData = { name: file.name, type: file.type, data: base64Data };
            console.log(`Pushing file to Python: ${file.name}`);
            eel.add_file_to_queue(fileData);
        } catch (error) {
            console.error(`Error processing file ${file.name}:`, error);
            removeFileFromLocalQueue(file.uniqueId);
        }
    }
}

function updateFileListUI() {
    const fileListContainer = document.getElementById('file-list-container');
    const textInputContainer = document.getElementById('text-input-container');
    fileListContainer.innerHTML = ''; 

    if (fileQueue.length > 0) {
        textInputContainer.classList.add('active');
        fileQueue.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const previewImg = document.createElement('img');
            previewImg.className = 'file-preview';
            if (file.type.startsWith('image/')) {
                if (!filePreviews.has(file.uniqueId)) {
                    filePreviews.set(file.uniqueId, URL.createObjectURL(file));
                }
                previewImg.src = filePreviews.get(file.uniqueId);
            }
            
            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';
            fileInfo.textContent = file.name;
            
            const removeBtn = document.createElement('span');
            removeBtn.className = 'file-remove-btn';
            removeBtn.innerHTML = '×';
            removeBtn.title = 'Remove file';
            removeBtn.onclick = () => { removeFileFromLocalQueue(file.uniqueId); };

            fileItem.appendChild(previewImg);
            fileItem.appendChild(fileInfo);
            fileItem.appendChild(removeBtn);
            fileListContainer.appendChild(fileItem);
        });
    } else {
        filePreviews.forEach(url => URL.revokeObjectURL(url));
        filePreviews.clear();
        if (document.activeElement !== textInput) {
             textInputContainer.classList.remove('active');
        }
    }
}

function removeFileFromLocalQueue(uniqueId) {
    const index = fileQueue.findIndex(f => f.uniqueId === uniqueId);
    if (index > -1) {
        const removedFile = fileQueue.splice(index, 1)[0];
        if(filePreviews.has(uniqueId)) {
            URL.revokeObjectURL(filePreviews.get(uniqueId));
            filePreviews.delete(uniqueId);
        }
        console.log(`Requesting Python to remove file: ${removedFile.name}`);
        eel.remove_file_from_queue(removedFile.name);
        updateFileListUI();
    }
}

function sendMessage(message) {
    const textInput = document.getElementById('text-input');
    const trimmedMessage = message.trim();

    if (!trimmedMessage && fileQueue.length === 0) { return; }

    console.log("Sending text prompt to Python: " + trimmedMessage);
    eel.process_text_input(trimmedMessage);
    
    // The backend will command the file list to clear when it processes the task.
    textInput.value = '';
    textInput.blur(); 
}