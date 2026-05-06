(() => {
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const navLinks = document.getElementById("navLinks");

    if (!mobileMenuBtn || !navLinks) {
        return;
    }

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

            const icon = mobileMenuBtn.querySelector("i");
            if (icon) {
                icon.classList.add("fa-bars");
                icon.classList.remove("fa-times");
            }
        });
    });
})();
