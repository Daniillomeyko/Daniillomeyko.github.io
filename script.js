const yearElement = document.getElementById("year");
const menuLinks = document.querySelectorAll(".menu a");
const sections = document.querySelectorAll("main[id], section[id]");
const menuToggle = document.getElementById("menu-toggle");
const mainMenu = document.getElementById("main-menu");
const revealItems = document.querySelectorAll(".card, .kpi, .timeline article, .adv-grid article, .contact-card");

if (yearElement) {
  yearElement.textContent = new Date().getFullYear();
}

if (menuToggle && mainMenu) {
  menuToggle.addEventListener("click", () => {
    mainMenu.classList.toggle("open");
  });
}

const setActiveMenu = () => {
  const scrollY = window.scrollY + 120;
  let currentId = "";

  sections.forEach((section) => {
    if (scrollY >= section.offsetTop) {
      currentId = section.id;
    }
  });

  menuLinks.forEach((link) => {
    const isActive = link.getAttribute("href") === `#${currentId}`;
    link.classList.toggle("active", isActive);
  });
};

window.addEventListener("scroll", setActiveMenu);
setActiveMenu();

menuLinks.forEach((link) => {
  link.addEventListener("click", () => {
    if (mainMenu) {
      mainMenu.classList.remove("open");
    }
  });
});

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  revealItems.forEach((item) => {
    item.classList.add("reveal");
    observer.observe(item);
  });
}
