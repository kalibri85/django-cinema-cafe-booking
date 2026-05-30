const selectedSeats = [];

function selectSeat(el) {
    if (el.dataset.status === 'booked' || el.dataset.status === 'reserved') return;

    const seatId = el.dataset.seatId;

    if (el.classList.contains('selected')) {
        el.classList.remove('selected');
        el.style.background = '#EAF3DE';
        el.style.borderColor = '#3B6D11';
        el.style.color = '#27500A';
        selectedSeats.splice(selectedSeats.indexOf(seatId), 1);
    } else {
        el.classList.add('selected');
        el.style.background = '#B5D4F4';
        el.style.borderColor = '#185FA5';
        el.style.color = '#0C447C';
        selectedSeats.push(seatId);
    }

    updateInfo();
}

function updateInfo() {
    const info = document.getElementById('info');
    const btn = document.getElementById('btn-book');
    const n = selectedSeats.length;

    if (n === 0) {
        info.textContent = 'Click on a seat to select';
        btn.style.display = 'none';
    } else {
        const nonIsolatedCount = selectedSeats.filter(id => !isolatedSeatIds.hasOwnProperty(id)).length;
        const hasOddSeat = selectedSeats.some(id => oddSeatIds.hasOwnProperty(id));
        let msg = `Selected ${n} seat(s)`;
        if (!hasOddSeat && nonIsolatedCount % 2 !== 0) {
            msg = `Add one more seat with ${oddDiscount}% discount to ensure your comfort!`;
        }
        info.textContent = msg;
        btn.style.display = 'block';
    }
}

function bookSeats() {
    if (selectedSeats.length === 0) return;

    const n = selectedSeats.length;
    document.getElementById('modal-seats-info').textContent = `You are booking ${n} seat(s)`;
    document.getElementById('modal-overlay').style.display = 'flex';
}
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('modal-error').textContent = '';
}

function submitBooking() {
    const name = document.getElementById('customer-name').value.trim();
    const email = document.getElementById('customer-email').value.trim();

    if (!name || !email) {
        document.getElementById('modal-error').textContent = 'Please fill in all fields';
        return;
    }

    const reservePromises = selectedSeats.map(seatId =>
        fetch(`/book/${seatId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
        }).then(res => res.json())
    );

    Promise.all(reservePromises).then(results => {
        const allReserved = results.every(r => r.success);
        if (!allReserved) {
            document.getElementById('modal-error').textContent = 'Some seats are no longer available.';
            return;
        }

        fetch('/confirm/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `customer_name=${encodeURIComponent(name)}&customer_email=${encodeURIComponent(email)}&seat_ids=${selectedSeats.join(',')}`
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeModal();
                window.location.href = '/payment/'
            } else {
                document.getElementById('modal-error').textContent = 'Something went wrong. Please try again.';
            }
        })
        .catch(() => {
            document.getElementById('modal-error').textContent = 'Connection error. Please try again.';
        });
    });
}

function refreshSeats() {
    fetch('/seats/status/')
        .then(res => res.json())
        .then(data => {
            data.seats.forEach(seat => {
                const el = document.querySelector(`[data-seat-id="${seat.id}"]`);
                if (!el) return;
                if (el.classList.contains('selected')) return;

                const current = el.dataset.status;
                if (current !== seat.status) {
                    el.classList.remove('available', 'booked', 'reserved');
                    el.classList.add(seat.status);
                    el.dataset.status = seat.status;

                    el.style.background = '';
                    el.style.borderColor = '';
                    el.style.color = '';
                }
            });
        });
}

setInterval(refreshSeats, 10000);