let currentSlide = 0;
let slides = [];
let totalSlides = 0;
let autoplayInterval = null;
let isAutoPlaying = false;
let backgroundAudio = null;
let isMuted = false;

// Upload functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('upload-box');
    const fileInput = document.getElementById('file-input');
    const uploadScreen = document.getElementById('upload-screen');
    const slidesScreen = document.getElementById('slides-screen');
    const processing = document.getElementById('processing');
    const errorMessage = document.getElementById('error-message');

    // File input change
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Prevent double-triggering when clicking the label
    const uploadLabel = uploadBox.querySelector('label[for="file-input"]');
    if (uploadLabel) {
        uploadLabel.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // Drag and drop
    uploadBox.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });

    uploadBox.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
    });

    uploadBox.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Click to upload (only if not clicking on the label)
    uploadBox.addEventListener('click', function(e) {
        // Don't trigger if clicking the label (it already handles the click)
        if (e.target.tagName !== 'LABEL') {
            fileInput.click();
        }
    });
});

function handleFile(file) {
    const uploadBox = document.getElementById('upload-box');
    const processing = document.getElementById('processing');
    const errorMessage = document.getElementById('error-message');

    // Show processing
    uploadBox.style.display = 'none';
    processing.style.display = 'block';
    errorMessage.style.display = 'none';

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Upload and process (with longer timeout for slide generation)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout
    
    fetch('/upload', {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Server error: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Store slides
        slides = data.slides;
        totalSlides = slides.length;
        
        // Setup audio if available
        if (data.audio_url) {
            setupBackgroundAudio(data.audio_url);
        }
        
        // Show slides screen
        showSlidesScreen();
    })
    .catch(error => {
        clearTimeout(timeoutId);
        // Show error
        processing.style.display = 'none';
        uploadBox.style.display = 'block';
        errorMessage.style.display = 'block';
        
        if (error.name === 'AbortError') {
            errorMessage.textContent = 'Request timed out. Your file may be too large or the server is busy. Please try again.';
        } else {
            errorMessage.textContent = `Error: ${error.message}. Please make sure you uploaded a valid Archive.org listening history export.`;
        }
    });
}

function showSlidesScreen() {
    const uploadScreen = document.getElementById('upload-screen');
    const slidesScreen = document.getElementById('slides-screen');
    const slideWrapper = document.getElementById('slide-wrapper');
    const progressDots = document.getElementById('progress-dots');

    // Create slide elements
    slideWrapper.innerHTML = '';
    progressDots.innerHTML = '';

    slides.forEach((slide, index) => {
        // Create slide
        const slideEl = document.createElement('div');
        slideEl.className = 'slide';
        if (index === 0) slideEl.classList.add('active');
        
        const img = document.createElement('img');
        img.src = `/slides/${slide}`;
        img.alt = `Slide ${index + 1}`;
        
        slideEl.appendChild(img);
        slideWrapper.appendChild(slideEl);

        // Create progress dot
        const dot = document.createElement('div');
        dot.className = 'dot';
        if (index === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToSlide(index));
        progressDots.appendChild(dot);
    });

    // Switch screens with animation
    uploadScreen.style.animation = 'fadeOut 0.5s ease-out';
    setTimeout(() => {
        uploadScreen.classList.remove('active');
        slidesScreen.classList.add('active');
        slidesScreen.style.animation = 'fadeInUp 0.8s ease-out';
    }, 500);

    // Setup navigation
    setupNavigation();
}

function setupNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const downloadBtn = document.getElementById('download-btn');
    const restartBtn = document.getElementById('restart-btn');
    const playPauseBtn = document.getElementById('play-pause-btn');

    prevBtn.addEventListener('click', prevSlide);
    nextBtn.addEventListener('click', nextSlide);
    downloadBtn.addEventListener('click', downloadCurrentSlide);
    restartBtn.addEventListener('click', restart);
    
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', toggleAutoplay);
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') prevSlide();
        if (e.key === 'ArrowRight') nextSlide();
    });

    // Touch swipe support
    let touchStartX = 0;
    let touchEndX = 0;
    
    const slideWrapper = document.getElementById('slide-wrapper');
    
    slideWrapper.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    slideWrapper.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        if (touchEndX < touchStartX - 50) nextSlide();
        if (touchEndX > touchStartX + 50) prevSlide();
    }

    updateNavButtons();
    
    // Start autoplay after 3 seconds
    setTimeout(startAutoplay, 3000);
}

