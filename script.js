(() => {
  const yearElement = document.getElementById("year");
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const navLinks = document.getElementById("navLinks");
  const revealItems = document.querySelectorAll(".reveal");

  if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
  }

  if (mobileMenuBtn && navLinks) {
    mobileMenuBtn.addEventListener("click", () => {
      navLinks.classList.toggle("active");
      navLinks.classList.toggle("open");
      const isExpanded = navLinks.classList.contains("active");
      mobileMenuBtn.setAttribute("aria-expanded", isExpanded ? "true" : "false");

      const icon = mobileMenuBtn.querySelector("i");
      if (icon) {
        icon.classList.toggle("fa-bars", !isExpanded);
        icon.classList.toggle("fa-times", isExpanded);
      }
    });

    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("active", "open");
        mobileMenuBtn.setAttribute("aria-expanded", "false");
      });
    });
  }

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
          }
        });
      },
      { threshold: 0.15 }
    );

    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add("in"));
  }
})();
