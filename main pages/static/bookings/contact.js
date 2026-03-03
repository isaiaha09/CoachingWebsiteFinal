const form = document.getElementById("contactForm");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    firstname: form.firstname.value,
    lastname: form.lastname.value,
    email: form.email.value,
    phone: form.phone.value,
    subject: form.subject.value,
    message: form.message.value,
  };

  try {
    const res = await fetch("/contact/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    alert(data.message);
  } catch (err) {
    alert("Something went wrong. Please try again later.");
    console.error(err);
  }
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