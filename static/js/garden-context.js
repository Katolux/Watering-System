(function () {
  "use strict";

  var contextNode = document.querySelector("[data-garden-context]");
  if (!contextNode) return;

  var context;
  try { context = JSON.parse(contextNode.textContent); } catch (error) { return; }

  var gardens = Array.isArray(context.gardens) ? context.gardens : [];
  if (!gardens.length) return;

  var activeStorageKey = "gardenhub.active-garden.session";
  var locationStoragePrefix = "gardenhub.garden-location.session.";

  function readSession(key) {
    try { return window.sessionStorage.getItem(key); } catch (error) { return null; }
  }

  function writeSession(key, value) {
    try { window.sessionStorage.setItem(key, value); } catch (error) { /* Session state is optional. */ }
  }

  function gardenById(id) {
    return gardens.find(function (garden) { return garden.id === id; }) || null;
  }

  var storedGarden = gardenById(readSession(activeStorageKey));
  var activeGarden = storedGarden || gardenById(context.active_garden_id) || gardens[0];

  function storedLocation(garden) {
    var serialized = readSession(locationStoragePrefix + garden.id);
    if (!serialized) return garden.location || {};
    try { return JSON.parse(serialized); } catch (error) { return garden.location || {}; }
  }

  function coordinateLabel(location) {
    if (Number.isFinite(location.latitude) && Number.isFinite(location.longitude)) {
      return location.latitude.toFixed(4) + "\u00b0, " + location.longitude.toFixed(4) + "\u00b0";
    }
    return "Coordinates not resolved";
  }

  function updateInterface() {
    var location = storedLocation(activeGarden);
    document.querySelectorAll("[data-active-garden-name]").forEach(function (node) {
      node.textContent = activeGarden.name;
    });
    document.querySelectorAll("[data-active-garden-location]").forEach(function (node) {
      node.textContent = location.address_label || coordinateLabel(location);
    });
    document.querySelectorAll("[data-garden-option]").forEach(function (button) {
      button.setAttribute("aria-selected", String(button.dataset.gardenOption === activeGarden.id));
    });
    document.documentElement.dataset.activeGardenId = activeGarden.id;
  }

  function closeGardenMenu() {
    var panel = document.getElementById("garden-context-menu");
    var trigger = document.querySelector('[data-menu-trigger="garden-context-menu"]');
    if (panel) panel.hidden = true;
    if (trigger) trigger.setAttribute("aria-expanded", "false");
  }

  document.querySelectorAll("[data-garden-option]").forEach(function (button) {
    button.addEventListener("click", function () {
      var nextGarden = gardenById(button.dataset.gardenOption);
      if (!nextGarden) return;
      activeGarden = nextGarden;
      writeSession(activeStorageKey, activeGarden.id);
      updateInterface();
      closeGardenMenu();
      window.dispatchEvent(new CustomEvent("gardenhub:gardenchange", {
        detail: { garden: activeGarden, location: storedLocation(activeGarden), persistence: "browser_session_only" }
      }));
    });
  });

  document.querySelectorAll("[data-workspace-garden-trigger]").forEach(function (button) {
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      var trigger = document.querySelector('[data-menu-trigger="garden-context-menu"]');
      if (trigger) trigger.click();
    });
  });

  var dialog = document.querySelector("[data-location-dialog]");
  var form = document.querySelector("[data-location-form]");
  var labelInput = document.querySelector("[data-location-label]");
  var status = document.querySelector("[data-location-status]");
  var coordinateGroup = document.querySelector("[data-location-coordinates]");
  var latitudeOutput = document.querySelector("[data-location-latitude]");
  var longitudeOutput = document.querySelector("[data-location-longitude]");
  var draftLocation = null;

  function showCoordinates(location) {
    var hasCoordinates = Number.isFinite(location.latitude) && Number.isFinite(location.longitude);
    coordinateGroup.hidden = !hasCoordinates;
    latitudeOutput.textContent = hasCoordinates ? location.latitude.toFixed(6) : "";
    longitudeOutput.textContent = hasCoordinates ? location.longitude.toFixed(6) : "";
  }

  function openLocationDialog() {
    if (!dialog || !form) return;
    closeGardenMenu();
    draftLocation = Object.assign({}, storedLocation(activeGarden));
    labelInput.value = draftLocation.address_label || "";
    status.textContent = draftLocation.source === "temporary_fallback"
      ? "Weather currently uses the temporary fallback coordinates."
      : "Changes remain in this browser session until the garden API is connected.";
    showCoordinates(draftLocation);
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  document.querySelectorAll("[data-location-dialog-open]").forEach(function (button) {
    button.addEventListener("click", openLocationDialog);
  });

  document.querySelectorAll("[data-location-dialog-close]").forEach(function (button) {
    button.addEventListener("click", function () { if (dialog) dialog.close(); });
  });

  if (labelInput) {
    labelInput.addEventListener("input", function () {
      if (!draftLocation) return;
      draftLocation.address_label = labelInput.value.trim();
      if (draftLocation.source !== "manual_unresolved") {
        draftLocation.latitude = null;
        draftLocation.longitude = null;
        draftLocation.source = "manual_unresolved";
        showCoordinates(draftLocation);
        status.textContent = "Address coordinates will be resolved when backend geocoding is connected.";
      }
    });
  }

  var geolocate = document.querySelector("[data-use-device-location]");
  if (geolocate) {
    geolocate.addEventListener("click", function () {
      if (!navigator.geolocation) {
        status.textContent = "This browser does not provide device location.";
        return;
      }
      geolocate.disabled = true;
      status.textContent = "Requesting your location\u2026";
      navigator.geolocation.getCurrentPosition(function (position) {
        draftLocation = {
          address_label: "Current location",
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
          source: "browser_geolocation",
          persisted: false
        };
        labelInput.value = draftLocation.address_label;
        showCoordinates(draftLocation);
        status.textContent = "Coordinates are ready. Save to use them for this browser session.";
        geolocate.disabled = false;
      }, function (error) {
        status.textContent = error.code === error.PERMISSION_DENIED
          ? "Location permission was denied. You can enter a location manually instead."
          : "Your location could not be determined. Try manual entry instead.";
        geolocate.disabled = false;
      }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
    });
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var label = labelInput.value.trim();
      if (!label) {
        status.textContent = "Enter a location label or use your current location.";
        labelInput.focus();
        return;
      }
      draftLocation = Object.assign({}, draftLocation || {}, {
        address_label: label,
        persisted: false
      });
      if (!Number.isFinite(draftLocation.latitude) || !Number.isFinite(draftLocation.longitude)) {
        draftLocation.latitude = null;
        draftLocation.longitude = null;
        draftLocation.source = "manual_unresolved";
      }
      writeSession(locationStoragePrefix + activeGarden.id, JSON.stringify(draftLocation));
      updateInterface();
      dialog.close();
      window.dispatchEvent(new CustomEvent("gardenhub:gardenlocationchange", {
        detail: { garden: activeGarden, location: draftLocation, persistence: "browser_session_only" }
      }));
    });
  }

  updateInterface();
})();
