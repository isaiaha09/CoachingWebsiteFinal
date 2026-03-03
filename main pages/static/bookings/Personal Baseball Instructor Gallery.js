/* ===============================
   Top Slideshow (Photo-based)
   =============================== */
var topSlideShow = (function () {
    var slideIndex = 0;
    var autoSlideInterval;
    var slides = document.getElementsByClassName("mySlides");

    function showSlides() {
        for (var i = 0; i < slides.length; i++) {
            slides[i].style.opacity = "0";
            slides[i].style.transition = "opacity 1.5s ease-in-out";
            slides[i].style.position = "absolute";
            slides[i].style.width = "100%";
        }

        slides[slideIndex].style.opacity = "1";
        slides[slideIndex].style.position = "relative";
    }

    function plusSlides(n) {
        clearInterval(autoSlideInterval);
        slideIndex += n;
        if (slideIndex >= slides.length) slideIndex = 0;
        if (slideIndex < 0) slideIndex = slides.length - 1;
        showSlides();
        startAutoSlide();
    }

    function startAutoSlide() {
        clearInterval(autoSlideInterval);
        autoSlideInterval = setInterval(function () {
            slideIndex = (slideIndex + 1) % slides.length;
            showSlides();
        }, 4000); // 4-second interval
    }

    function init() {
        showSlides();        // Show first slide immediately
        startAutoSlide();    // Start automatic slideshow
    }

    return {
        plusSlides: plusSlides,
        init: init
    };
})();

/* ===============================
   Bottom Slideshow (Video-based)
   =============================== */

var bottomSlideShow = (function () {
    var slideIndex = 0;
    var slides = [];
    var slideTimer = null; 

    function init() {
        slides = document.getElementsByClassName("mySlides2");
        showSlides();
    }

    function clearSlideTimer() {
        if (slideTimer) {
            clearTimeout(slideTimer);
            slideTimer = null;
        }
    }

    function stopAndResetAllVideos() {
        for (let i = 0; i < slides.length; i++) {
            let v = slides[i].querySelector("video");
            if (v) {
                v.onplay = null;
                v.onpause = null;
                v.onended = null;
                try { v.pause(); } catch(e) {}
                try { v.currentTime = 0; } catch(e) {}
            }
        }
    }

    function scheduleNextSlide(delayMs = 10000) {
        clearSlideTimer();
        slideTimer = setTimeout(() => {
            slideIndex++;
            if (slideIndex >= slides.length) slideIndex = 0;
            showSlides();
        }, delayMs);
    }

    function showSlides() {
        if (slides.length === 0) return;

        // normalize index
        if (slideIndex >= slides.length) slideIndex = 0;
        if (slideIndex < 0) slideIndex = slides.length - 1;

        // hide all slides & stop videos
        stopAndResetAllVideos();
        clearSlideTimer();

        for (let i = 0; i < slides.length; i++) {
            slides[i].style.opacity = "0";
            slides[i].style.position = "absolute";
            slides[i].style.width = "100%";
        }

        // show current slide
        let current = slides[slideIndex];
        current.style.opacity = "1";
        current.style.position = "relative";

        let activeVideo = current.querySelector("video");

        if (activeVideo) {
            // Video never autoplay
            try { activeVideo.pause(); } catch(e) {}
            try { activeVideo.currentTime = 0; } catch(e) {}

            // Schedule 10-second auto-advance if not playing
            scheduleNextSlide(10000);

            // While user plays, cancel timer
            activeVideo.onplay = function () {
                clearSlideTimer();
            };

            // When paused, start 10s timer to next slide
            activeVideo.onpause = function () {
                scheduleNextSlide(10000);
            };

            // When video ends, start 10s timer to next slide
            activeVideo.onended = function () {
                scheduleNextSlide(10000);
            };
        } else {
            // Photo slide → auto-advance after 4s
            slideTimer = setTimeout(() => {
                slideIndex++;
                if (slideIndex >= slides.length) slideIndex = 0;
                showSlides();
            }, 4000);
        }
    }

    function plusSlides(n) {
        stopAndResetAllVideos();
        clearSlideTimer();

        slideIndex += n;
        if (slideIndex >= slides.length) slideIndex = 0;
        if (slideIndex < 0) slideIndex = slides.length - 1;
        showSlides();
    }

    return {
        init: init,
        plusSlides: plusSlides
    };
})();

document.addEventListener("DOMContentLoaded", function () {
    bottomSlideShow.init();
});

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