document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("id_image_file");
    
    if (!input) return;

    let cropper;
    let modal, image, cropBtn, closeBtn, previewCanvas, skipBtn;
    let originalFile = null;
    let currentAspectRatio = NaN;
    let isProcessing = false;

    // Create Image Editor modal
    modal = document.createElement("div");
    modal.className = "image-editor-modal";
    modal.innerHTML = `
        <div class="editor-backdrop"></div>
        <div class="editor-container">
            <div class="editor-header">
                <h3>🎨 Image Editor</h3>
                <div class="editor-status">
                    <span class="status-indicator">✨ Ready to Edit</span>
                </div>
                <button type="button" class="close-btn" title="Close Editor">&times;</button>
            </div>
            
            <div class="editor-content">
                <div class="editor-main">
                    <div class="image-wrapper">
                        <img id="editor-image" alt="Image to edit">
                    </div>
                </div>
                
                <div class="editor-sidebar">
                    <div class="controls-section">
                        <h4>Crop Aspect Ratios</h4>
                        <div class="aspect-ratio-buttons">
                            <button type="button" class="aspect-btn active" data-ratio="free">Free Crop</button>
                            <button type="button" class="aspect-btn" data-ratio="1">Square (1:1)</button>
                            <button type="button" class="aspect-btn" data-ratio="1.333">4:3</button>
                            <button type="button" class="aspect-btn" data-ratio="1.777">16:9</button>
                            <button type="button" class="aspect-btn" data-ratio="0.75">3:4 (Portrait)</button>
                        </div>
                        
                        <h4>Custom Dimensions</h4>
                        <div class="custom-size-inputs">
                            <div class="input-group">
                                <label>Width:</label>
                                <input type="number" id="custom-width" placeholder="1200" min="100" max="4000">
                            </div>
                            <div class="input-group">
                                <label>Height:</label>
                                <input type="number" id="custom-height" placeholder="1200" min="100" max="4000">
                            </div>
                            <button type="button" id="apply-custom-ratio" class="btn-secondary">Apply Custom</button>
                        </div>
                    </div>
                    
                    <div class="controls-section">
                        <h4>Edit Tools</h4>
                        <div class="tool-buttons">
                            <button type="button" id="zoom-in-btn" class="btn-tool" title="Zoom In">🔍+</button>
                            <button type="button" id="zoom-out-btn" class="btn-tool" title="Zoom Out">🔍-</button>
                            <button type="button" id="rotate-left-btn" class="btn-tool" title="Rotate Left">↶</button>
                            <button type="button" id="rotate-right-btn" class="btn-tool" title="Rotate Right">↷</button>
                            <button type="button" id="flip-h-btn" class="btn-tool" title="Flip Horizontal">⇄</button>
                            <button type="button" id="flip-v-btn" class="btn-tool" title="Flip Vertical">⇅</button>
                            <button type="button" id="reset-btn" class="btn-tool">Reset</button>
                        </div>
                    </div>
                    
                    <div class="controls-section">
                        <h4>Preview</h4>
                        <div class="preview-container">
                            <canvas id="preview-canvas"></canvas>
                        </div>
                        <div class="preview-info">
                            <span id="preview-dimensions">0 × 0</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="editor-footer">
                <button type="button" id="skip-editing" class="btn-skip">
                    📷 Use Original Image
                </button>
                <button type="button" id="cancel-edit" class="btn-secondary">Cancel</button>
                <button type="button" id="apply-edit" class="btn-primary">Apply Changes</button>
            </div>
        </div>
    `;

    // Updated styles with Image Editor theme
    const styles = `
        <style>
        .image-editor-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10000;
            display: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .editor-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(4px);
        }
        
        .editor-container {
            position: relative;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
            margin: 2vh auto;
            max-width: 95vw;
            max-height: 95vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }
        
        .editor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 28px;
            border-bottom: 1px solid #e2e8f0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .editor-header h3 {
            margin: 0;
            font-size: 20px;
            font-weight: 700;
            color: white;
        }
        
        .status-indicator {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 6px 14px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .close-btn {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: white;
            padding: 0;
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        .close-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .editor-content {
            display: flex;
            flex: 1;
            min-height: 0;
        }
        
        .editor-main {
            flex: 2;
            padding: 28px;
            min-width: 0;
            background: #f8fafc;
        }
        
        .image-wrapper {
            height: 60vh;
            max-height: 500px;
            overflow: hidden;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }
        
        .image-wrapper img {
            display: block;
            max-width: 100%;
            height: auto;
        }
        
        .editor-sidebar {
            flex: 1;
            min-width: 320px;
            max-width: 380px;
            padding: 28px;
            background: #ffffff;
            border-left: 1px solid #e2e8f0;
            overflow-y: auto;
        }
        
        .controls-section {
            margin-bottom: 28px;
        }
        
        .controls-section h4 {
            margin: 0 0 16px 0;
            font-size: 14px;
            font-weight: 700;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        
        .aspect-ratio-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .aspect-btn {
            padding: 10px 14px;
            border: 2px solid #e2e8f0;
            background: #ffffff;
            color: #475569;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .aspect-btn:hover {
            border-color: #cbd5e1;
            background: #f1f5f9;
            transform: translateY(-1px);
        }
        
        .aspect-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .custom-size-inputs {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .input-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .input-group label {
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            min-width: 50px;
        }
        
        .input-group input {
            flex: 1;
            padding: 8px 12px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            font-size: 13px;
            background: #ffffff !important;
            color: #475569 !important;
            transition: border-color 0.2s;
        }
        
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .tool-buttons {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        
        .btn-tool {
            padding: 10px;
            border: 2px solid #e2e8f0;
            background: #ffffff;
            color: #475569;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .btn-tool:hover {
            border-color: #cbd5e1;
            background: #f1f5f9;
            transform: translateY(-1px);
        }
        
        .btn-tool:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .preview-container {
            width: 100%;
            height: 160px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8fafc;
            margin-bottom: 12px;
        }
        
        #preview-canvas {
            max-width: 100%;
            max-height: 100%;
            border-radius: 6px;
        }
        
        .preview-info {
            text-align: center;
            font-size: 12px;
            color: #64748b;
            font-weight: 600;
        }
        
        .editor-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 20px 28px;
            border-top: 1px solid #e2e8f0;
            background: #f8fafc;
        }
        
        .btn-skip {
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }
        
        .btn-skip:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .btn-primary:disabled {
            background: #94a3b8;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #ffffff;
            color: #475569;
            border: 2px solid #e2e8f0;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }
        
        .btn-secondary:hover {
            background: #f1f5f9;
            border-color: #cbd5e1;
            transform: translateY(-1px);
        }
        
        .processing {
            opacity: 0.7;
            pointer-events: none;
        }
        
        @media (max-width: 768px) {
            .editor-container {
                margin: 1vh auto;
                max-height: 98vh;
            }
            
            .editor-content {
                flex-direction: column;
            }
            
            .editor-sidebar {
                min-width: auto;
                max-width: none;
                border-left: none;
                border-top: 1px solid #e2e8f0;
            }
            
            .image-wrapper {
                height: 40vh;
            }
            
            .editor-footer {
                flex-direction: column;
                gap: 12px;
            }
            
            .editor-footer > div {
                display: flex;
                gap: 12px;
                width: 100%;
            }
        }
        </style>
    `;

    document.head.insertAdjacentHTML('beforeend', styles);
    document.body.appendChild(modal);

    // Get elements
    image = modal.querySelector('#editor-image');
    cropBtn = modal.querySelector('#apply-edit');
    closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('#cancel-edit');
    skipBtn = modal.querySelector('#skip-editing');
    previewCanvas = modal.querySelector('#preview-canvas');
    const previewDimensions = modal.querySelector('#preview-dimensions');

    // Event listeners
    closeBtn.addEventListener('click', closeEditor);
    cancelBtn.addEventListener('click', closeEditor);
    modal.querySelector('.editor-backdrop').addEventListener('click', function(e) {
        if (!isProcessing) {
            closeEditor();
        }
    });

    // Skip editing - use original image
    skipBtn.addEventListener('click', function() {
        if (isProcessing || !originalFile) return;
        
        console.log('Skipping editing, using original image');
        
        // Clear input and set original file
        input.value = '';
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(originalFile);
        input.files = dataTransfer.files;
        
        closeEditor();
    });

    // Aspect ratio buttons
    modal.querySelectorAll('.aspect-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (isProcessing) return;
            
            modal.querySelectorAll('.aspect-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            const ratio = this.dataset.ratio;
            if (ratio === 'free') {
                currentAspectRatio = NaN;
            } else {
                currentAspectRatio = parseFloat(ratio);
            }
            
            if (cropper) {
                cropper.setAspectRatio(currentAspectRatio);
            }
        });
    });

    // Custom aspect ratio
    modal.querySelector('#apply-custom-ratio').addEventListener('click', function() {
        if (isProcessing) return;
        
        const width = parseInt(modal.querySelector('#custom-width').value);
        const height = parseInt(modal.querySelector('#custom-height').value);
        
        if (width && height && width > 0 && height > 0) {
            currentAspectRatio = width / height;
            modal.querySelectorAll('.aspect-btn').forEach(b => b.classList.remove('active'));
            
            if (cropper) {
                cropper.setAspectRatio(currentAspectRatio);
            }
        }
    });

    // Tool buttons
    modal.querySelector('#zoom-in-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) cropper.zoom(0.1);
    });
    modal.querySelector('#zoom-out-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) cropper.zoom(-0.1);
    });
    modal.querySelector('#rotate-left-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) cropper.rotate(-90);
    });
    modal.querySelector('#rotate-right-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) cropper.rotate(90);
    });
    modal.querySelector('#flip-h-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) {
            const data = cropper.getData();
            cropper.scaleX(data.scaleX === 1 ? -1 : 1);
        }
    });
    modal.querySelector('#flip-v-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) {
            const data = cropper.getData();
            cropper.scaleY(data.scaleY === 1 ? -1 : 1);
        }
    });
    modal.querySelector('#reset-btn').addEventListener('click', () => {
        if (!isProcessing && cropper) cropper.reset();
    });

    // Functions
    function closeEditor() {
        if (isProcessing) return;
        
        modal.style.display = 'none';
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        isProcessing = false;
        originalFile = null;
        
        cropBtn.textContent = 'Apply Changes';
        cropBtn.disabled = false;
    }

    function setProcessingState(processing) {
        isProcessing = processing;
        const buttons = modal.querySelectorAll('button');
        
        if (processing) {
            buttons.forEach(btn => btn.disabled = true);
            cropBtn.textContent = 'Processing...';
        } else {
            buttons.forEach(btn => btn.disabled = false);
            cropBtn.textContent = 'Apply Changes';
        }
    }

    function updatePreview() {
        if (!cropper) return;
        
        try {
            const canvas = cropper.getCroppedCanvas({
                width: 200,
                height: 200,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });
            
            if (canvas) {
                const ctx = previewCanvas.getContext('2d');
                const containerWidth = previewCanvas.parentElement.clientWidth - 24;
                const containerHeight = previewCanvas.parentElement.clientHeight - 24;
                
                const scale = Math.min(containerWidth / canvas.width, containerHeight / canvas.height, 1);
                const scaledWidth = canvas.width * scale;
                const scaledHeight = canvas.height * scale;
                
                previewCanvas.width = scaledWidth;
                previewCanvas.height = scaledHeight;
                
                ctx.clearRect(0, 0, scaledWidth, scaledHeight);
                ctx.drawImage(canvas, 0, 0, scaledWidth, scaledHeight);
                
                const cropData = cropper.getCropBoxData();
                previewDimensions.textContent = `${Math.round(cropData.width)} × ${Math.round(cropData.height)}`;
            }
        } catch (error) {
            console.warn('Preview update failed:', error);
        }
    }

    let previewTimeout;
    function debouncedPreviewUpdate() {
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(updatePreview, 150);
    }

    // File change handler - Always open Image Editor
    function handleFileChange(e) {
        if (isProcessing) return;
        
        const file = e.target.files[0];
        if (file && file !== originalFile) {
            originalFile = file;
            
            const reader = new FileReader();
            reader.onload = function(evt) {
                image.src = evt.target.result;
                modal.style.display = 'block';
                
                if (cropper) {
                    cropper.destroy();
                }
                
                cropper = new Cropper(image, {
                    viewMode: 1,
                    responsive: true,
                    restore: false,
                    guides: true,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                    aspectRatio: currentAspectRatio,
                    autoCropArea: 1.0,
                    ready: function() {
                        updatePreview();
                    },
                    cropstart: debouncedPreviewUpdate,
                    cropmove: debouncedPreviewUpdate,
                    cropend: debouncedPreviewUpdate,
                    zoom: debouncedPreviewUpdate
                });
            };
            reader.readAsDataURL(file);
        }
    }

    input.addEventListener('change', handleFileChange);

    // Apply changes function
    cropBtn.addEventListener('click', function() {
        if (!cropper || isProcessing) return;
        
        console.log('Applying image changes...'); 
        setProcessingState(true);
        
        const timeout = setTimeout(() => {
            console.error('Edit operation timed out');
            setProcessingState(false);
            alert('Edit operation timed out. Please try again.');
        }, 10000);
        
        try {
            const imageData = cropper.getImageData();
            const cropBoxData = cropper.getCropBoxData();
            const canvasData = cropper.getCanvasData();
            
            const scaleX = imageData.naturalWidth / canvasData.width;
            const scaleY = imageData.naturalHeight / canvasData.height;
            
            const canvas = cropper.getCroppedCanvas({
                width: Math.round((cropBoxData.width - canvasData.left) * scaleX),
                height: Math.round((cropBoxData.height - canvasData.top) * scaleY),
                imageSmoothingEnabled: false,
                imageSmoothingQuality: 'high'
            });
            
            if (!canvas) {
                clearTimeout(timeout);
                setProcessingState(false);
                alert('Failed to process image. Please try again.');
                return;
            }
            
            console.log('Canvas created with dimensions:', canvas.width, 'x', canvas.height); 
            
            const blobPromise = new Promise((resolve, reject) => {
                let outputType = originalFile.type;
                let quality = 1.0;
                
                if (outputType === 'image/jpeg' || outputType === 'image/jpg') {
                    quality = 1.0;
                } else if (outputType === 'image/webp') {
                    quality = 1.0;
                }
                
                canvas.toBlob(function(blob) {
                    if (blob) {
                        resolve(blob);
                    } else {
                        reject(new Error('Failed to create blob'));
                    }
                }, outputType, quality);
            });
            
            blobPromise.then(function(blob) {
                clearTimeout(timeout);
                console.log('High-quality blob created:', blob.size, 'bytes'); 
                
                const file = new File([blob], originalFile.name, { 
                    type: blob.type,
                    lastModified: Date.now()
                });
                
                input.value = '';
                
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                input.files = dataTransfer.files;
                
                console.log('Edited file set in input, closing editor...'); 
                
                setProcessingState(false);
                closeEditor();
                
            }).catch(function(error) {
                clearTimeout(timeout);
                console.error('Blob creation failed:', error);
                setProcessingState(false);
                alert('Failed to process edited image. Please try again.');
            });
            
        } catch (error) {
            clearTimeout(timeout);
            console.error('Edit failed:', error);
            setProcessingState(false);
            alert('Failed to edit image. Please try again.');
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (modal.style.display !== 'block' || isProcessing) return;
        
        switch(e.key) {
            case 'Escape':
                closeEditor();
                break;
            case 'Enter':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    cropBtn.click();
                }
                break;
            case 's':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    skipBtn.click();
                }
                break;
            case '=':
            case '+':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    cropper && cropper.zoom(0.1);
                }
                break;
            case '-':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    cropper && cropper.zoom(-0.1);
                }
                break;
        }
    });
});