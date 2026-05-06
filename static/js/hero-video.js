(function () {
    const heroVideo = document.querySelector(".hero-video-bg");
    if (!heroVideo) {
        return;
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const saveData = navigator.connection && navigator.connection.saveData;

    const hideVideo = function () {
        heroVideo.pause();
        heroVideo.style.display = "none";
    };

    const showVideo = function () {
        heroVideo.style.display = "";
    };

    if (reducedMotion || saveData) {
        hideVideo();
        return;
    }

    const startPlayback = function () {
        const playPromise = heroVideo.play();
        if (playPromise && typeof playPromise.then === "function") {
            // В ряде браузеров autoplay может быть отклонен, но файл при этом корректный.
            // Не скрываем видео, оставляем первый кадр вместо "пропажи" hero.
            playPromise.catch(function () {});
        }
    };

    heroVideo.addEventListener("loadeddata", function () {
        showVideo();
        startPlayback();
    }, { once: true });
    heroVideo.addEventListener("error", hideVideo);
    heroVideo.querySelectorAll("source").forEach(function (sourceEl) {
        sourceEl.addEventListener("error", hideVideo);
    });

    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            heroVideo.pause();
        } else {
            startPlayback();
        }
    });
})();
