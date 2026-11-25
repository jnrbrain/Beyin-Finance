(function () {
  const storageKey = "beyin-docs-theme";
  const root = document.documentElement;
  const darkMode = window.matchMedia("(prefers-color-scheme: dark)");
  let selectedTheme;

  try {
    const stored = window.localStorage.getItem(storageKey);
    if (stored === "dark" || stored === "light") selectedTheme = stored;
  } catch {
    // The site also works with storage disabled.
  }

  function applyTheme() {
    const theme = selectedTheme || (darkMode.matches ? "dark" : "light");
    root.setAttribute("data-bf-theme", theme);
    const button = document.querySelector(".bf-theme-toggle");
    if (button) button.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  }

  applyTheme();
  darkMode.addEventListener("change", applyTheme);

  function installToggle() {
    const search = document.querySelector(".wy-side-nav-search");
    if (!search) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "bf-theme-toggle";
    button.addEventListener("click", function () {
      selectedTheme = root.getAttribute("data-bf-theme") === "dark" ? "light" : "dark";
      try {
        window.localStorage.setItem(storageKey, selectedTheme);
      } catch {
        // The selected theme still applies during this visit.
      }
      applyTheme();
    });
    search.appendChild(button);
    applyTheme();
  }

  function installMobileNavigation() {
    const sidebar = document.querySelector(".wy-nav-side");
    const icon = document.querySelector(".wy-nav-top [data-toggle='wy-nav-top']");
    const content = document.querySelector(".wy-nav-content");
    if (!sidebar || !icon || !content) return;

    const mobile = window.matchMedia("(max-width: 768px)");
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "bf-mobile-menu-toggle";
    toggle.setAttribute("aria-label", "Documentation menu");
    toggle.setAttribute("aria-controls", "bf-docs-navigation");
    icon.removeAttribute("data-toggle");
    icon.setAttribute("aria-hidden", "true");
    icon.replaceWith(toggle);
    toggle.appendChild(icon);
    sidebar.id = "bf-docs-navigation";

    const backdrop = document.createElement("div");
    backdrop.className = "bf-mobile-nav-backdrop";
    backdrop.setAttribute("aria-hidden", "true");
    sidebar.after(backdrop);

    function setOpen(open) {
      root.classList.toggle("bf-mobile-nav-open", open);
      sidebar.classList.toggle("shift", open);
      sidebar.inert = mobile.matches && !open;
      content.inert = open;
      backdrop.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
    }

    function closeMenu() {
      setOpen(false);
      toggle.focus();
    }

    setOpen(false);
    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("shift")) {
        closeMenu();
      } else {
        setOpen(true);
        sidebar.querySelector(".wy-side-nav-search > a")?.focus();
      }
    });
    backdrop.addEventListener("click", closeMenu);
    mobile.addEventListener("change", function () { setOpen(false); });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && sidebar.classList.contains("shift")) closeMenu();
    });
    sidebar.addEventListener("click", function (event) {
      const link = event.target.closest("a[href]");
      if (!link || !sidebar.classList.contains("shift")) return;
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const destination = new URL(link.href);
      if (destination.pathname !== window.location.pathname) return;
      closeMenu();
      const section = document.getElementById(decodeURIComponent(destination.hash.slice(1)));
      const heading = section?.querySelector("h2, h3, h4") || section;
      if (heading) {
        // Let the browser follow the fragment before transferring keyboard focus.
        window.setTimeout(function () {
          heading.tabIndex = -1;
          heading.focus({ preventScroll: true });
        }, 0);
      }
    });
  }

  function improveDocumentLandmarks() {
    const main = document.querySelector("[role='main']");
    if (main) {
      main.id = "bf-docs-content";
      main.tabIndex = -1;
      const skipLink = document.createElement("a");
      skipLink.className = "bf-skip-link";
      skipLink.href = "#bf-docs-content";
      skipLink.textContent = "Skip to content";
      skipLink.addEventListener("click", function () {
        document.querySelector(".bf-mobile-menu-toggle[aria-expanded='true']")?.click();
        main.focus();
      });
      document.body.prepend(skipLink);
    }
    const footer = document.querySelector(".wy-nav-content footer");
    if (footer) {
      footer.setAttribute("role", "contentinfo");
      footer.querySelector("[role='contentinfo']")?.removeAttribute("role");
    }
    document.querySelectorAll(".caption[role='heading']").forEach(function (caption) {
      caption.setAttribute("aria-level", "2");
    });
  }

  function improveSectionToggles() {
    const menu = document.querySelector(".wy-menu-vertical");
    if (!menu) return;
    const buttons = Array.from(menu.querySelectorAll("a > .toctree-expand"));
    buttons.forEach(function (button, index) {
      const link = button.parentElement;
      const item = link.parentElement;
      const children = item.querySelector(":scope > ul");
      if (!children) return;
      children.id = "bf-docs-menu-group-" + (index + 1);
      button.type = "button";
      button.removeAttribute("title");
      button.setAttribute("aria-label", "Toggle " + link.textContent.trim());
      button.setAttribute("aria-controls", children.id);
      item.classList.add("bf-nav-branch");
      item.insertBefore(button, link);
    });

    function updateStates() {
      buttons.forEach(function (button) {
        const children = document.getElementById(button.getAttribute("aria-controls"));
        if (!children) return;
        const visible = window.getComputedStyle(children).display !== "none";
        button.setAttribute("aria-expanded", String(visible));
      });
      menu.querySelectorAll("[aria-expanded]:not(button)").forEach(function (element) {
        element.removeAttribute("aria-expanded");
      });
    }

    updateStates();
    new MutationObserver(updateStates).observe(menu, {
      subtree: true,
      attributes: true,
      attributeFilter: ["class"],
    });
  }

  function installCopyControls() {
    if (!navigator.clipboard?.writeText) return;

    const status = document.createElement("span");
    status.className = "bf-visually-hidden";
    status.setAttribute("role", "status");
    document.body.appendChild(status);

    document.querySelectorAll(".rst-content .highlight > pre").forEach(function (sample) {
      const frame = sample.closest("div[class^='highlight-']");
      if (!frame) return;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "bf-copy-code";
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy code");
      let reset;
      button.addEventListener("click", async function () {
        window.clearTimeout(reset);
        status.textContent = "";
        try {
          await navigator.clipboard.writeText(sample.textContent);
          status.textContent = "Code copied to clipboard.";
          button.textContent = "Copied";
        } catch {
          status.textContent = "Select the code to copy it manually.";
          button.textContent = "Failed";
        }
        reset = window.setTimeout(function () { button.textContent = "Copy"; }, 1800);
      });
      frame.prepend(button);
    });
  }

  function labelScrollRegions() {
    const regions = document.querySelectorAll(
      ".rst-content .wy-table-responsive, .rst-content .highlight > pre, .rst-content pre.literal-block"
    );
    const labels = Array.from(regions, function (region) {
      const section = region.closest("section[id]");
      const heading = section?.querySelector(":scope > :is(h1, h2, h3, h4, h5, h6)");
      const title = heading && Array.from(heading.childNodes)
        .filter(node => !node.classList?.contains("headerlink"))
        .map(node => node.textContent).join("").trim();
      const kind = region.matches("pre") ? "Code example" : "Table";
      return [region, title ? kind + " in " + title : kind];
    });
    function updateRegions() {
      labels.forEach(function ([region, name]) {
        if (region.scrollWidth > region.clientWidth + 1) {
          region.tabIndex = 0;
          region.setAttribute("role", "group");
          region.setAttribute("aria-label", name);
        } else {
          region.removeAttribute("tabindex");
          region.removeAttribute("role");
          region.removeAttribute("aria-label");
        }
      });
    }
    updateRegions();
    window.addEventListener("resize", updateRegions);
    document.fonts?.ready.then(updateRegions);
  }

  document.addEventListener("DOMContentLoaded", function () {
    improveDocumentLandmarks();
    installToggle();
    installMobileNavigation();
    // RTD adds table wrappers and navigation buttons in its jQuery ready callback.
    window.jQuery(function () {
      window.setTimeout(enhanceReference, 0);
    });
    function enhanceReference() {
      improveSectionToggles();
      installCopyControls();
      labelScrollRegions();
      if (!window.location.hash) {
        const sidebarScroll = document.querySelector(".wy-side-scroll");
        if (sidebarScroll) sidebarScroll.scrollTop = 0;
      }
    }
  });
})();
