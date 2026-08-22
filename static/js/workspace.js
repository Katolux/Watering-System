(function () {
  "use strict";

  var viewButtons = Array.from(document.querySelectorAll("[data-workspace-view]"));
  var viewPanels = Array.from(document.querySelectorAll("[data-workspace-panel]"));

  viewButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      var selectedView = button.dataset.workspaceView;
      viewButtons.forEach(function (item) {
        var selected = item === button;
        item.classList.toggle("is-active", selected);
        item.setAttribute("aria-pressed", String(selected));
      });
      viewPanels.forEach(function (panel) {
        panel.hidden = panel.dataset.workspacePanel !== selectedView;
      });
    });
  });

})();
