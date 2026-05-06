(() => {
  window.addEventListener("scroll", () => {
    const progress = document.getElementById("readingProgress");
    if (!progress) return;
    const doc = document.documentElement;
    const top = doc.scrollTop || document.body.scrollTop;
    const height = doc.scrollHeight - doc.clientHeight;
    const percent = height > 0 ? (top / height) * 100 : 0;
    progress.style.width = `${percent}%`;
  });

  const copyBtn = document.getElementById("copyArticleLink");
  const copyMsg = document.getElementById("copyArticleMessage");
  if (copyBtn && copyMsg) {
    const defaultCopyText = copyMsg.textContent;
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        copyMsg.textContent = "Ссылка скопирована.";
      } catch (_error) {
        copyMsg.textContent = "Не удалось скопировать ссылку.";
      }
      window.setTimeout(() => {
        copyMsg.textContent = defaultCopyText;
      }, 2500);
    });
  }

  document.querySelectorAll(".js-fallback-hero-image").forEach((img) => {
    img.addEventListener("error", () => {
      const cover = img.closest(".news-hero-cover");
      if (cover) {
        cover.classList.add("is-image-broken");
      }
      img.remove();
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
