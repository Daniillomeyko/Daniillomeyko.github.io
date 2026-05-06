const yearElement = document.getElementById("year");
const menuLinks = document.querySelectorAll(".menu a");
const sections = document.querySelectorAll("main[id], section[id]");
const menuToggle = document.getElementById("menu-toggle");
const mainMenu = document.getElementById("main-menu");

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
