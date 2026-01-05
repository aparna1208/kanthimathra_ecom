 (function () {
    const preloader = document.getElementById('preloader');
    if (!preloader) return;

    function hidePreloader() {
      preloader.classList.add('hide');
      // remove from DOM after transition for performance
      setTimeout(() => preloader.remove(), 450);
    }

    // Hide only after ALL contents load (images, videos, fonts, etc.)
    window.addEventListener('load', hidePreloader);

    // Safety fallback (in case load event gets stuck)
    setTimeout(hidePreloader, 12000);
  })();


const btn = document.getElementById('menuBtn');
const menu = document.getElementById('mobileMenu');
btn?.addEventListener('click', () => menu.classList.toggle('hidden'));


// revel
const reveals = document.querySelectorAll('.reveal');

const observer = new IntersectionObserver(
    entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target); // animate once
            }
        });
    },
    {
        threshold: 0.15,
    }
);

reveals.forEach(el => observer.observe(el));



// video

const playBtn = document.getElementById('playVideo');
  const video = document.getElementById('videoEl');

  playBtn.addEventListener('click', () => {
    playBtn.classList.add('hidden');
    video.classList.remove('hidden');

    video.muted = false;      // force sound
    video.volume = 1;        // full volume
    video.play();
  });





// year
 document.getElementById('year').textContent = new Date().getFullYear();






//  +/- button

