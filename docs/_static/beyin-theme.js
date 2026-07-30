(function () {
  const storageKey = "beyin-docs-theme";
  const root = document.documentElement;

  function preferredTheme() {
    const stored = window.localStorage.getItem(storageKey);
    if (stored === "dark" || stored === "light") return stored;
    return "light";
  }

  function label(theme) {
    return theme === "dark" ? "Light mode" : "Dark mode";
  }

  function applyTheme(theme) {
    root.setAttribute("data-bf-theme", theme);
    window.localStorage.setItem(storageKey, theme);
    const button = document.querySelector(".bf-theme-toggle");
    if (button) button.textContent = label(theme);
  }

  applyTheme(preferredTheme());

  function installToggle() {
    const search = document.querySelector(".wy-side-nav-search");
    if (!search || document.querySelector(".bf-theme-toggle")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "bf-theme-toggle";
    button.addEventListener("click", function () {
      const current = root.getAttribute("data-bf-theme") || "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
    const version = search.querySelector(".version");
    if (version && version.parentNode === search) {
      version.insertAdjacentElement("afterend", button);
    } else {
      search.appendChild(button);
    }
    button.textContent = label(root.getAttribute("data-bf-theme") || "light");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", installToggle);
  } else {
    installToggle();
  }
})();
