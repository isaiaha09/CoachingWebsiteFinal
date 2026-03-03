var slideIndex = 0;
var autoSlideInterval;
var slides = document.getElementsByClassName("mySlides");
var resetTimeout; // <-- new: controls when to reset back to slide 1

document.addEventListener("DOMContentLoaded", function() {
    showSlides(slideIndex);
    startAutoSlide();
});

function plusSlides(n) {
    clearInterval(autoSlideInterval); 
    if (slideIndex === slides.length - 1 && n > 0) {
        slideIndex = 0; 
    } else {
        slideIndex += n;
    }
    showSlides(slideIndex);

    if (slideIndex < slides.length - 1) {
        startAutoSlide();
    }
}

function currentSlide(n) {
    clearInterval(autoSlideInterval);
    slideIndex = n - 1;
    showSlides(slideIndex);

    if (slideIndex < slides.length - 1) {
        startAutoSlide();
    }
}

function showSlides() {
    var i;
    var dots = document.getElementsByClassName("dot");

    if (slideIndex >= slides.length) {
        slideIndex = slides.length - 1;
    }
    if (slideIndex < 0) {
        slideIndex = 0;
    }

    // Hide all slides
    for (i = 0; i < slides.length; i++) {
        slides[i].style.opacity = "0";
        slides[i].style.transition = "opacity 1.5s ease-in-out";
        slides[i].style.position = "absolute";
        slides[i].style.width = "100%";

        let video = slides[i].querySelector("video");
        if (video) {
            video.pause();
            video.currentTime = 0;
            video.onended = null;
            video.onplay = null;
            video.onpause = null;
        }
    }

    // Clear any previous reset timers
    clearTimeout(resetTimeout);

    // Remove "active" class from dots
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }

    // Show current slide
    slides[slideIndex].style.opacity = "1";
    slides[slideIndex].style.position = "relative";

    let activeVideo = slides[slideIndex].querySelector("video");
    if (activeVideo) {
        // RULE 1: If no one plays → reset after 10s
        resetTimeout = setTimeout(goToFirstSlide, 10000);

        // RULE 2: If they finish video → reset after 10s
        activeVideo.onended = function() {
            clearTimeout(resetTimeout);
            resetTimeout = setTimeout(goToFirstSlide, 10000);
        };

        // RULE 3: If they pause/stop before finishing → reset after 10s
        activeVideo.onpause = function() {
            clearTimeout(resetTimeout);
            resetTimeout = setTimeout(goToFirstSlide, 10000);
        };

        // While video is playing → do not auto advance
        activeVideo.onplay = function() {
            clearTimeout(resetTimeout);
        };
    }

    if (dots[slideIndex]) {
        dots[slideIndex].className += " active";
    }
}

function goToFirstSlide() {
    slideIndex = 0;
    showSlides(slideIndex);
    startAutoSlide();
}

// Auto slide (stops before video)
function startAutoSlide() {
    autoSlideInterval = setInterval(function() {
        if (slideIndex < slides.length - 1) {
            plusSlides(1);
        }
    }, 4000);
}


document.addEventListener("DOMContentLoaded", () => {
    const words = [
        document.querySelector(".top-left"),
        document.querySelector(".top-right"),
        document.querySelector(".bottom-left"),
        document.querySelector(".bottom-right")
    ];

    let index = 0;

    function popNextWord() {
        // Hide all words first
        words.forEach(w => w.classList.remove("show"));

        // Show current word
        words[index].classList.add("show");

        // Determine delay: 3s after "book", else 1s
        const delay = (index === words.length - 1) ? 3000 : 1000;

        // Move to next word
        index = (index + 1) % words.length;

        setTimeout(popNextWord, delay);
    }

    popNextWord(); // Start loop
});

document.addEventListener("DOMContentLoaded", () => {
    const topLeftWord = document.querySelector(".top-left");

    function updateWord() {
        if (window.innerWidth <= 900) {
            topLeftWord.textContent = "tap";
        } else {
            topLeftWord.textContent = "click";
        }
    }

    // Run on page load
    updateWord();

    // Run on window resize
    window.addEventListener("resize", updateWord);
});

