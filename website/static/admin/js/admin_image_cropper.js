document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("id_image_file");
    
    if (!input) return;

    let cropper;
    let modal, image, cropBtn, closeBtn, previewCanvas, skipBtn;
    let originalFile = null;
    let currentAspectRatio = NaN;
    let isProcessing = false;

    // File size constants
    const MAX_FILE_SIZE_MB = 5;
    const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

    // Utility functions for file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function validateFileSize(file) {
        const fileSize = file.size;
        const fileSizeMB = fileSize / (1024 * 1024);
        
        if (fileSize > MAX_FILE_SIZE_BYTES) {
            return {
                valid: false,
                message: `File size is ${formatFileSize(fileSize)} (${fileSizeMB.toFixed(2)}MB). Maximum allowed size is ${MAX_FILE_SIZE_MB}MB.`,
                size: formatFileSize(fileSize)
            };
        }
        
        return {
            valid: true,
            message: `File size: ${formatFileSize(fileSize)} - OK`,
            size: formatFileSize(fileSize)
        };
    }

    function showFileSizeError(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            left: 20px;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3);
            z-index: 10001;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 600;
            max-width: calc(100vw - 40px);
            backdrop-filter: blur(10px);
        `;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 20px;">⚠️</span>
                <div>
                    <div style="font-weight: 700; margin-bottom: 4px;">File Too Large</div>
                    <div style="font-weight: 400; opacity: 0.9;">${message}</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        notification.addEventListener('click', () => {
            notification.remove();
        });
    }

    function showFileSizeSuccess(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            left: 20px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);
            z-index: 10001;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            font-weight: 600;
            backdrop-filter: blur(10px);
            max-width: calc(100vw - 40px);
        `;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px;">✅</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Create Image Editor modal
    modal = document.createElement("div");
    modal.className = "image-editor-modal";
    modal.innerHTML = `
        <div class="editor-backdrop"></div>
        <div class="editor-container">
            <div class="editor-header">
                <h3>🎨 Image Editor</h3>
                <div class="editor-status">
                    <span class="status-indicator" id="file-size-indicator">✨ Ready to Edit</span>
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
                        <h4>File Info</h4>
                        <div class="file-info-panel">
                            <div class="info-item">
                                <span class="info-label">Size:</span>
                                <span class="info-value" id="current-file-size">-</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Type:</span>
                                <span class="info-value" id="current-file-type">-</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Dimensions:</span>
                                <span class="info-value" id="current-dimensions">-</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="controls-section">
                        <h4>Crop Aspect Ratios</h4>
                        <div class="aspect-ratio-buttons">
                            <button type="button" class="aspect-btn active" data-ratio="free">Free Crop</button>
                            <button type="button" class="aspect-btn" data-ratio="1">Square (1:1)</button>
                            <button type="button" class="aspect-btn" data-ratio="1.333">4:3</button>
                            <button type="button" class="aspect-btn" data-ratio="1.777">16:9</button>
                            <button type="button" class="aspect-btn" data-ratio="2">Banner (2:1)</button>
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
                <div class="footer-buttons">
                    <button type="button" id="cancel-edit" class="btn-secondary">Cancel</button>
                    <button type="button" id="apply-edit" class="btn-primary">Apply Changes</button>
                </div>
            </div>
        </div>
    `;

    // Enhanced mobile-responsive styles
    const styles = `
        <style>
        .file-info-panel {
            background: #f1f5f9;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        }
        
        .info-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .info-item:last-child {
            margin-bottom: 0;
        }
        
        .info-label {
            font-weight: 600;
            color: #64748b;
            font-size: 12px;
        }
        
        .info-value {
            font-weight: 700;
            color: #1e293b;
            font-size: 12px;
        }
        
        .status-indicator.size-ok {
            background: rgba(16, 185, 129, 0.2);
            color: #059669;
        }
        
        .status-indicator.size-warning {
            background: rgba(245, 158, 11, 0.2);
            color: #d97706;
        }
        
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
            flex-shrink: 0;
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
            touch-action: manipulation;
        }
        
        .close-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .editor-content {
            display: flex;
            flex: 1;
            min-height: 0;
            overflow: hidden;
        }
        
        .editor-main {
            flex: 2;
            padding: 28px;
            min-width: 0;
            background: #f8fafc;
            overflow: auto;
        }
        
        .image-wrapper {
            height: 60vh;
            max-height: 500px;
            overflow: hidden;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            touch-action: manipulation;
        }
        
        .image-wrapper img {
            display: block;
            max-width: 100%;
            height: auto;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }
        
        .editor-sidebar {
            flex: 1;
            min-width: 320px;
            max-width: 380px;
            padding: 28px;
            background: #ffffff;
            border-left: 1px solid #e2e8f0;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
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
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .aspect-btn {
            padding: 12px 14px;
            border: 2px solid #e2e8f0;
            background: #ffffff;
            color: #475569;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            touch-action: manipulation;
            min-height: 44px;
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
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            font-size: 16px;
            background: #ffffff !important;
            color: #475569 !important;
            transition: border-color 0.2s;
            min-height: 44px;
            box-sizing: border-box;
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
            padding: 12px;
            border: 2px solid #e2e8f0;
            background: #ffffff;
            color: #475569;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            touch-action: manipulation;
            min-height: 44px;
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
            flex-shrink: 0;
        }
        
        .footer-buttons {
            display: flex;
            gap: 12px;
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
            touch-action: manipulation;
            min-height: 44px;
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
            touch-action: manipulation;
            min-height: 44px;
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
            touch-action: manipulation;
            min-height: 44px;
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
        
        /* Mobile Responsive Styles */
        @media (max-width: 1024px) {
            .editor-container {
                margin: 1vh auto;
                max-height: 98vh;
                border-radius: 12px;
            }
            
            .editor-header {
                padding: 16px 20px;
            }
            
            .editor-header h3 {
                font-size: 18px;
            }
            
            .status-indicator {
                display: none;
            }
            
            .editor-content {
                flex-direction: column;
            }
            
            .editor-main {
                flex: none;
                padding: 20px;
                order: 1;
            }
            
            .image-wrapper {
                height: 50vh;
                max-height: 400px;
                min-height: 300px;
            }
            
            .editor-sidebar {
                flex: none;
                min-width: auto;
                max-width: none;
                border-left: none;
                border-top: 1px solid #e2e8f0;
                padding: 20px;
                order: 2;
                max-height: 40vh;
                overflow-y: auto;
            }
            
            .controls-section {
                margin-bottom: 20px;
            }
            
            .aspect-ratio-buttons {
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .aspect-btn {
                padding: 10px 8px;
                font-size: 11px;
                min-height: 44px;
            }
            
            .tool-buttons {
                grid-template-columns: repeat(4, 1fr);
                gap: 8px;
            }
            
            .btn-tool {
                padding: 10px 8px;
                font-size: 11px;
                min-height: 44px;
            }
            
            .preview-container {
                height: 120px;
            }
            
            .editor-footer {
                padding: 16px 20px;
                flex-direction: column;
                gap: 12px;
            }
            
            .footer-buttons {
                width: 100%;
                justify-content: space-between;
            }
            
            .btn-skip {
                width: 100%;
                margin-bottom: 8px;
                padding: 14px 20px;
                font-size: 16px;
            }
            
            .btn-primary, .btn-secondary {
                flex: 1;
                padding: 14px 20px;
                font-size: 16px;
            }
        }
        
        @media (max-width: 640px) {
            .editor-container {
                margin: 0;
                max-width: 100vw;
                max-height: 100vh;
                border-radius: 0;
            }
            
            .editor-header {
                padding: 12px 16px;
            }
            
            .editor-header h3 {
                font-size: 16px;
            }
            
            .close-btn {
                width: 32px;
                height: 32px;
                font-size: 20px;
            }
            
            .editor-main {
                padding: 16px;
            }
            
            .image-wrapper {
                height: 45vh;
                max-height: 350px;
                min-height: 250px;
            }
            
            .editor-sidebar {
                padding: 16px;
                max-height: 35vh;
            }
            
            .aspect-ratio-buttons {
                grid-template-columns: 1fr;
                gap: 6px;
            }
            
            .aspect-btn {
                padding: 12px 16px;
                font-size: 12px;
                text-align: center;
            }
            
            .tool-buttons {
                grid-template-columns: repeat(3, 1fr);
                gap: 6px;
            }
            
            .btn-tool {
                padding: 12px 8px;
                font-size: 10px;
            }
            
            .custom-size-inputs {
                gap: 8px;
            }
            
            .input-group {
                flex-direction: column;
                align-items: stretch;
                gap: 4px;
            }
            
            .input-group label {
                min-width: auto;
                font-size: 12px;
            }
            
            .input-group input {
                font-size: 16px;
                padding: 12px;
            }
            
            .preview-container {
                height: 100px;
            }
            
            .editor-footer {
                padding: 12px 16px;
                gap: 8px;
            }
            
            .btn-skip {
                padding: 12px 16px;
                font-size: 14px;
                margin-bottom: 6px;
            }
            
            .btn-primary, .btn-secondary {
                padding: 12px 16px;
                font-size: 14px;
            }
            
            .file-info-panel {
                padding: 12px;
                margin-bottom: 16px;
            }
            
            .controls-section h4 {
                font-size: 12px;
                margin-bottom: 12px;
            }
        }
        
        /* Landscape orientation on mobile */
        @media (max-width: 896px) and (orientation: landscape) {
            .editor-content {
                flex-direction: row;
            }
            
            .editor-main {
                flex: 2;
                order: 1;
                padding: 16px;
            }
            
            .image-wrapper {
                height: calc(100vh - 200px);
                max-height: none;
                min-height: 200px;
            }
            
            .editor-sidebar {
                flex: 1;
                min-width: 280px;
                max-width: 320px;
                border-left: 1px solid #e2e8f0;
                border-top: none;
                order: 2;
                max-height: none;
                padding: 16px;
            }
            
            .aspect-ratio-buttons {
                grid-template-columns: 1fr 1fr;
            }
            
            .tool-buttons {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        /* Touch improvements */
        @media (hover: none) and (pointer: coarse) {
            .aspect-btn:hover,
            .btn-tool:hover,
            .btn-primary:hover,
            .btn-secondary:hover,
            .btn-skip:hover,
            .close-btn:hover {
                transform: none;
                box-shadow: none;
            }
            
            .aspect-btn:active,
            .btn-tool:active,
            .btn-primary:active,
            .btn-secondary:active,
            .btn-skip:active,
            .close-btn:active {
                transform: scale(0.98);
            }
            
            /* Improve touch targets */
            .aspect-btn,
            .btn-tool,
            .btn-primary,
            .btn-secondary,
            .btn-skip,
            .close-btn {
                min-height: 48px;
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

    // File info elements
    const fileSizeIndicator = modal.querySelector('#file-size-indicator');
    const currentFileSize = modal.querySelector('#current-file-size');
    const currentFileType = modal.querySelector('#current-file-type');
    const currentDimensions = modal.querySelector('#current-dimensions');

    function updateFileInfo(file) {
        const validation = validateFileSize(file);
        
        currentFileSize.textContent = validation.size;
        currentFileType.textContent = file.type.split('/')[1].toUpperCase();
        
        fileSizeIndicator.textContent = validation.valid ? 
            `✅ ${validation.size}` : 
            `⚠️ ${validation.size}`;
        
        if (validation.valid) {
            fileSizeIndicator.className = 'status-indicator size-ok';
        } else {
            fileSizeIndicator.className = 'status-indicator size-warning';
        }
        
        const img = new Image();
        img.onload = function() {
            currentDimensions.textContent = `${this.width} × ${this.height}px`;
        };
        img.src = URL.createObjectURL(file);
    }

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

    // ENHANCED File change handler with size validation
    function handleFileChange(e) {
        if (isProcessing) return;
        
        const file = e.target.files[0];
        if (!file) return;

        // Validate file size FIRST
        const validation = validateFileSize(file);
        
        if (!validation.valid) {
            e.target.value = '';
            showFileSizeError(validation.message);
            return;
        }
        
        showFileSizeSuccess(validation.message);
        
        if (file !== originalFile) {
            originalFile = file;
            
            const reader = new FileReader();
            reader.onload = function(evt) {
                image.src = evt.target.result;
                modal.style.display = 'block';
                
                updateFileInfo(file);
                
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