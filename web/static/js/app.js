// HYROX Course Correct - JavaScript

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('convertForm');
    const resultDiv = document.getElementById('result');

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
