function filterDates() {
    const type = document.querySelector('select[name="session_type"]').value;
    document.querySelectorAll('input[name="dates"]').forEach(cb => {
        const d = cb.value;
        const wrapper = cb.parentElement;
        const taken = type === 'day' ? existingDay : existingEvening;
        if (taken.includes(d)) {
            wrapper.style.display = 'none';
            cb.checked = false;
        } else {
            wrapper.style.display = '';
        }
    });
}

document.querySelector('select[name="session_type"]').addEventListener('change', filterDates);
filterDates();