(() => {
  const navLinks = document.getElementById("navLinks");
  const menuBtn = document.querySelector(".mobile-menu-btn");

  const setMenuState = (isOpen) => {
    if (!navLinks || !menuBtn) return;
    navLinks.classList.toggle("active", isOpen);
    menuBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    const icon = menuBtn.querySelector("i");
    if (icon) {
      icon.classList.toggle("fa-bars", !isOpen);
      icon.classList.toggle("fa-times", isOpen);
    }
  };

  if (menuBtn && navLinks) {
    menuBtn.addEventListener("click", () => {
      setMenuState(!navLinks.classList.contains("active"));
    });
  }

  window.addEventListener("scroll", () => {
    const header = document.querySelector(".header");
    if (header) {
      header.classList.toggle("scrolled", window.scrollY > 50);
    }
  });

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("fade-in-up");
          }
        });
      },
      { threshold: 0.1 }
    );
    document.querySelectorAll(".animate-on-scroll").forEach((el) => observer.observe(el));
  }

  document.querySelectorAll(".nav-links a").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        setMenuState(false);
      }
    });
  });

  let footerLogoClicks = 0;
  let footerLogoTimer = null;
  const footerLogo = document.querySelector(".footer-logo");
  if (footerLogo) {
    footerLogo.style.cursor = "pointer";
    footerLogo.addEventListener("click", () => {
      footerLogoClicks += 1;
      if (footerLogoClicks === 1) {
        footerLogoTimer = setTimeout(() => {
          footerLogoClicks = 0;
        }, 2000);
      }
      if (footerLogoClicks === 5) {
        clearTimeout(footerLogoTimer);
        footerLogoClicks = 0;
        window.location.href = "/admin";
      }
    });
  }

  document.querySelectorAll(".js-about-image").forEach((img) => {
    img.addEventListener("error", () => {
      const wrap = img.closest(".about-image");
      if (wrap) {
        wrap.classList.add("is-broken");
      }
      img.remove();
    });
  });
})();
