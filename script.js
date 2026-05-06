const yearElement = document.getElementById("year");
const themeButton = document.getElementById("theme-toggle");
const menuLinks = document.querySelectorAll(".menu a");
const sections = document.querySelectorAll("main[id], section[id]");
const savedTheme = localStorage.getItem("theme");

if (yearElement) {
  yearElement.textContent = new Date().getFullYear();
}

if (savedTheme === "light") {
  document.body.classList.add("light");
}

if (themeButton) {
  themeButton.addEventListener("click", () => {
    document.body.classList.toggle("light");
    const currentTheme = document.body.classList.contains("light") ? "light" : "dark";
    localStorage.setItem("theme", currentTheme);
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
