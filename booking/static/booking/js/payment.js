let seconds = 600;

function updateTimer() {
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    document.getElementById('countdown').textContent =
        `${min}:${sec.toString().padStart(2, '0')}`;

    if (seconds <= 0) {
        document.getElementById('timer').textContent = 'Reservation expired!';
        window.location.href = '/';
    }
    seconds--;
}

setInterval(updateTimer, 1000);