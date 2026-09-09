(function () {
  "use strict";

  var contextNode = document.querySelector("[data-garden-context]");
  if (!contextNode) return;

  var context;

  try {
    context = JSON.parse(contextNode.textContent);
  } catch (error) {
    console.error("GardenHub: invalid garden context.", error);
    return;
  }

  var gardens = Array.isArray(context.gardens)
    ? context.gardens
    : [];

  if (!gardens.length) return;

  var activeStorageKey = "gardenhub.active-garden.session";

  function readSession(key) {
    try {
      return window.sessionStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function writeSession(key, value) {
    try {
      window.sessionStorage.setItem(key, value);
    } catch (error) {
      // Session persistence is optional.
    }
  }

  function gardenById(id) {
    return gardens.find(function (garden) {
      return garden.id === id;
    }) || null;
  }

  var activeGarden =
    gardenById(readSession(activeStorageKey)) ||
    gardenById(context.active_garden_id) ||
    gardens[0];

  function getActiveGarden() {
    return activeGarden;
  }

  function getLocation() {
    return activeGarden.location || {};
  }

  function coordinateLabel(location) {
    if (
      Number.isFinite(location.latitude) &&
      Number.isFinite(location.longitude)
    ) {
      return (
        location.latitude.toFixed(4) +
        "°, " +
        location.longitude.toFixed(4) +
        "°"
      );
    }

    return "Location unavailable";
  }

  function updateInterface() {
    var location = getLocation();

    document
      .querySelectorAll("[data-active-garden-name]")
      .forEach(function (node) {
        node.textContent = activeGarden.name;
      });

    document
      .querySelectorAll("[data-active-garden-location]")
      .forEach(function (node) {
        node.textContent =
          location.address_label ||
          coordinateLabel(location);
      });

    document
      .querySelectorAll("[data-garden-option]")
      .forEach(function (button) {
        button.setAttribute(
          "aria-selected",
          String(
            button.dataset.gardenOption === activeGarden.id
          )
        );
      });

    document.documentElement.dataset.activeGardenId =
      activeGarden.id;
  }

  function closeGardenMenu() {
    var panel = document.getElementById("garden-context-menu");

    var trigger = document.querySelector(
      '[data-menu-trigger="garden-context-menu"]'
    );

    if (panel) {
      panel.hidden = true;
    }

    if (trigger) {
      trigger.setAttribute("aria-expanded", "false");
    }
  }

  function setLocation(location) {
    activeGarden.location = location || {};

    updateInterface();

    window.dispatchEvent(
      new CustomEvent("gardenhub:gardenlocationchange", {
        detail: {
          garden: activeGarden,
          location: activeGarden.location,
          persistence: "backend"
        }
      })
    );
  }

  document
    .querySelectorAll("[data-garden-option]")
    .forEach(function (button) {
      button.addEventListener("click", function () {
        var nextGarden = gardenById(
          button.dataset.gardenOption
        );

        if (!nextGarden) return;

        activeGarden = nextGarden;

        writeSession(
          activeStorageKey,
          activeGarden.id
        );

        updateInterface();
        closeGardenMenu();

        window.dispatchEvent(
          new CustomEvent("gardenhub:gardenchange", {
            detail: {
              garden: activeGarden,
              location: getLocation(),
              persistence: "browser_session_only"
            }
          })
        );
      });
    });

  document
    .querySelectorAll("[data-workspace-garden-trigger]")
    .forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.stopPropagation();

        var trigger = document.querySelector(
          '[data-menu-trigger="garden-context-menu"]'
        );

        if (trigger) {
          trigger.click();
        }
      });
    });

  /*
   * Small public API for other GardenHub frontend modules.
   *
   * garden-location.js does not need to duplicate
   * active-garden/header/menu logic.
   */
  window.GardenHubGardenContext = {
    getActiveGarden: getActiveGarden,
    getLocation: getLocation,
    setLocation: setLocation,
    closeMenu: closeGardenMenu
  };

  updateInterface();
})();