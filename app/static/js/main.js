/**
 * NyayVeya - Global Interactive & Animation Controller
 * Smooth scroll reveals, header elevation, card micro-interactions, mobile drawer.
 */
document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // 2. Sticky Header Elevation on Scroll
    const header = document.querySelector('header');
    if (header) {
        const updateHeaderElevation = () => {
            if (window.scrollY > 15) {
                header.classList.add('header-scrolled');
            } else {
                header.classList.remove('header-scrolled');
            }
        };
        window.addEventListener('scroll', updateHeaderElevation, { passive: true });
        updateHeaderElevation();
    }

    // 3. Mobile Navigation Drawer Toggle
    const menuToggle = document.getElementById('menu-toggle');
    const mobileLinks = document.getElementById('mobile-links');
    if (menuToggle && mobileLinks) {
        menuToggle.addEventListener('click', function () {
            const isHidden = mobileLinks.classList.contains('hidden');
            mobileLinks.classList.toggle('hidden', !isHidden);
            menuToggle.setAttribute('aria-expanded', String(isHidden));
            if (isHidden) {
                mobileLinks.classList.add('animate-drawer');
            }
        });
    }

    // 4. Scroll Reveal Observer
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const revealElements = document.querySelectorAll('.reveal-on-scroll');

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
        revealElements.forEach(function (el) {
            el.classList.add('reveal-visible');
        });
    } else {
        const revealObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('reveal-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.08,
            rootMargin: '0px 0px -30px 0px'
        });

        revealElements.forEach(function (el) {
            revealObserver.observe(el);
        });

        window.NyayVeyaRevealObserver = revealObserver;
    }

    // 5. Smooth Anchor Scrolling for on-page links
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetElem = document.querySelector(targetId);
                if (targetElem) {
                    e.preventDefault();
                    targetElem.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });
});

/**
 * 6. Global Password Visibility Toggle
 * Toggles input type between 'password' and 'text' and swaps eye/eye-off icons.
 */
window.togglePasswordVisibility = function (fieldId, btn) {
    const input = document.getElementById(fieldId);
    if (!input) return;
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    const eye = btn.querySelector('.eye-icon');
    const eyeOff = btn.querySelector('.eye-off-icon');
    if (eye && eyeOff) {
        eye.classList.toggle('hidden', isPassword);
        eyeOff.classList.toggle('hidden', !isPassword);
    }
};
