(function () {
  "use strict";

  var button = document.querySelector("[data-weather-refresh]");
  if (!button) return;

  var label = button.querySelector("[data-weather-refresh-label]");
  var status = document.querySelector("[data-weather-refresh-status]");
  var normalLabel = label.textContent;

  function setRefreshing(isRefreshing) {
    button.disabled = isRefreshing;
    label.textContent = isRefreshing ? "Refreshing\u2026" : normalLabel;
    if (isRefreshing) {
      button.setAttribute("aria-busy", "true");
    } else {
      button.removeAttribute("aria-busy");
    }
  }

  button.addEventListener("click", async function () {
    if (button.disabled) return;

    setRefreshing(true);
    status.hidden = true;
    status.textContent = "";

    try {
      var response = await fetch(button.dataset.refreshUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Accept": "application/json",
          "X-Requested-With": "XMLHttpRequest"
        }
      });
      var result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.error || "Weather refresh request failed");
      }
      window.location.reload();
    } catch (error) {
      status.textContent = "Couldn\u2019t refresh weather. Current data is still shown.";
      status.hidden = false;
    } finally {
      setRefreshing(false);
    }
  });
})();
