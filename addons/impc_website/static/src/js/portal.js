/** @odoo-module **/

/**
 * IMPC Portal JavaScript
 * Handles dashboard interactivity and progress tracking.
 */

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // === Animate progress bars on scroll ===
    const progressBars = document.querySelectorAll('.progress-bar');
    if (progressBars.length) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.style.width;
                    bar.style.width = '0%';
                    setTimeout(function () {
                        bar.style.width = width;
                    }, 100);
                    observer.unobserve(bar);
                }
            });
        }, { threshold: 0.5 });

        progressBars.forEach(function (bar) {
            observer.observe(bar);
        });
    }

    // === Animate stat counters ===
    const statNumbers = document.querySelectorAll('.impc-stats h3');
    if (statNumbers.length) {
        const counterObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10);
                    if (isNaN(target) || target === 0) return;

                    let current = 0;
                    const increment = Math.ceil(target / 50);
                    const suffix = el.textContent.replace(/[0-9]/g, '');

                    const timer = setInterval(function () {
                        current += increment;
                        if (current >= target) {
                            current = target;
                            clearInterval(timer);
                        }
                        el.textContent = current + suffix;
                    }, 30);

                    counterObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        statNumbers.forEach(function (el) {
            counterObserver.observe(el);
        });
    }

    // === Smooth scroll for anchor links ===
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                });
            }
        });
    });

    // === Active nav link highlighting ===
    const currentPath = window.location.pathname;
    document.querySelectorAll('.impc-navbar .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active', 'fw-bold');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active', 'fw-bold');
        }
    });
});