function startAutoplay() {
    if (autoplayInterval) return;
    isAutoPlaying = true;
    updatePlayPauseButton();
    autoplayInterval = setInterval(() => {
        if (currentSlide < totalSlides - 1) {
            nextSlide();
        } else {
            stopAutoplay();
        }
    }, 6000); // 6 seconds per slide
}

function stopAutoplay() {
    if (autoplayInterval) {
        clearInterval(autoplayInterval);
        autoplayInterval = null;
        isAutoPlaying = false;
        updatePlayPauseButton();
    }
}

function toggleAutoplay() {
    if (isAutoPlaying) {
        stopAutoplay();
    } else {
        startAutoplay();
    }
}

function updatePlayPauseButton() {
    const icon = document.getElementById('play-pause-icon');
    if (icon) {
        icon.textContent = isAutoPlaying ? '\u23f8' : '\u25b6';
    }
}

function goToSlide(index) {
    if (index < 0 || index >= totalSlides) return;
    
    stopAutoplay(); // Stop autoplay when user navigates

    const slideEls = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot');

    // Update slides
    slideEls[currentSlide].classList.remove('active');
    slideEls[currentSlide].classList.add('prev');
    slideEls[index].classList.remove('prev');
    slideEls[index].classList.add('active');

    // Update dots
    dots[currentSlide].classList.remove('active');
    dots[index].classList.add('active');

    currentSlide = index;
    updateNavButtons();
}

function prevSlide() {
    if (currentSlide > 0) {
        goToSlide(currentSlide - 1);
    }
}

function nextSlide() {
    if (currentSlide < totalSlides - 1) {
        goToSlide(currentSlide + 1);
    }
}

function updateNavButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    prevBtn.disabled = currentSlide === 0;
    nextBtn.disabled = currentSlide === totalSlides - 1;
}

function downloadCurrentSlide() {
    const currentSlideImg = slides[currentSlide];
    const link = document.createElement('a');
    link.href = `/slides/${currentSlideImg}`;
    link.download = currentSlideImg;
    link.click();
}

function restart() {
    const uploadScreen = document.getElementById('upload-screen');
    const slidesScreen = document.getElementById('slides-screen');
    const uploadBox = document.getElementById('upload-box');
    const processing = document.getElementById('processing');
    const errorMessage = document.getElementById('error-message');

    // Reset upload screen
    uploadBox.style.display = 'block';
    processing.style.display = 'none';
    errorMessage.style.display = 'none';

    // Switch screens
    slidesScreen.classList.remove('active');
    uploadScreen.classList.add('active');

    // Reset state
    currentSlide = 0;
    slides = [];
    totalSlides = 0;
    
    // Stop and remove audio
    if (backgroundAudio) {
        backgroundAudio.pause();
        backgroundAudio = null;
    }
    const muteBtn = document.getElementById('mute-btn');
    if (muteBtn) {
        muteBtn.style.display = 'none';
    }
}

function setupBackgroundAudio(audioUrl) {
    backgroundAudio = document.getElementById('background-audio');
    const muteBtn = document.getElementById('mute-btn');
    const muteIcon = document.getElementById('mute-icon');
    
    if (backgroundAudio && audioUrl) {
        backgroundAudio.src = audioUrl;
        backgroundAudio.volume = 0.3;
        backgroundAudio.loop = true;
        
        // Show mute button
        muteBtn.style.display = 'flex';
        
        // Try to play (browsers may require user interaction)
        backgroundAudio.play().catch(err => {
            console.log('Audio autoplay prevented:', err);
        });
        
        // Setup mute button
        muteBtn.addEventListener('click', function() {
            isMuted = !isMuted;
            backgroundAudio.muted = isMuted;
            muteIcon.textContent = isMuted ? '🔇' : '🔊';
            muteBtn.classList.toggle('muted', isMuted);
        });
    }
}

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: scale(1);
        }
        to {
            opacity: 0;
            transform: scale(0.95);
        }
    }
`;
document.head.appendChild(style);
