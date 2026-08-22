(function () {
  "use strict";

  var shell = document.querySelector("[data-app-shell]");
  if (!shell) return;

  var desktopToggle = shell.querySelector("[data-sidebar-toggle]");
  var mobileToggle = shell.querySelector("[data-mobile-sidebar-toggle]");
  var scrim = shell.querySelector("[data-sidebar-scrim]");
  var tabletQuery = window.matchMedia("(max-width: 64rem)");

  function setMobileSidebar(open) {
    shell.dataset.sidebarOpen = String(open);
    if (mobileToggle) mobileToggle.setAttribute("aria-expanded", String(open));
    if (scrim) scrim.hidden = !open;
    document.body.style.overflow = open ? "hidden" : "";
  }

  if (desktopToggle) {
    desktopToggle.addEventListener("click", function () {
      if (tabletQuery.matches) {
        setMobileSidebar(false);
        return;
      }

      var collapsed = shell.dataset.sidebarCollapsed !== "true";
      shell.dataset.sidebarCollapsed = String(collapsed);
      desktopToggle.setAttribute("aria-expanded", String(!collapsed));
      desktopToggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
      desktopToggle.setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
    });
  }

  if (mobileToggle) {
    mobileToggle.addEventListener("click", function () {
      setMobileSidebar(shell.dataset.sidebarOpen !== "true");
    });
  }

  if (scrim) scrim.addEventListener("click", function () { setMobileSidebar(false); });

  tabletQuery.addEventListener("change", function () {
    setMobileSidebar(false);
  });

  document.querySelectorAll("[data-menu-trigger]").forEach(function (trigger) {
    trigger.addEventListener("click", function () {
      var panel = document.getElementById(trigger.dataset.menuTrigger);
      var willOpen = panel && panel.hidden;

      document.querySelectorAll("[data-menu-panel]").forEach(function (item) { item.hidden = true; });
      document.querySelectorAll("[data-menu-trigger]").forEach(function (item) { item.setAttribute("aria-expanded", "false"); });

      if (panel && willOpen) {
        panel.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
      }
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest(".header-menu")) {
      document.querySelectorAll("[data-menu-panel]").forEach(function (panel) { panel.hidden = true; });
      document.querySelectorAll("[data-menu-trigger]").forEach(function (trigger) { trigger.setAttribute("aria-expanded", "false"); });
    }
  });

  document.querySelectorAll("[data-tabs]").forEach(function (tabList) {
    var tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));

    tabs.forEach(function (tab, index) {
      tab.addEventListener("click", function () {
        tabs.forEach(function (item) {
          var selected = item === tab;
          item.setAttribute("aria-selected", String(selected));
          item.setAttribute("tabindex", selected ? "0" : "-1");
          var panel = document.getElementById(item.getAttribute("aria-controls"));
          if (panel) panel.hidden = !selected;
        });
      });

      tab.addEventListener("keydown", function (event) {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        var offset = event.key === "ArrowRight" ? 1 : -1;
        tabs[(index + offset + tabs.length) % tabs.length].focus();
      });
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    setMobileSidebar(false);
    document.querySelectorAll("[data-menu-panel]").forEach(function (panel) { panel.hidden = true; });
    document.querySelectorAll("[data-menu-trigger]").forEach(function (trigger) { trigger.setAttribute("aria-expanded", "false"); });
  });
})();
