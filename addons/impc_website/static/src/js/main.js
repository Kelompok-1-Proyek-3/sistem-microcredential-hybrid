document.addEventListener('DOMContentLoaded', () => {
    const revealItems = document.querySelectorAll('.impc-reveal');
    const observer = new IntersectionObserver(
        (entries, obs) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    obs.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.15 }
    );

    revealItems.forEach((item) => observer.observe(item));

    const redeemButtons = document.querySelectorAll('[data-redeem]');
    redeemButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const targetId = button.getAttribute('data-redeem-target');
            const target = document.getElementById(targetId);
            if (!target) {
                return;
            }
            target.textContent = 'Validation is not connected yet. This is a UI placeholder.';
        });
    });

    const filterButtons = document.querySelectorAll('[data-impc-filter]');
    filterButtons.forEach((button) => {
        button.addEventListener('click', () => {
            filterButtons.forEach((btn) => btn.classList.remove('is-active'));
            button.classList.add('is-active');
        });
    });
});
