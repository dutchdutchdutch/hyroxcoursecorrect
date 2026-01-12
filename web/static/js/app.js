// HYROX Course Correct - JavaScript

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('convertForm');

    // Only add submit listener if the conversion form exists on this page
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const formData = {
                finish_time: document.getElementById('finishTime').value,
                from_venue: document.getElementById('fromVenue').value,
                to_venue: document.getElementById('toVenue').value,
                gender: document.querySelector('input[name="gender"]:checked').value
            };

            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) {
                    const error = await response.json();
                    alert(error.error || 'An error occurred');
                    return;
                }

                const data = await response.json();
                displayResult(data);

            } catch (error) {
                console.error('Error:', error);
                alert('Failed to convert time. Please try again.');
            }
        });
    }

    // Feedback Form Handling
    const feedbackForm = document.getElementById('feedbackForm');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const formData = new FormData(feedbackForm);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    alert('Thank you for your feedback!');
                    closeFeedbackModal();
                    feedbackForm.reset();
                } else {
                    alert('Failed to submit feedback. Please try again.');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }

    // Feature Flag: Auto-popup timer
    if (typeof SHOW_FEEDBACK_POPUP !== 'undefined' && SHOW_FEEDBACK_POPUP) {
        setTimeout(() => {
            // Only open if not already viewed/dismissed in this session (optional, simpler for now just opens)
            // Check if modal is already open to avoid disruption
            const modal = document.getElementById('feedbackModal');
            if (modal && modal.classList.contains('hidden')) {
                openFeedbackModal();
            }
        }, 120000); // 2 minutes (120,000 ms)
    }
});

function displayResult(data) {
    // Update result display
    document.getElementById('originalTime').textContent = data.original_time;
    document.getElementById('originalVenue').textContent = `${data.from_venue} (${data.gender})`;
    document.getElementById('convertedTime').textContent = data.converted_time;
    document.getElementById('convertedVenue').textContent = data.to_venue;

    // Update time difference
    const timeDiffDiv = document.getElementById('timeDiff');
    const diffText = data.faster ?
        `⚡ ${data.time_difference} faster` :
        `🐌 ${data.time_difference} slower`;

    timeDiffDiv.textContent = diffText;
    timeDiffDiv.className = 'time-diff ' + (data.faster ? 'faster' : 'slower');

    // Show result
    document.getElementById('result').classList.remove('hidden');

    // Smooth scroll to result
    document.getElementById('result').scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
    });
}

// Global functions for Feedback Modal
function openFeedbackModal(e) {
    if (e) e.preventDefault();
    const modal = document.getElementById('feedbackModal');
    modal.classList.remove('hidden');
    // Small timeout to allow removing 'hidden' to take effect before adding 'visible' for transition
    setTimeout(() => {
        modal.classList.add('visible');
    }, 10);
}

function closeFeedbackModal() {
    const modal = document.getElementById('feedbackModal');
    modal.classList.remove('visible');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300); // Wait for transition
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('feedbackModal');
    if (event.target === modal) {
        closeFeedbackModal();
    }
}
