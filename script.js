const yearElement = document.getElementById("year");
const themeButton = document.getElementById("theme-toggle");

if (yearElement) {
  yearElement.textContent = new Date().getFullYear();
}

if (themeButton) {
  themeButton.addEventListener("click", () => {
    document.body.classList.toggle("light");
  });
}
