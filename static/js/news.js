(() => {
  document.querySelectorAll(".news-filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const category = btn.dataset.category;
      document.querySelectorAll(".news-filter-btn").forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll("[data-category]").forEach((card) => {
        const isVisible = category === "all" || card.dataset.category === category;
        card.style.display = isVisible ? "" : "none";
      });
    });
  });

  document.querySelectorAll(".js-fallback-image").forEach((img) => {
    img.addEventListener("error", () => {
      const cover = img.closest(".news-card-cover");
      if (cover) {
        cover.classList.add("is-image-broken");
      }
      img.remove();
    });
  });
})();
