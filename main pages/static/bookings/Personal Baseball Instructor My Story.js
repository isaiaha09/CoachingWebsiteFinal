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

document.addEventListener("DOMContentLoaded", () => {
    const faders = document.querySelectorAll('.fade-in');

    const appearOptions = {
      threshold: 0.1,   // triggers when 20% visible
      rootMargin: "0px 0px -50px 0px"
    };

    const appearOnScroll = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("show");
          observer.unobserve(entry.target); // only animate once
        }
      });
    }, appearOptions);

    faders.forEach(fader => {
      appearOnScroll.observe(fader);
    });
  });