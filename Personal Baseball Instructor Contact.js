document.getElementById('contactForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    const formData = new FormData(this); // Collect form data

    // Send the form data using Fetch API
    fetch('http://formsubmit.co/isaiah.aris@gmail.com', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.ok) {
            // Show the success message
            document.querySelector('.message').style.display = 'block';
            this.reset(); // Reset the form fields
        } else {
            throw new Error('Network response was not ok.');
        }
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });
});