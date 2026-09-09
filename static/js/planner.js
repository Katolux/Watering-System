(function () {
  "use strict";

  var planner = document.querySelector("[data-planner]");
  if (!planner) return;

  var DEFAULT_PIXELS_PER_METRE = 40;
  var METRES_PER_FOOT = 0.3048;
  var METRES_PER_INCH = 0.0254;
  var MIN_ZOOM = 0.1;
  var MAX_ZOOM = 4;
  var ZOOM_STEPS = [0.1, 0.15, 0.2, 0.25, 0.33, 0.4, 0.5, 0.67, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 3.5, 4];
  var PLANT_SPACE_TINTS = ["101,139,83", "91,139,124", "131,126,160", "155,132,76", "160,113,92", "95,128,157"];
  var MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var currentMonth = new Date().getMonth() + 1;
  var catalog = parseJSON("[data-planner-catalog]", []);
  var initialState = parseJSON("[data-planner-state]", { garden: { width: 24, height: 16 }, objects: [] });
  var demoObjects = clone(initialState.objects || []);
  var plants = {};
  catalog.forEach(function (plant) { plants[plant.plant_id] = plant; });

  var state = {
    garden: clone(initialState.garden || { name: "My Garden", width: 10, height: 8, units: "m", north: 0 }),
    objects: initialState.planExists ? clone(initialState.objects || []) : [],
    hasPlan: Boolean(initialState.planExists),
    activeView: "plan",
    plantFilters: [],
    selectedId: null,
    shapeEditId: null,
    mode: "select",
    workingMode: "garden",
    basePixelsPerMetre: DEFAULT_PIXELS_PER_METRE,
    zoomMultiplier: 1,
    fittedViewportWidth: 0,
    fittedViewportHeight: 0,
    viewportResizePending: false,
    northLocked: initialState.garden && initialState.garden.northLocked !== false,
    panelCollapsed: { library: false, inspector: false },
    hiddenLayers: { sensors: true, labels: true },
    undo: [],
    redo: [],
    dirty: false,
    saving: false,
    saveError: false,
    savedSignature: null,
    idCounter: Date.now()
  };

  var stage = planner.querySelector("[data-planner-stage]");
  var viewport = planner.querySelector("[data-planner-viewport]");
  var objectLayer = planner.querySelector("[data-planner-objects]");
  var measure = planner.querySelector("[data-measure]");
  var interaction = null;
  var draggedAsset = null;
  var toastTimer = null;

  recalculatePlantQuantities(state.objects);
  ensureZOrder();
  state.savedSignature = state.hasPlan ? planSignature() : null;
  updateGardenCanvas();

  function parseJSON(selector, fallback) {
    var node = planner.querySelector(selector);
    if (!node) return fallback;
    try { return JSON.parse(node.textContent); } catch (error) { return fallback; }
  }

  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function round(value, places) {
    var factor = Math.pow(10, places || 2);
    return Math.round(value * factor) / factor;
  }
  function clamp(value, minimum, maximum) { return Math.max(minimum, Math.min(maximum, value)); }
  function renderScale() { return state.basePixelsPerMetre * state.zoomMultiplier; }
  function selected() { return state.objects.find(function (item) { return item.id === state.selectedId; }) || null; }
  function nextId(prefix) { state.idCounter += 1; return prefix + "-" + state.idCounter; }
  function assetURL(plant) { return planner.dataset.staticRoot + plant.asset_path; }
  function isImperial() { return state.garden.measurement === "imperial" || state.garden.units === "ft"; }
  function unitAbbreviation() { return isImperial() ? "ft" : "m"; }
  function toDisplayUnits(metres) { return isImperial() ? metres / METRES_PER_FOOT : metres; }
  function fromDisplayUnits(value) { return isImperial() ? value * METRES_PER_FOOT : value; }
  function formatLength(metres, compact) {
    if (isImperial()) {
      var inches = Math.max(0, Math.round(metres / METRES_PER_INCH));
      if (inches < 12) return inches + " in";
      var feet = Math.floor(inches / 12);
      var remainder = inches % 12;
      return feet + " ft" + (remainder ? " " + remainder + " in" : "");
    }
    if (compact && metres < 1) return Math.round(metres * 100) + " cm";
    return round(metres, 2).toFixed(metres < 10 ? 2 : 1).replace(/\.0+$/, "").replace(/(\.\d)0$/, "$1") + " m";
  }
  function formatDimensions(item) {
    if (geometryType(item) === "path") {
    return formatLength(shapePathLength(item), true) + " path";
    }
    if (isLinear(item)) return formatLength(item.width, true);
    if (item.variant === "round-pot") return "Ø " + formatLength(item.width, true);
    return formatLength(item.width, true) + " × " + formatLength(item.height, true);
  }
  function monthLabel(event) {
    var months = event && Array.isArray(event.months) ? event.months : [];
    if (!months.length) return "Not recorded";
    if (months.length === 1) return MONTH_NAMES[months[0]];
    var consecutive = months.every(function (month, index) { return index === 0 || month === months[index - 1] + 1; });
    return consecutive ? MONTH_NAMES[months[0]] + "–" + MONTH_NAMES[months[months.length - 1]] : months.map(function (month) { return MONTH_NAMES[month]; }).join(", ");
  }
  function updateStageGeometry() {
    var pixelsPerMetre = state.basePixelsPerMetre;
    stage.style.width = (state.garden.width * pixelsPerMetre) + "px";
    stage.style.height = (state.garden.height * pixelsPerMetre) + "px";
    stage.style.setProperty("--planner-pixels-per-metre", pixelsPerMetre + "px");
    var major = (isImperial() ? METRES_PER_FOOT : 1) * pixelsPerMetre;
    var minor = (isImperial() ? METRES_PER_INCH * 3 : 0.25) * pixelsPerMetre;
    stage.style.setProperty("--planner-grid-major", major + "px");
    stage.style.setProperty("--planner-grid-minor", minor + "px");
  }
  function updateGardenCanvas() {
    updateStageGeometry();
    planner.querySelector("[data-ruler-unit]").textContent = unitAbbreviation();
    planner.querySelector("[data-garden-name]").textContent = state.garden.name;
    planner.querySelector("[data-garden-summary]").textContent = formatLength(state.garden.width) + " × " + formatLength(state.garden.height) + " working area";
    var compass = planner.querySelector("[data-compass]");
    var north = normalizeAngle(state.garden.north || 0);
    state.garden.north = north;
    compass.style.setProperty("--north-rotation", north + "deg");
    compass.classList.toggle("is-unlocked", !state.northLocked);
    compass.querySelector("[data-north-angle]").value = normalizeAngle(Math.round(north)) + "°";
    var lock = compass.querySelector("[data-north-lock]");
    lock.setAttribute("aria-pressed", state.northLocked ? "true" : "false");
    lock.textContent = state.northLocked ? "Locked" : "Unlocked";
    lock.title = state.northLocked ? "Unlock north orientation" : "Lock north orientation";
  }
  function normalizeAngle(angle) { return ((angle % 360) + 360) % 360; }
  function signedAngleDelta(from, to) { return ((to - from + 540) % 360) - 180; }
  function geometryType(item) {
    return item && item.geometryType || "rect";
  }

  function hasEditableGeometry(item) {
    return geometryType(item) === "area" || geometryType(item) === "path";
  }

  function isShapeEditing(item) {
    return Boolean(
      item &&
      !item.locked &&
      hasEditableGeometry(item) &&
      state.shapeEditId === item.id &&
      state.selectedId === item.id &&
      state.mode === "select" &&
      state.activeView === "plan" &&
      !state.hiddenLayers[item.layer]
    );
  }

  function initialShapePoints(type) {
    return type === "area"
      ? [{ x: 0, y: 0 }, { x: 1, y: 0 },
         { x: 1, y: 1 }, { x: 0, y: 1 }]
      : [{ x: 0, y: 0.5 }, { x: 1, y: 0.5 }];
  }

  function validShape(item) {
    var points = item.points;
    var minimum = geometryType(item) === "area" ? 3 : 2;
    if (!Array.isArray(points) ||
        points.length < minimum || points.length > 128) return false;

    if (!points.every(function (point) {
      return point &&
        Number.isFinite(point.x) && Number.isFinite(point.y) &&
        point.x >= 0 && point.x <= 1 &&
        point.y >= 0 && point.y <= 1;
    })) return false;

    if (geometryType(item) === "path") {
      return points.some(function (point) {
        return point.x !== points[0].x || point.y !== points[0].y;
      });
    }

    var twiceArea = points.reduce(function (sum, point, index) {
      var next = points[(index + 1) % points.length];
      return sum + point.x * next.y - next.x * point.y;
    }, 0);
    return Math.abs(twiceArea) > 1e-8;
  }

  function shapePathLength(item) {
    return item.points.reduce(function (length, point, index, points) {
      if (!index) return length;
      return length + Math.hypot(
        (point.x - points[index - 1].x) * item.width,
        (point.y - points[index - 1].y) * item.height
      );
    }, 0);
  }

  function shapeMarkup(item) {
    var tag = geometryType(item) === "area" ? "polygon" : "polyline";
    var points = item.points.map(function (point) {
      return point.x + "," + point.y;
    }).join(" ");

    return '<svg class="planner-shape" viewBox="0 0 1 1" ' +
      'preserveAspectRatio="none" aria-hidden="true">' +
      '<' + tag + ' points="' + points + '" /></svg>';
  }

  function shapeHandlesMarkup(item) {
    function button(point, attribute, index, label, text) {
      return '<button type="button" class="planner-shape-node' +
        (attribute === "data-shape-edge" ? " is-insert" : "") +
        '" ' + attribute + '="' + index +
        '" style="left:' + (point.x * 100) +
        '%;top:' + (point.y * 100) +
        '%" aria-label="' + label + '">' + text + '</button>';
    }

    var markup = item.points.map(function (point, index) {
      return button(point, "data-shape-node", index,
        "Move vertex " + (index + 1), "");
    }).join("");

    var edgeCount = geometryType(item) === "area"
      ? item.points.length : item.points.length - 1;

    if (item.points.length < 128) {
      for (var index = 0; index < edgeCount; index += 1) {
        var first = item.points[index];
        var next = item.points[(index + 1) % item.points.length];
        markup += button(
          { x: (first.x + next.x) / 2, y: (first.y + next.y) / 2 },
          "data-shape-edge", index,
          "Insert vertex after vertex " + (index + 1), "+"
        );
      }
    }
    return markup;
  }

  function insertShapePoint(item, edgeIndex) {
    var edgeCount = geometryType(item) === "area"
      ? item.points.length : item.points.length - 1;
    if (!Number.isInteger(edgeIndex) ||
        edgeIndex < 0 || edgeIndex >= edgeCount ||
        item.points.length >= 128) return -1;

    var first = item.points[edgeIndex];
    var next = item.points[(edgeIndex + 1) % item.points.length];
    item.points.splice(edgeIndex + 1, 0, {
      x: round((first.x + next.x) / 2, 4),
      y: round((first.y + next.y) / 2, 4)
    });
    return edgeIndex + 1;
  }
  function isLinear(item) {
    if (hasEditableGeometry(item)) return false;
    return Boolean(item && ((item.kind === "irrigation" && item.variant !== "dripper") || (item.kind === "structure" && (item.variant === "fence" || item.variant === "hedge"))));
  }
  function defaultZBase(layer) {
    return { surfaces: 100, paths: 200, beds: 300, irrigation: 400, structures: 500, plants: 600 }[layer] || 250;
  }
  function ensureZOrder() {
    state.objects.forEach(function (item, index) {
      item.z = Number.isFinite(item.z) ? Math.round(item.z) : defaultZBase(item.layer) + index;
    });
  }
  function nextZForLayer(layer) {
    var base = defaultZBase(layer);
    var layerValues = state.objects.filter(function (item) { return item.layer === layer && item.z >= base && item.z < base + 100; }).map(function (item) { return item.z; });
    return layerValues.length ? Math.min(base + 99, Math.max.apply(Math, layerValues) + 1) : base;
  }
  function orderedObjects() {
    return state.objects.slice().sort(function (left, right) {
      if (left.z === right.z) return state.objects.indexOf(left) - state.objects.indexOf(right);
      return left.z - right.z;
    });
  }

  function serializedPlan() {
    return {
      version: 1,
      garden: clone(state.garden),
      objects: state.objects.map(function (item) {
        var serialized = clone(item);
        if (item.kind === "plant" && plants[item.plantId]) serialized.quantity = plantGrid(item).cells;
        return serialized;
      })
    };
  }

  function planSignature() {
    return JSON.stringify(serializedPlan());
  }

  function refreshDirtyState() {
    state.saveError = false;
    state.dirty = state.hasPlan && (state.savedSignature === null || planSignature() !== state.savedSignature);
  }

  function snapshot() { return JSON.stringify(state.objects); }
  function beginChange() { return snapshot(); }
  function finishChange(before) {
    var after = snapshot();
    if (before === after) return;
    state.undo.push(before);
    if (state.undo.length > 60) state.undo.shift();
    state.redo = [];
    refreshDirtyState();
    updateHistoryControls();
    updateSaveState();
  }

  function restore(serialized) {
    state.shapeEditId = null;
    state.objects = JSON.parse(serialized);
    recalculatePlantQuantities(state.objects);
    ensureZOrder();
    if (!selected()) state.selectedId = null;
    render();
  }

  function undo() {
    if (!state.undo.length) return;
    state.redo.push(snapshot());
    restore(state.undo.pop());
    refreshDirtyState();
    updateHistoryControls();
    updateSaveState();
  }

  function redo() {
    if (!state.redo.length) return;
    state.undo.push(snapshot());
    restore(state.redo.pop());
    refreshDirtyState();
    updateHistoryControls();
    updateSaveState();
  }

  function updateHistoryControls() {
    planner.querySelectorAll('[data-action="undo"]').forEach(function (button) { button.disabled = !state.undo.length; });
    planner.querySelectorAll('[data-action="redo"]').forEach(function (button) { button.disabled = !state.redo.length; });
  }

  function updateSaveState() {
    var label = planner.querySelector("[data-save-state]");
    var saveButton = planner.querySelector("[data-save-plan]");
    if (saveButton) saveButton.disabled = state.saving || !state.hasPlan || !state.dirty;
    if (!label) return;
    label.classList.toggle("is-dirty", state.dirty);
    label.classList.toggle("is-saved", state.hasPlan && !state.dirty && !state.saving && !state.saveError);
    label.classList.toggle("is-saving", state.saving);
    label.classList.toggle("is-error", state.saveError);
    var text = !state.hasPlan ? " No saved plan" : state.saving ? " Saving…" : state.saveError ? " Save failed" : state.dirty ? " Unsaved changes" : " Saved";
    label.lastChild.nodeValue = text;
  }

  async function savePlan() {
    if (!state.hasPlan || state.saving || !state.dirty) return;
    var payload = serializedPlan();
    var savingSignature = JSON.stringify(payload);
    state.saving = true;
    state.saveError = false;
    updateSaveState();
    try {
      var response = await fetch(planner.dataset.saveUrl, {
        method: "PUT",
        headers: { "Accept": "application/json", "Content-Type": "application/json" },
        body: savingSignature
      });
      var result = await response.json().catch(function () { return {}; });
      if (!response.ok || !result.ok) throw new Error(result.error || "The Planner layout could not be saved.");
      state.savedSignature = savingSignature;
      state.saveError = false;
      state.dirty = planSignature() !== state.savedSignature;
      toast(state.dirty ? "Plan saved; newer changes are still unsaved" : "Plan saved");
    } catch (error) {
      state.saveError = true;
      state.dirty = true;
      toast(error.message || "The Planner layout could not be saved.");
    } finally {
      state.saving = false;
      updateSaveState();
    }
  }

  function plantGrid(item) {
    var plant = plants[item.plantId];
    if (!plant) {
      var savedQuantity = Number.isInteger(item.quantity) && item.quantity > 0 ? item.quantity : null;
      return { available: false, spacingX: null, spacingY: null, hasSpacingX: false, hasSpacingY: false, columns: 1, rows: 1, cells: null, quantity: savedQuantity };
    }
    var hasSpacingX = Number.isFinite(plant.spacing_in_row_cm) && plant.spacing_in_row_cm > 0;
    var hasSpacingY = Number.isFinite(plant.spacing_between_rows_cm) && plant.spacing_between_rows_cm > 0;
    var spacingX = hasSpacingX ? Math.max(plant.spacing_in_row_cm / 100, 0.1) : 0.5;
    var spacingY = hasSpacingY ? Math.max(plant.spacing_between_rows_cm / 100, 0.1) : 0.5;
    var columns = hasSpacingX ? Math.max(1, Math.floor((item.width + 0.015) / spacingX)) : 1;
    var rows = hasSpacingY ? Math.max(1, Math.floor((item.height + 0.015) / spacingY)) : 1;
    var cells = columns * rows;
    return { available: true, spacingX: spacingX, spacingY: spacingY, hasSpacingX: hasSpacingX, hasSpacingY: hasSpacingY, columns: columns, rows: rows, cells: cells, quantity: cells };
  }

  function recalculatePlantQuantity(item) {
    if (item.kind !== "plant" || !plants[item.plantId]) return;
    item.quantity = plantGrid(item).cells;
  }

  function recalculatePlantQuantities(items) {
    items.forEach(recalculatePlantQuantity);
  }

  function plantSpaceTint(item) {
    var key = String(item.plantId || item.id || "plant");
    var hash = 0;
    for (var index = 0; index < key.length; index += 1) hash = ((hash * 31) + key.charCodeAt(index)) >>> 0;
    return PLANT_SPACE_TINTS[hash % PLANT_SPACE_TINTS.length];
  }

  function objectMarkup(item) {
    if (hasEditableGeometry(item)) return shapeMarkup(item);
    if (item.kind === "plant") return plantMarkup(item);
    if (item.kind === "bed") return bedMarkup(item);
    if (item.kind === "surface") return '<span class="planner-object__visual planner-surface--' + item.variant + '"></span>';
    if (item.kind === "irrigation") {
      if (item.variant === "dripper") return '<span class="planner-object__visual planner-dripper"></span>';
      return '<span class="planner-object__visual planner-line planner-line--' + item.variant + '"></span>';
    }
    if (item.kind === "structure") {
      if (item.variant === "fence" || item.variant === "hedge") return '<span class="planner-object__visual planner-boundary--' + item.variant + '"></span>';
      if (item.variant === "greenhouse") return bedMarkup(Object.assign({}, item, { variant: "greenhouse" }));
      return structureMarkup("structure");
    }
    return structureMarkup(item.variant);
  }

  function svgObjectMarkup(viewBox, content) {
    return '<span class="planner-object__visual"><svg viewBox="' + viewBox + '" preserveAspectRatio="none" aria-hidden="true">' + content + '</svg></span>';
  }

  function bedMarkup(item) {
    var variant = item.variant || "raised-bed";
    if (variant === "round-pot") {
      return svgObjectMarkup("0 0 100 100", '<ellipse cx="50" cy="50" rx="47.5" ry="47.5" fill="#9b6957" stroke="#5d5146" stroke-width="2.5"/><ellipse cx="50" cy="50" rx="39" ry="39" fill="#9a8065" stroke="#c18a70" stroke-width="4"/><ellipse cx="50" cy="50" rx="31.5" ry="31.5" fill="#92785e"/><path d="M25 38c13-15 38-20 56-8" fill="none" stroke="#d5a18b" stroke-opacity=".58" stroke-width="2"/><path d="M30 67c15 9 35 10 49 0" fill="none" stroke="#695b4c" stroke-opacity=".24" stroke-width="1.5"/>');
    }
    if (variant === "greenhouse") {
      return svgObjectMarkup("0 0 120 70", '<rect x="2" y="2" width="116" height="66" rx="8" fill="#dfe8e2" fill-opacity=".8" stroke="#596a61" stroke-width="2.2"/><path d="M31 3v64M60 3v64M89 3v64M3 35h114" fill="none" stroke="#82978b" stroke-width="1.5"/><path d="M7 32L31 7l29 25L89 7l24 25M7 38l24 25 29-25 29 25 24-25" fill="none" stroke="#f7faf8" stroke-opacity=".66" stroke-width="1.3"/><path d="M60 4v62" fill="none" stroke="#65786e" stroke-width="2"/><rect x="102" y="25" width="15" height="20" rx="1.5" fill="#eef4f0" fill-opacity=".72" stroke="#65786e" stroke-width="1.5"/><path d="M102 35h15" stroke="#8ea197" stroke-width="1"/>');
    }
    if (variant === "ground-bed") {
      return svgObjectMarkup("0 0 120 70", '<rect x="2" y="2" width="116" height="66" rx="5" fill="#a68f70" stroke="#6d6855" stroke-width="2"/><rect x="7" y="7" width="106" height="56" rx="3" fill="#a99170" stroke="#c0ad8c" stroke-opacity=".55" stroke-width="1"/><path d="M7 17V7h12M101 7h12v10M7 53v10h12M101 63h12V53" fill="none" stroke="#e0ceb0" stroke-opacity=".62" stroke-width="1.3"/><path d="M12 21c24-3 72 3 96 0M12 35c24 3 72-3 96 0M12 49c24-3 72 3 96 0" fill="none" stroke="#76644f" stroke-opacity=".42" stroke-width="1.2"/>');
    }
    var isMetal = variant === "large-container";
    var isTerracotta = variant === "planter";
    var frameColor = isMetal ? "#7f8d89" : isTerracotta ? "#9a6755" : "#84694e";
    var edgeColor = isMetal ? "#52625e" : isTerracotta ? "#644f46" : "#5f5144";
    var rimColor = isMetal ? "#aeb9b4" : isTerracotta ? "#bd8770" : "#ad895f";
    var soilColor = isTerracotta ? "#96775e" : "#9b8061";
    var radius = isMetal ? "7" : isTerracotta ? "5" : "3";
    var materialDetail = isMetal
      ? '<path d="M7 15h106M7 55h106" stroke="#d8dfda" stroke-opacity=".5" stroke-width="1.2"/><circle cx="8" cy="8" r="2" fill="#d7dfda"/><circle cx="112" cy="8" r="2" fill="#d7dfda"/>'
      : '<path d="M5 17h110M5 53h110M19 5v60M101 5v60" fill="none" stroke="#d0ab7c" stroke-opacity=".38" stroke-width="1.2"/>';
    return svgObjectMarkup("0 0 120 70", '<rect x="2" y="2" width="116" height="66" rx="' + radius + '" fill="' + frameColor + '" stroke="' + edgeColor + '" stroke-width="2.2"/><rect x="10" y="10" width="100" height="50" rx="' + (isMetal ? "4" : "2") + '" fill="' + soilColor + '" stroke="' + rimColor + '" stroke-width="2.5"/>' + materialDetail + '<path d="M17 26c25-3 61 3 86 0M17 43c25 3 61-3 86 0" fill="none" stroke="#715f4b" stroke-opacity=".38" stroke-width="1.1"/>');
  }

  function structureMarkup(variant) {
    if (variant === "tree") {
      return svgObjectMarkup("0 0 100 100", '<path d="M50 3c9 0 15 6 19 13 9-3 18 1 22 9 4 8 1 16-4 22 7 7 7 17 2 25-5 8-13 11-22 9-4 10-13 16-23 14-8-1-13-7-15-14-10 2-19-3-22-12-3-8 1-16 7-21-5-8-3-18 4-24 6-6 14-7 22-4C35 9 41 3 50 3Z" fill="#738e62" stroke="#4f6250" stroke-width="2.2"/><path d="M23 43c7-15 21-23 37-20 13 2 23 11 27 24-10-7-18-5-24 2-9-9-19-10-28-3-5 4-8 9-9 15-5-4-6-11-3-18Z" fill="#91a977" fill-opacity=".72"/><path d="M35 76c8-8 18-10 27-5 6 3 10 2 16-2-6 13-21 19-34 13" fill="#5f7b57" fill-opacity=".78"/><circle cx="51" cy="52" r="5" fill="#59624f" fill-opacity=".55"/>');
    }
    if (variant === "water-tank") {
      return svgObjectMarkup("0 0 100 100", '<ellipse cx="50" cy="50" rx="46" ry="47" fill="#849ca4" stroke="#53666a" stroke-width="2.4"/><ellipse cx="50" cy="50" rx="37" ry="38" fill="#9db0b5" stroke="#c4d0d0" stroke-width="2"/><ellipse cx="50" cy="50" rx="26" ry="27" fill="#91a7ac" stroke="#6e858a" stroke-width="1.3"/><path d="M18 35c18-12 48-14 65-1" fill="none" stroke="#d8e1df" stroke-opacity=".62" stroke-width="1.7"/><circle cx="50" cy="50" r="7" fill="#657a7e" stroke="#d4ddda" stroke-width="1.5"/>');
    }
    if (variant === "structure") {
      return svgObjectMarkup("0 0 120 70", '<rect x="2" y="2" width="116" height="66" rx="3" fill="#aaa28f" stroke="#5f625a" stroke-width="2.2"/><rect x="9" y="9" width="102" height="52" rx="1" fill="#bbb29d" stroke="#756f62" stroke-width="1.5"/><path d="M23 10v50M42 10v50M61 10v50M80 10v50M99 10v50" stroke="#81796a" stroke-opacity=".62" stroke-width="1.2"/><path d="M10 19h100M10 51h100" stroke="#e0d9ca" stroke-opacity=".68" stroke-width="1.3"/><rect x="4" y="4" width="9" height="9" rx="1" fill="#65665e"/><rect x="107" y="4" width="9" height="9" rx="1" fill="#65665e"/><rect x="4" y="57" width="9" height="9" rx="1" fill="#65665e"/><rect x="107" y="57" width="9" height="9" rx="1" fill="#65665e"/>');
    }
    return svgObjectMarkup("0 0 100 100", '<rect x="3" y="3" width="94" height="94" rx="5" fill="#aeb2ac" stroke="#5d645f" stroke-width="2.2"/><rect x="11" y="11" width="78" height="78" rx="3" fill="#c3c6c0" stroke="#858b85" stroke-width="1.5"/><path d="M18 50h64M50 18v64" stroke="#8a908a" stroke-width="1.3"/><circle cx="50" cy="50" r="7" fill="#737b76"/>');
  }

  function plantMarkup(item) {
    var plant = plants[item.plantId];
    if (!plant) {
      return '<span class="planner-plant-unavailable"><span aria-hidden="true">?</span><strong>Plant unavailable</strong></span>';
    }
    var grid = plantGrid(item);
    var instances = "";
    for (var index = 0; index < grid.quantity; index += 1) {
      instances += '<span class="planner-plant-instance"><span class="planner-plant-instance__halo" aria-hidden="true"></span><img src="' + assetURL(plant) + '" alt="" draggable="false"><span class="planner-plant-placeholder" hidden>' + escapeHTML((plant.name || "Plant").slice(0, 2).toUpperCase()) + '</span></span>';
    }
    return '<span class="planner-plant-halo" aria-hidden="true"></span><span class="planner-plant-instances" style="--plant-columns:' + grid.columns + ';--plant-rows:' + grid.rows + '">' + instances + '</span>';
  }

  function escapeHTML(value) {
    return String(value).replace(/[&<>'"]/g, function (character) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]; });
  }

  function renderObjects() {
    if (state.shapeEditId && !isShapeEditing(selected())) {
      state.shapeEditId = null;
    }
    objectLayer.innerHTML = "";
    orderedObjects().forEach(function (item) {
      if (state.hiddenLayers[item.layer]) return;
      var element = document.createElement("div");
      element.className = "planner-object planner-object--" + item.kind;
      element.classList.toggle("is-locked", Boolean(item.locked));
      element.title = item.locked
        ? item.name + " — locked. Double-click to select and unlock."
        : item.name;
      if (item.kind === "plant" && !plants[item.plantId]) element.classList.add("is-unavailable");
      if (isLinear(item)) element.classList.add("is-linear");
      if (item.kind === "plant" && plantGrid(item).cells > 1) element.classList.add("is-block");
      element.dataset.objectId = item.id;
      element.dataset.kind = item.kind;
      element.dataset.layer = item.layer;
      element.setAttribute("role", "button");
      element.setAttribute("aria-pressed", item.id === state.selectedId ? "true" : "false");
      element.setAttribute("tabindex", item.id === state.selectedId ? "0" : "-1");
      var plantDetail = item.kind === "plant" ? plantGrid(item) : null;
      element.setAttribute("aria-label", item.name + (plantDetail ? (plantDetail.available ? ", " + plantDetail.quantity + " plants" : ", plant unavailable") : ""));
      applyObjectGeometry(element, item, item.z);
      element.innerHTML = objectMarkup(item) + '<span class="planner-object__label"></span>';
      element.querySelector(".planner-object__label").textContent = item.name;
      element.querySelectorAll("img").forEach(setImageFallback);
      objectLayer.appendChild(element);
    });
    var item = selected();
    if (!item || state.hiddenLayers[item.layer]) return;
    var overlay = document.createElement("div");
    overlay.className = "planner-object planner-object--" + item.kind + " planner-selection-overlay is-selected";
    overlay.classList.toggle("is-locked", Boolean(item.locked));
    if (item.kind === "plant" && !plants[item.plantId]) overlay.classList.add("is-unavailable");
    if (isLinear(item)) overlay.classList.add("is-linear");
    if (item.kind === "plant" && plantGrid(item).cells > 1) overlay.classList.add("is-block");
    if (interaction && interaction.item && interaction.item.id === item.id && ["move", "resize", "rotate"].indexOf(interaction.type) !== -1) {
      overlay.classList.add("is-editing");
      if (interaction.type === "rotate") overlay.classList.add("is-rotating");
    }
    overlay.dataset.objectId = item.id;
    overlay.dataset.kind = item.kind;
    overlay.dataset.layer = item.layer;
    overlay.setAttribute("role", "group");
    overlay.setAttribute("aria-label", item.name + " editing controls");
    applyObjectGeometry(overlay, item, 10000);
    overlay.innerHTML = (item.kind === "plant" ? '<span class="planner-object__label">' + escapeHTML(item.name) + '</span>' : '') + '<span class="planner-live-label">' + liveLabelMarkup(item) + '</span>' + handlesMarkup(item);
    objectLayer.appendChild(overlay);
  }

  function applyObjectGeometry(element, item, zIndex) {
    element.dataset.geometryType = geometryType(item);
    element.dataset.variant = item.variant || "";
    element.style.setProperty("--object-x", item.x);
    element.style.setProperty("--object-y", item.y);
    element.style.setProperty("--object-width", item.width);
    element.style.setProperty("--object-height", item.height);
    element.style.setProperty("--object-rotation", item.rotation || 0);
    element.style.setProperty("--object-counter-rotation", (-(item.rotation || 0)) + "deg");
    if (item.kind === "plant") element.style.setProperty("--plant-space-rgb", plantSpaceTint(item));
    element.style.zIndex = zIndex;
  }

  function liveLabelMarkup(item) {
    var title = item.name;
    var grid = item.kind === "plant" ? plantGrid(item) : null;
    var detail = grid ? (grid.available ? grid.quantity + " plants · " + formatLength(grid.spacingX, true) + " spacing" : "Plant unavailable") : formatDimensions(item);
    if (interaction && interaction.item && interaction.item.id === item.id) {
      if (interaction.type === "rotate") {
        title = "Rotation";
        detail = Math.round(item.rotation || 0) + "°" + (interaction.snapActive ? " · 15° snap" : " · Shift to snap");
      } else if (interaction.type === "resize") {
        title = item.kind === "plant" ? "Planting footprint" : "Dimensions";
        detail = formatDimensions(item);
      } else if (interaction.type === "move") {
        title = "Position";
        detail = formatLength(item.x, true) + " × " + formatLength(item.y, true);
      }
    }
    return '<strong>' + escapeHTML(title) + '</strong><span>' + escapeHTML(detail) + '</span>';
  }

  function handlesMarkup(item) {
    if (item.locked) return "";
    if (isShapeEditing(item)) return shapeHandlesMarkup(item);
    var horizontal = '<button class="planner-resize-handle" data-handle="e" aria-label="Extend length from end"></button><button class="planner-resize-handle" data-handle="w" aria-label="Extend length from start"></button>';
    var area = '<button class="planner-resize-handle" data-handle="nw" aria-label="Resize from top left"></button><button class="planner-resize-handle" data-handle="ne" aria-label="Resize from top right"></button><button class="planner-resize-handle" data-handle="se" aria-label="Resize from bottom right"></button><button class="planner-resize-handle" data-handle="sw" aria-label="Resize from bottom left"></button>';
    return (isLinear(item) ? horizontal : area) + '<button class="planner-rotation-handle" data-rotate-handle aria-label="Rotate"></button>';
  }

  function setImageFallback(image) {
    image.addEventListener("error", function () {
      image.hidden = true;
      var placeholder = image.nextElementSibling;
      if (placeholder) placeholder.hidden = false;
    }, { once: true });
  }

  function render() {
    renderObjects();
    updateInspector();
    updateSelectionControls();
    updateLayerClasses();
    renderCalendar();
    updateSaveState();
  }

  function renderCalendar() {
    var body = planner.querySelector("[data-calendar-body]");
    if (!body) return;
    var grouped = {};
    state.objects.filter(function (item) { return item.kind === "plant"; }).forEach(function (item) {
      var grid = plantGrid(item);
      if (!grouped[item.plantId]) grouped[item.plantId] = { plant: plants[item.plantId] || null, name: item.name || "Unknown plant", quantity: 0, quantityAvailable: true };
      if (grid.quantity === null) grouped[item.plantId].quantityAvailable = false;
      else grouped[item.plantId].quantity += grid.quantity;
    });
    var rows = Object.keys(grouped).map(function (plantId) { return grouped[plantId]; }).sort(function (left, right) {
      return (left.plant ? left.plant.name : left.name).localeCompare(right.plant ? right.plant.name : right.name);
    });
    body.innerHTML = "";
    rows.forEach(function (entry) {
      var calendar = entry.plant ? entry.plant.calendar || {} : {};
      var notes = [calendar.sow_indoors, calendar.sow_outdoors, calendar.transplant_out, calendar.harvest]
        .map(function (event) { return event && event.notes; }).filter(Boolean);
      var row = document.createElement("tr");
      var plantIdentity = entry.plant
        ? '<img src="' + assetURL(entry.plant) + '" alt=""><span><strong>' + escapeHTML(entry.plant.name) + '</strong><small>' + escapeHTML(entry.plant.scientific_name || "") + '</small></span>'
        : '<span class="planner-calendar__missing-symbol" aria-hidden="true">?</span><span><strong>' + escapeHTML(entry.name) + '</strong><small>Plant unavailable</small></span>';
      var unavailable = "Plant unavailable";
      row.innerHTML = '<th scope="row"><span class="planner-calendar__plant">' + plantIdentity + '</span></th>' +
        '<td data-label="Quantity">' + (entry.quantityAvailable ? entry.quantity : "Unavailable") + '</td>' +
        '<td data-label="Indoor sowing">' + escapeHTML(entry.plant ? monthLabel(calendar.sow_indoors) : unavailable) + '</td>' +
        '<td data-label="Outdoor sowing">' + escapeHTML(entry.plant ? monthLabel(calendar.sow_outdoors) : unavailable) + '</td>' +
        '<td data-label="Transplant">' + escapeHTML(entry.plant ? monthLabel(calendar.transplant_out) : unavailable) + '</td>' +
        '<td data-label="Harvest">' + escapeHTML(entry.plant ? monthLabel(calendar.harvest) : unavailable) + '</td>' +
        '<td data-label="Notes">' + escapeHTML(entry.plant ? (notes.length ? notes.join(" ") : "—") : unavailable) + '</td>';
      body.appendChild(row);
      row.querySelectorAll("img").forEach(setImageFallback);
    });
    planner.querySelector("[data-calendar-empty]").hidden = rows.length > 0;
    planner.querySelector("[data-calendar-table-wrap]").hidden = rows.length === 0;
    var greenhouse = initialState.greenhouse || {};
    planner.querySelector("[data-calendar-greenhouse]").textContent = greenhouse.rulesAvailable ? "Greenhouse timing rules active" : (greenhouse.message || "Season extension not yet implemented");
  }

  function selectObject(id, focus) {
    if (id !== state.selectedId) state.shapeEditId = null;
    state.selectedId = id;
    render();
    var item = selected();
    var status = planner.querySelector("[data-canvas-status]");
    status.textContent = item ? item.name + " selected" : "Select an object or add one from the library.";
    if (focus && id) {
      var element = objectLayer.querySelector('[data-object-id="' + CSS.escape(id) + '"]');
      if (element) element.focus({ preventScroll: true });
    }
    if (state.plantFilters.some(function (filter) { return filter.indexOf("relationship:") === 0; })) filterLibrary();
  }

  function updateSelectionControls() {
  var item = selected();

  planner.querySelectorAll('[data-action="duplicate"]').forEach(function (button) {
    button.disabled = !item;
  });

  planner.querySelectorAll('[data-action="delete"]').forEach(function (button) {
    button.disabled = !item || Boolean(item.locked);
  });

  planner.querySelectorAll('[data-action="toggle-lock"]').forEach(function (button) {
    button.disabled = !item;
    button.textContent = item && item.locked ? "Unlock" : "Lock";
    button.setAttribute("aria-pressed", item && item.locked ? "true" : "false");
  });
}

  function toggleSelectedLock() {
    var item = selected();
    if (!item || interaction) return;

    var before = beginChange();
    item.locked = !item.locked;
    finishChange(before);
    render();
    toast(item.name + (item.locked ? " locked" : " unlocked"));
  }

  function updateInspector() {
    var item = selected();
    var empty = planner.querySelector("[data-inspector-empty]");
    var form = planner.querySelector("[data-inspector-form]");
    var title = planner.querySelector("[data-inspector-title]");
    empty.hidden = Boolean(item);
    form.hidden = !item;
    title.textContent = item ? item.name : "Nothing selected";
    if (!item) return;

    form.querySelector("[data-shape-controls]").hidden =
      !hasEditableGeometry(item);

    var shapeButton = form.querySelector("[data-edit-shape]");
    shapeButton.disabled = Boolean(item.locked);
    shapeButton.textContent = isShapeEditing(item) ? "Done" : "Edit shape";
    shapeButton.setAttribute(
      "aria-pressed", isShapeEditing(item) ? "true" : "false"
    );
    form.querySelector("[data-inspector-name]").textContent = item.name;
    form.querySelector("[data-inspector-type]").textContent = typeLabel(item);
    form.querySelector('[data-field="name"]').value = item.name;
    form.querySelector('[data-field="width"]').value = round(toDisplayUnits(item.width), 2);
    form.querySelector('[data-field="height"]').value = round(toDisplayUnits(item.height), 2);
    form.querySelector('[data-field="length"]').value = round(toDisplayUnits(item.width), 2);
    form.querySelector('[data-field="rotation"]').value = Math.round(item.rotation || 0);
    form.querySelector("[data-rotation-output]").value = Math.round(item.rotation || 0) + "°";
    updateInspectorSymbol(item);

    var plantFields = form.querySelector("[data-plant-fields]");
    var companionFields = form.querySelector("[data-companion-fields]");
    var bedFields = form.querySelector("[data-bed-fields]");
    var greenhouseFields = form.querySelector("[data-greenhouse-fields]");
    var linear = isLinear(item);
    form.querySelector("[data-area-fields]").hidden = linear;
    form.querySelectorAll("[data-linear-fields]").forEach(function (field) { field.hidden = !linear; });
    form.querySelector('[data-field="length"]').min = round(toDisplayUnits(item.kind === "structure" ? 1 : 0.5), 2);
    form.querySelector("[data-width-label]").textContent = "Width (" + unitAbbreviation() + ")";
    form.querySelector("[data-height-label]").textContent = "Height (" + unitAbbreviation() + ")";
    form.querySelector("[data-length-label]").textContent = "Length (" + unitAbbreviation() + ")";
    if (hasEditableGeometry(item)) {
      form.querySelector("[data-width-label]").textContent =
        "Frame width (" + unitAbbreviation() + ")";
      form.querySelector("[data-height-label]").textContent =
        "Frame height (" + unitAbbreviation() + ")";
    }
    plantFields.hidden = item.kind !== "plant";
    companionFields.hidden = item.kind !== "plant";
    bedFields.hidden = item.kind !== "bed";
    greenhouseFields.hidden = item.variant !== "greenhouse";
    var geometrySection = form.querySelector("[data-geometry-section]");
    if (geometrySection.dataset.itemId !== item.id) {
      geometrySection.open = item.kind !== "plant";
      geometrySection.dataset.itemId = item.id;
    }
    if (item.kind === "plant") {
      var plant = plants[item.plantId];
      var grid = plantGrid(item);
      var calendar = plant ? plant.calendar || {} : {};
      form.querySelector("[data-inspector-type]").textContent = plant ? "Planting group" : "Planting group · Plant unavailable";
      form.querySelector("[data-plant-scientific]").textContent = plant ? (plant.scientific_name || "Scientific name not recorded") : "Plant unavailable";
      form.querySelector("[data-plant-quantity]").textContent = grid.quantity === null ? "Unavailable" : grid.quantity;
      form.querySelector("[data-plant-spacing-x]").textContent = grid.hasSpacingX ? formatLength(grid.spacingX, true) : "Not recorded";
      form.querySelector("[data-plant-spacing-y]").textContent = grid.hasSpacingY ? formatLength(grid.spacingY, true) : "Not recorded";
      form.querySelector("[data-plant-sow-indoors]").textContent = plant ? monthLabel(calendar.sow_indoors) : "Plant unavailable";
      form.querySelector("[data-plant-sow-outdoors]").textContent = plant ? monthLabel(calendar.sow_outdoors) : "Plant unavailable";
      form.querySelector("[data-plant-transplant]").textContent = plant ? monthLabel(calendar.transplant_out) : "Plant unavailable";
      form.querySelector("[data-plant-harvest]").textContent = plant ? monthLabel(calendar.harvest) : "Plant unavailable";
      form.querySelector("[data-plant-bed]").textContent = item.bedId || "Not assigned";
      var encyclopediaLink = form.querySelector("[data-plant-encyclopedia]");
      encyclopediaLink.hidden = !plant;
      if (plant) encyclopediaLink.href = plant.encyclopedia_path || ("/automation/plants/" + plant.plant_id);
      else encyclopediaLink.removeAttribute("href");
      form.querySelector("[data-plant-hint]").textContent = !plant
        ? "This saved plant reference is no longer in the catalogue. Its layout object and historical details are preserved."
        : grid.hasSpacingX || grid.hasSpacingY
        ? "Resize the planting group with its four handles. Growing space follows catalogue spacing on both axes; artwork stays proportional."
        : "Catalogue spacing is not recorded for this plant, so the prototype keeps it as one plant inside a visual footprint."
      renderCompanions(plant);
    }
    if (item.kind === "bed") {
      form.querySelector("[data-bed-record]").textContent = item.bedId || "Prototype object";
      form.querySelector("[data-bed-zone]").textContent = item.zoneName || "Not assigned";
    }
    updateStackInspector(item);
    form.querySelector("[data-lock-status]").hidden = !item.locked;

    form.querySelectorAll("[data-field], [data-orientation]").forEach(function (control) {
      control.disabled = Boolean(item.locked);
    });

    if (item.locked) {
      form.querySelectorAll("[data-stack-action]").forEach(function (button) {
        button.disabled = true;
      });
    }
    }

  function updateStackInspector(item) {
    var ordered = orderedObjects();
    var position = ordered.indexOf(item);
    planner.querySelector("[data-stack-position]").value = (position + 1) + " of " + ordered.length + " · " + layerLabel(item.layer);
    planner.querySelectorAll("[data-stack-action]").forEach(function (button) {
      var atBack = position === 0;
      var atFront = position === ordered.length - 1;
      button.disabled = (atBack && (button.dataset.stackAction === "back" || button.dataset.stackAction === "backward")) || (atFront && (button.dataset.stackAction === "front" || button.dataset.stackAction === "forward"));
    });
  }

  function layerLabel(layer) {
    return { surfaces: "Surfaces", paths: "Paths & ground areas", beds: "Beds & containers", irrigation: "Irrigation", structures: "Structures", plants: "Plants" }[layer] || "Objects";
  }

  function typeLabel(item) {
    if (item.kind === "plant") return "Planting group";
    if (item.kind === "bed") return item.bedId ? "Linked bed" : "Bed / container";
    return item.kind.charAt(0).toUpperCase() + item.kind.slice(1);
  }

  function updateInspectorSymbol(item) {
    var symbol = planner.querySelector("[data-inspector-symbol]");
    symbol.innerHTML = "";
    if (item.kind === "plant") {
      var plant = plants[item.plantId];
      if (!plant) {
        var missing = document.createElement("span");
        missing.className = "planner-plant-placeholder planner-plant-placeholder--missing";
        missing.textContent = "?";
        missing.title = "Plant unavailable";
        symbol.appendChild(missing);
        return;
      }
      var image = document.createElement("img");
      image.src = assetURL(plant);
      image.alt = "";
      var placeholder = document.createElement("span");
      placeholder.className = "planner-plant-placeholder";
      placeholder.textContent = item.name.slice(0, 2).toUpperCase();
      placeholder.hidden = true;
      symbol.appendChild(image);
      symbol.appendChild(placeholder);
      setImageFallback(image);
    } else {
      symbol.textContent = item.kind === "bed" ? "▦" : item.kind === "irrigation" ? "≈" : "◇";
    }
  }

  function renderCompanions(plant) {
    var container = planner.querySelector("[data-companions]");
    container.innerHTML = "";
    if (!plant) {
      var unavailable = document.createElement("small");
      unavailable.textContent = "Plant unavailable; companion data cannot be shown.";
      container.appendChild(unavailable);
      return;
    }
    var relationships = plant.companions || [];
    [["good", "Recommended"], ["avoid", "Plants to avoid"]].forEach(function (group) {
      var matches = relationships.filter(function (relationship) { return relationship.relation === group[0]; });
      if (!matches.length) return;
      var section = document.createElement("section");
      section.className = "planner-companion-group" + (group[0] === "avoid" ? " planner-companion-group--avoid" : "");
      var heading = document.createElement("strong");
      heading.innerHTML = "<i></i>" + group[1];
      section.appendChild(heading);
      matches.slice(0, 4).forEach(function (relationship) {
        var row = document.createElement("div");
        row.className = "planner-companion";
        var name = document.createElement("strong");
        name.textContent = relationship.name;
        var reason = document.createElement("small");
        reason.textContent = relationship.reason || "Catalogue relationship";
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = "+";
        button.title = "Add " + relationship.name;
        button.setAttribute("aria-label", "Add " + relationship.name);
        button.dataset.addCompanion = relationship.other_plant_id;
        row.appendChild(name); row.appendChild(reason); row.appendChild(button);
        section.appendChild(row);
      });
      container.appendChild(section);
    });
    if (!container.children.length) {
      var note = document.createElement("small");
      note.textContent = "No companion relationships are stored for this plant.";
      container.appendChild(note);
    }
  }

  function setMode(mode) {
    if (mode !== "select") state.shapeEditId = null;
    state.mode = mode;
    planner.querySelectorAll("[data-tool]").forEach(function (button) {
      var active = button.dataset.tool === mode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    viewport.classList.toggle("is-panning", mode === "pan");
    viewport.classList.toggle("is-measuring", mode === "measure");
    if (mode !== "measure") measure.hidden = true;
    renderObjects();
    updateInspector();
  }

  function setWorkingMode(mode) {
    if (["garden", "irrigation", "sensors"].indexOf(mode) === -1) return;

    state.workingMode = mode;
    planner.dataset.workingMode = mode;

    planner.querySelectorAll("button[data-working-mode]").forEach(function (button) {
      var active = button.dataset.workingMode === mode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  function addFromAsset(asset, point) {
    var kind = asset.dataset.kind;
    var item;
    if (kind === "plant") {
      var plant = plants[asset.dataset.plantId];
      if (!plant) return;
      var width = Number.isFinite(plant.spacing_in_row_cm) && plant.spacing_in_row_cm > 0 ? Math.max(plant.spacing_in_row_cm / 100, 0.1) : 0.5;
      var height = Number.isFinite(plant.spacing_between_rows_cm) && plant.spacing_between_rows_cm > 0 ? Math.max(plant.spacing_between_rows_cm / 100, 0.1) : 0.5;
      item = { id: nextId("plant"), kind: "plant", layer: "plants", name: plant.name, plantId: plant.plant_id, x: 0, y: 0, width: width, height: height, rotation: 0, quantity: 1, bedId: null };
    } else {
      var size = defaultSize(kind, asset.dataset.variant);
      item = { id: nextId(kind), kind: kind, variant: asset.dataset.variant, layer: layerFor(kind, asset.dataset.variant), name: asset.dataset.name || kind, x: 0, y: 0, width: size[0], height: size[1], rotation: 0 };
    }
    var requestedGeometry = asset.dataset.geometryType || "rect";
    if (requestedGeometry === "area" || requestedGeometry === "path") {
      item.geometryType = requestedGeometry;
      item.points = initialShapePoints(requestedGeometry);
      // Give a new path room to bend vertically.
      if (requestedGeometry === "path") item.height = Math.max(item.height, 2);
    }
    item.width = Math.min(item.width, state.garden.width);
    item.height = Math.min(item.height, state.garden.height);
    if (item.variant === "round-pot") item.width = item.height = Math.min(item.width, item.height);
    item.z = nextZForLayer(item.layer);
    var target = point || visibleCanvasCentre();
    item.x = clamp(round(target.x - item.width / 2), 0, state.garden.width - item.width);
    item.y = clamp(round(target.y - item.height / 2), 0, state.garden.height - item.height);
    if (item.kind === "plant") { recalculatePlantQuantity(item); syncAssignedBed(item); }
    var before = beginChange();
    state.objects.push(item);
    state.selectedId = item.id;
    finishChange(before);
    render();
    toast(item.name + " added");
    if (window.innerWidth <= 1024) closePanels();
  }

  function addPlantById(plantId, nearItem) {
    var asset = planner.querySelector('[data-library-asset][data-plant-id="' + CSS.escape(plantId) + '"]');
    if (!asset) return;
    var point = nearItem ? { x: nearItem.x + nearItem.width + 0.4, y: nearItem.y } : null;
    addFromAsset(asset, point);
  }

  function defaultSize(kind, variant) {
    var sizes = {
      "raised-bed": [4, 2], "ground-bed": [4, 2], "square-bed": [2.5, 2.5], "round-pot": [1, 1], "planter": [2, 0.9], "large-container": [1.6, 1.3], "greenhouse": [6, 3.5],
      "main-1in": [5, 0.35], "main-half": [5, 0.3], "main-quarter": [4, 0.25], "emitter-15": [4, 0.25], "emitter-30": [4, 0.25], "dripper": [0.5, 0.5],
      "grass": [5, 4], "soil": [5, 4], "paving": [4, 1.2], "gravel": [4, 3], "mulch": [4, 3], "woodchips": [4, 3], "concrete": [3, 2], "decking": [4, 3], "soaker-hose": [4, 2], "garden-hose": [5, 2], "fence": [5, 0.35], "hedge": [5, 0.55], "structure": [3, 2.5], "tree": [1.8, 1.8], "water-tank": [1.2, 1.5], "utility": [1.5, 1.5]
    };
    return sizes[variant] || (kind === "surface" ? [4, 3] : [2, 1.5]);
  }

  function layerFor(kind, variant) {
    if (
      kind === "surface" &&
      ["paving", "gravel", "concrete", "decking"].indexOf(variant) !== -1
    ) {
      return "paths";
    }

    return {
      bed: "beds",
      irrigation: "irrigation",
      surface: "surfaces",
      structure: "structures",
      utility: "structures"
    }[kind] || kind;
  }

  function visibleCanvasCentre() {
    var rect = stage.getBoundingClientRect();
    var viewRect = viewport.getBoundingClientRect();
    return {
      x: clamp(((viewRect.left + viewRect.width / 2) - rect.left) / renderScale(), 0, state.garden.width),
      y: clamp(((viewRect.top + viewRect.height / 2) - rect.top) / renderScale(), 0, state.garden.height)
    };
  }

  function pointOnStage(event) {
    var rect = stage.getBoundingClientRect();
    return {
      x: clamp((event.clientX - rect.left) / renderScale(), 0, state.garden.width),
      y: clamp((event.clientY - rect.top) / renderScale(), 0, state.garden.height)
    };
  }

  function syncAssignedBed(item) {
    var centreX = item.x + item.width / 2;
    var centreY = item.y + item.height / 2;
    var bed = state.objects.find(function (candidate) {
      return candidate.kind === "bed" && candidate.bedId && centreX >= candidate.x && centreX <= candidate.x + candidate.width && centreY >= candidate.y && centreY <= candidate.y + candidate.height;
    });
    item.bedId = bed ? bed.bedId : null;
  }

  function nextDuplicateName(name) {
  var base = String(name || "Object").trim();

  // Treat trailing "copy" and integer suffixes as duplication suffixes.
  base = base.replace(/(?:\s+copy|\s+[2-9]\d*|\s+1\d+)+$/i, "").trim();
  if (!base) base = "Object";

  var used = new Set(state.objects.map(function (item) {
    return item.name.trim().toLowerCase();
  }));

  var number = 2;
  var candidate;

  do {
    var suffix = " " + number;
    candidate = base.slice(0, 120 - suffix.length).trimEnd() + suffix;
    number += 1;
  } while (used.has(candidate.toLowerCase()));

  return candidate;
}

  function duplicateSelected() {
    var item = selected();
    if (!item) return;
    var before = beginChange();
    var copy = clone(item);
    copy.id = nextId(item.kind);
    copy.name = nextDuplicateName(item.name);
    copy.locked = false;
    copy.x = clamp(round(item.x + 0.4), 0, state.garden.width - item.width);
    copy.y = clamp(round(item.y + 0.4), 0, state.garden.height - item.height);
    copy.z = nextZForLayer(item.layer);
    delete copy.sourcePlantingId;
    if (copy.kind === "bed") { delete copy.bedId; delete copy.zoneName; }
    if (copy.kind === "plant") { recalculatePlantQuantity(copy); syncAssignedBed(copy); }
    state.objects.push(copy);
    state.selectedId = copy.id;
    finishChange(before);
    render();
    toast(copy.name + " created");
  }

  function deleteSelected() {
    var item = selected();
    if (!item || item.locked) return;
    var before = beginChange();
    state.objects = state.objects.filter(function (candidate) { return candidate.id !== item.id; });
    state.selectedId = null;
    finishChange(before);
    render();
    toast(item.name + " removed");
  }

  function reorderSelected(action) {
    var item = selected();
    if (!item || item.locked) return;
    var ordered = orderedObjects();
    var index = ordered.indexOf(item);
    var before = beginChange();
    if (action === "forward" && index < ordered.length - 1) {
      var above = ordered[index + 1];
      var aboveZ = above.z;
      above.z = item.z;
      item.z = aboveZ;
    }
    if (action === "backward" && index > 0) {
      var below = ordered[index - 1];
      var belowZ = below.z;
      below.z = item.z;
      item.z = belowZ;
    }
    if (action === "front") item.z = Math.max.apply(Math, ordered.map(function (candidate) { return candidate.z; })) + 1;
    if (action === "back") item.z = Math.min.apply(Math, ordered.map(function (candidate) { return candidate.z; })) - 1;
    finishChange(before);
    render();
    toast(item.name + " stacking order updated");
  }

  function viewportMetrics() {
    var style = window.getComputedStyle(viewport);
    var rect = viewport.getBoundingClientRect();
    var borderWidth = (parseFloat(style.borderLeftWidth) || 0) + (parseFloat(style.borderRightWidth) || 0);
    var borderHeight = (parseFloat(style.borderTopWidth) || 0) + (parseFloat(style.borderBottomWidth) || 0);
    var paddingLeft = parseFloat(style.paddingLeft) || 0;
    var paddingRight = parseFloat(style.paddingRight) || 0;
    var paddingTop = parseFloat(style.paddingTop) || 0;
    var paddingBottom = parseFloat(style.paddingBottom) || 0;
    var width = Math.max(0, rect.width - borderWidth);
    var height = Math.max(0, rect.height - borderHeight);
    return {
      width: width,
      height: height,
      contentWidth: Math.max(0, width - paddingLeft - paddingRight),
      contentHeight: Math.max(0, height - paddingTop - paddingBottom)
    };
  }

  function calculateFittedBaseScale() {
    var metrics = viewportMetrics();
    var stageStyle = window.getComputedStyle(stage);
    var borderWidth = (parseFloat(stageStyle.borderLeftWidth) || 0) + (parseFloat(stageStyle.borderRightWidth) || 0);
    var borderHeight = (parseFloat(stageStyle.borderTopWidth) || 0) + (parseFloat(stageStyle.borderBottomWidth) || 0);
    var availableWidth = Math.max(1, metrics.contentWidth - borderWidth);
    var availableHeight = Math.max(1, metrics.contentHeight - borderHeight);
    if (!metrics.width || !metrics.height || !state.garden.width || !state.garden.height) return null;
    return Math.min(availableWidth / state.garden.width, availableHeight / state.garden.height);
  }

  function centreStageInViewport() {
    var metrics = viewportMetrics();
    stage.style.marginLeft = Math.max(0, (metrics.contentWidth - stage.offsetWidth) / 2) + "px";
    stage.style.marginTop = Math.max(0, (metrics.contentHeight - stage.offsetHeight) / 2) + "px";
  }

  function updateZoomPresentation() {
    stage.style.setProperty("--planner-zoom", state.zoomMultiplier);
    stage.style.setProperty("--planner-inverse-zoom", round(1 / state.zoomMultiplier, 4));
    planner.querySelector("[data-zoom-output]").value = Math.round(state.zoomMultiplier * 100) + "%";
    planner.querySelector("[data-zoom-in]").disabled = state.zoomMultiplier >= MAX_ZOOM;
    planner.querySelector("[data-zoom-out]").disabled = state.zoomMultiplier <= MIN_ZOOM;
    var scaleMetres = isImperial() ? 6 * METRES_PER_FOOT : 2;
    planner.querySelector("[data-scale-bar]").style.width = (scaleMetres * renderScale()) + "px";
    planner.querySelector("[data-scale-output]").value = isImperial() ? "6 ft" : "2 m";
  }

  function setBasePixelsPerMetre(next, preserveCentre) {
    var viewRect = viewport.getBoundingClientRect();
    var focusClientX = viewRect.left + viewport.clientWidth / 2;
    var focusClientY = viewRect.top + viewport.clientHeight / 2;
    var oldStageRect = stage.getBoundingClientRect();
    var oldRenderScale = renderScale();
    var gardenX = (focusClientX - oldStageRect.left) / oldRenderScale;
    var gardenY = (focusClientY - oldStageRect.top) / oldRenderScale;
    state.basePixelsPerMetre = next;
    updateStageGeometry();
    centreStageInViewport();
    var metrics = viewportMetrics();
    state.fittedViewportWidth = metrics.width;
    state.fittedViewportHeight = metrics.height;
    updateZoomPresentation();
    if (preserveCentre && oldRenderScale) {
      var newStageRect = stage.getBoundingClientRect();
      viewport.scrollLeft += newStageRect.left + gardenX * renderScale() - focusClientX;
      viewport.scrollTop += newStageRect.top + gardenY * renderScale() - focusClientY;
    }
    updateRulers();
  }

  function setZoomMultiplier(next, preserveCentre, focusPoint) {
    var viewRect = viewport.getBoundingClientRect();
    var focusClientX = focusPoint ? focusPoint.clientX : viewRect.left + viewport.clientWidth / 2;
    var focusClientY = focusPoint ? focusPoint.clientY : viewRect.top + viewport.clientHeight / 2;
    var oldStageRect = stage.getBoundingClientRect();
    var oldRenderScale = renderScale();
    var gardenX = (focusClientX - oldStageRect.left) / oldRenderScale;
    var gardenY = (focusClientY - oldStageRect.top) / oldRenderScale;
    state.zoomMultiplier = clamp(round(next, 2), MIN_ZOOM, MAX_ZOOM);
    updateZoomPresentation();
    if (preserveCentre && oldRenderScale) {
      var newStageRect = stage.getBoundingClientRect();
      viewport.scrollLeft += newStageRect.left + gardenX * renderScale() - focusClientX;
      viewport.scrollTop += newStageRect.top + gardenY * renderScale() - focusClientY;
    }
    updateRulers();
  }

  function steppedZoom(direction) {
    var next = state.zoomMultiplier;
    if (direction > 0) {
      next = ZOOM_STEPS.find(function (step) { return step > state.zoomMultiplier + 0.001; }) || MAX_ZOOM;
    } else {
      next = ZOOM_STEPS.slice().reverse().find(function (step) { return step < state.zoomMultiplier - 0.001; }) || MIN_ZOOM;
    }
    return next;
  }

  function fitZoom() {
    var fittedBaseScale = calculateFittedBaseScale();
    if (!fittedBaseScale) return;
    setBasePixelsPerMetre(fittedBaseScale, false);
    setZoomMultiplier(1, false);
    requestAnimationFrame(function () { viewport.scrollLeft = 0; viewport.scrollTop = 0; updateRulers(); });
  }

  function updateRulers() {
    var rulerX = planner.querySelector("[data-ruler-x]");
    var rulerY = planner.querySelector("[data-ruler-y]");
    var stageRect = stage.getBoundingClientRect();
    var viewRect = viewport.getBoundingClientRect();
    var originX = stageRect.left - viewRect.left;
    var originY = stageRect.top - viewRect.top;
    rulerX.innerHTML = "";
    rulerY.innerHTML = "";
    var step = isImperial() ? METRES_PER_FOOT : 0.5;
    var majorEvery = isImperial() ? 2 : 2;
    var xTicks = Math.floor(state.garden.width / step);
    var yTicks = Math.floor(state.garden.height / step);
    for (var x = 0; x <= xTicks; x += 1) {
      var tickX = document.createElement("i");
      tickX.className = "planner-ruler__tick" + (x % majorEvery === 0 ? " is-major" : "");
      tickX.style.left = (originX + x * step * renderScale()) + "px";
      if (x % majorEvery === 0) tickX.innerHTML = "<span>" + (isImperial() ? x : x / 2) + "</span>";
      rulerX.appendChild(tickX);
    }
    for (var y = 0; y <= yTicks; y += 1) {
      var tickY = document.createElement("i");
      tickY.className = "planner-ruler__tick" + (y % majorEvery === 0 ? " is-major" : "");
      tickY.style.top = (originY + y * step * renderScale()) + "px";
      if (y % majorEvery === 0) tickY.innerHTML = "<span>" + (isImperial() ? y : y / 2) + "</span>";
      rulerY.appendChild(tickY);
    }
  }

  function updateLayerClasses() {
    stage.classList.toggle("hide-halos", Boolean(state.hiddenLayers.halos));
    stage.classList.toggle("hide-labels", Boolean(state.hiddenLayers.labels));
  }

  function openPanel(name) {
    if (window.innerWidth > 1024) {
      state.panelCollapsed[name] = !state.panelCollapsed[name];
      updatePanelLayout();
      requestAnimationFrame(function () { updateRulers(); fitZoom(); });
      return;
    }

    var panel = planner.querySelector('[data-panel="' + name + '"]');
    if (!panel) return;

    var wasOpen = panel.classList.contains("is-open");
    closePanels();
    if (wasOpen) return;

    panel.classList.add("is-open");
    planner.querySelector("[data-panel-scrim]").hidden = false;
    updatePanelLayout();
  }

  function closePanels() {
    planner.querySelectorAll("[data-panel]").forEach(function (panel) { panel.classList.remove("is-open"); });
    planner.querySelector("[data-panel-scrim]").hidden = true;
    updatePanelLayout();
  }

  function collapsePanel(name) {
    if (window.innerWidth <= 1024) { closePanels(); return; }
    state.panelCollapsed[name] = true;
    updatePanelLayout();
    requestAnimationFrame(function () { updateRulers(); fitZoom(); });
  }

  function updatePanelLayout() {
    planner.classList.toggle("is-library-collapsed", state.panelCollapsed.library);
    planner.classList.toggle("is-inspector-collapsed", state.panelCollapsed.inspector);
    planner.querySelectorAll("[data-panel-toggle]").forEach(function (button) {
      var expanded = window.innerWidth > 1024
        ? !state.panelCollapsed[button.dataset.panelToggle]
        : Boolean(planner.querySelector('[data-panel="' + button.dataset.panelToggle + '"].is-open'));
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
      button.classList.toggle("is-active", expanded);
    });
  }

  function toast(message) {
    var node = planner.querySelector("[data-planner-toast]");
    window.clearTimeout(toastTimer);
    node.textContent = message;
    node.hidden = false;
    toastTimer = window.setTimeout(function () { node.hidden = true; }, 2200);
  }

  function setPlannerView(view) {
    if (view !== "plan") state.shapeEditId = null;
    state.activeView = view;
    planner.querySelectorAll("[data-planner-view-button]").forEach(function (button) {
      var active = button.dataset.plannerViewButton === view;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    planner.querySelectorAll("[data-plan-only]").forEach(function (node) { node.hidden = view !== "plan"; });
    planner.querySelector("[data-calendar-view]").hidden = view !== "calendar";
    if (view === "calendar") { closePanels(); planner.querySelector("[data-layers-panel]").hidden = true; renderCalendar(); }
    if (view === "plan") requestAnimationFrame(updateRulers);
    renderObjects();
    updateInspector();
  }

  function updateFilterButtons() {
    planner.querySelectorAll("[data-plant-filter]").forEach(function (button) {
      var active = state.plantFilters.indexOf(button.dataset.plantFilter) !== -1;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    planner.querySelector("[data-clear-plant-filters]").hidden = state.plantFilters.length === 0;
  }

  function openGardenDialog(editing) {
    var dialog = planner.querySelector("[data-garden-dialog]");
    var form = planner.querySelector("[data-garden-form]");
    dialog.dataset.editing = editing ? "true" : "false";
    dialog.querySelector("h2").textContent = editing ? "Edit Your Garden" : "Create Your Garden";
    dialog.querySelector('[type="submit"]').textContent = editing ? "Update garden" : "Create garden";
    dialog.querySelector("[data-garden-cancel]").hidden = !editing;
    if (editing) {
      form.elements.gardenName.value = state.garden.name;
      form.elements.measurement.value = isImperial() ? "imperial" : "metric";
      writeDimensionInputs(form, state.garden.width, "width");
      writeDimensionInputs(form, state.garden.height, "height");
      form.elements.north.value = String(state.garden.north || 0);
      form.elements.template.value = "empty";
    }
    syncGardenUnitLabels();
    planner.querySelector("[data-garden-error]").hidden = true;
    if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", "");
  }

  function writeDimensionInputs(form, metres, prefix) {
    var imperial = form.elements.measurement.value === "imperial";
    var totalMinor = imperial ? Math.round(metres / METRES_PER_INCH) : Math.round(metres * 100);
    var base = imperial ? 12 : 100;
    form.elements[prefix + "Major"].value = Math.floor(totalMinor / base);
    form.elements[prefix + "Minor"].value = totalMinor % base;
  }

  function syncGardenUnitLabels() {
    var form = planner.querySelector("[data-garden-form]");
    var imperial = form.elements.measurement.value === "imperial";
    form.querySelectorAll("[data-major-unit]").forEach(function (node) { node.textContent = imperial ? "feet" : "metres"; });
    form.querySelectorAll("[data-minor-unit]").forEach(function (node) { node.textContent = imperial ? "inches" : "centimetres"; });
    form.elements.widthMajor.setAttribute("aria-label", "Width " + (imperial ? "feet" : "metres"));
    form.elements.widthMinor.setAttribute("aria-label", "Width " + (imperial ? "inches" : "centimetres"));
    form.elements.heightMajor.setAttribute("aria-label", "Height " + (imperial ? "feet" : "metres"));
    form.elements.heightMinor.setAttribute("aria-label", "Height " + (imperial ? "inches" : "centimetres"));
    ["widthMinor", "heightMinor"].forEach(function (name) { form.elements[name].max = imperial ? "11" : "99"; });
  }

  function readDimension(form, prefix) {
    var major = Number(form.elements[prefix + "Major"].value);
    var minor = Number(form.elements[prefix + "Minor"].value || 0);
    var imperial = form.elements.measurement.value === "imperial";
    var limit = imperial ? 12 : 100;
    if (!Number.isFinite(major) || !Number.isFinite(minor) || major < 0 || minor < 0 || minor >= limit) return NaN;
    return imperial ? major * METRES_PER_FOOT + minor * METRES_PER_INCH : major + minor / 100;
  }

  function applyGardenSettings(settings, editing) {
    var oldGarden = clone(state.garden);
    var sourceObjects = editing ? state.objects : (settings.template === "demo" ? demoObjects : []);
    var sourceWidth = editing ? oldGarden.width : initialState.garden.width;
    var sourceHeight = editing ? oldGarden.height : initialState.garden.height;
    var scaleX = settings.width / sourceWidth;
    var scaleY = settings.height / sourceHeight;
    state.garden = { name: settings.name, width: round(settings.width), height: round(settings.height), measurement: settings.measurement, units: settings.measurement === "imperial" ? "ft" : "m", north: settings.north };
    state.objects = clone(sourceObjects).map(function (item) {
      if (editing && item.locked) return item;
      item.x = round(clamp(item.x * scaleX, 0, Math.max(0, state.garden.width - 0.1)));
      item.y = round(clamp(item.y * scaleY, 0, Math.max(0, state.garden.height - 0.1)));
      item.width = round(clamp(item.width * scaleX, 0.1, Math.max(0.1, state.garden.width - item.x)));
      item.height = round(clamp(item.height * scaleY, 0.1, Math.max(0.1, state.garden.height - item.y)));
      if (item.variant === "round-pot") item.width = item.height = Math.min(item.width, item.height);
      recalculatePlantQuantity(item);
      return item;
    });
    state.hasPlan = true;
    state.selectedId = null;
    state.shapeEditId = null;
    state.undo = [];
    state.redo = [];
    refreshDirtyState();
    ensureZOrder();
    updateGardenCanvas();
    render();
    updateHistoryControls();
    setPlannerView("plan");
    requestAnimationFrame(fitZoom);
  }

  planner.addEventListener("click", function (event) {
    var workingModeButton = event.target.closest("button[data-working-mode]");
    if (workingModeButton) {
      setWorkingMode(workingModeButton.dataset.workingMode);
      return;
    }
    if (interaction && interaction.type === "node") {
      endObjectInteraction({ pointerId: interaction.pointerId, type: "pointerup" });
    }
    if (event.target.closest("[data-edit-shape]")) {
      var shapeItem = selected();
      if (!hasEditableGeometry(shapeItem) || shapeItem.locked) return;
      if (isShapeEditing(shapeItem)) {
        state.shapeEditId = null;
      } else {
        setMode("select");
        state.shapeEditId = shapeItem.id;
      }
      render();
      return;
    }

    // Keyboard activation of the midpoint buttons.
    var shapeEdge = event.target.closest("[data-shape-edge]");
    if (shapeEdge && event.detail === 0 && isShapeEditing(selected())) {
      var shapeBefore = beginChange();
      if (insertShapePoint(selected(), Number(shapeEdge.dataset.shapeEdge)) >= 0) {
        if (validShape(selected())) finishChange(shapeBefore);
        else state.objects = JSON.parse(shapeBefore);
        render();
      }
      return;
    }
    if (event.target.closest("[data-save-plan]")) { savePlan(); return; }
    var viewButton = event.target.closest("[data-planner-view-button]");
    if (viewButton) { setPlannerView(viewButton.dataset.plannerViewButton); return; }
    if (event.target.closest("[data-north-lock]")) {
      state.northLocked = !state.northLocked;
      updateGardenCanvas();
      toast(state.northLocked ? "North orientation locked" : "North orientation unlocked");
      return;
    }
    if (event.target.closest("[data-edit-garden]")) { openGardenDialog(true); return; }
    var filterButton = event.target.closest("[data-plant-filter]");
    if (filterButton) {
      var filter = filterButton.dataset.plantFilter;
      var existing = state.plantFilters.indexOf(filter);
      if (existing === -1) state.plantFilters.push(filter); else state.plantFilters.splice(existing, 1);
      updateFilterButtons(); filterLibrary(); return;
    }
    if (event.target.closest("[data-clear-plant-filters]")) { state.plantFilters = []; updateFilterButtons(); filterLibrary(); return; }
    var tool = event.target.closest("[data-tool]");
    if (tool) { setMode(tool.dataset.tool); return; }
    var action = event.target.closest("[data-action]");
    if (action && !action.disabled) {
      if (action.dataset.action === "toggle-lock") toggleSelectedLock();
      if (action.dataset.action === "duplicate") duplicateSelected();
      if (action.dataset.action === "delete") deleteSelected();
      if (action.dataset.action === "undo") undo();
      if (action.dataset.action === "redo") redo();
      return;
    }
    var stackAction = event.target.closest("[data-stack-action]");
    if (stackAction && !stackAction.disabled) { reorderSelected(stackAction.dataset.stackAction); return; }
    var orientation = event.target.closest("[data-orientation]");
    if (orientation && !orientation.disabled && selected() && !selected().locked) {
      var orientationBefore = beginChange();
      selected().rotation = Number(orientation.dataset.orientation);
      finishChange(orientationBefore);
      render();
      return;
    }
    var add = event.target.closest("[data-add-asset]");
    if (add) { addFromAsset(add.closest("[data-library-asset]")); return; }
    var companion = event.target.closest("[data-add-companion]");
    if (companion) { addPlantById(companion.dataset.addCompanion, selected()); return; }
    var tab = event.target.closest("[data-library-tab]");
    if (tab) {
      planner.querySelectorAll("[data-library-tab]").forEach(function (button) { var active = button === tab; button.classList.toggle("is-active", active); button.setAttribute("aria-pressed", active ? "true" : "false"); });
      planner.querySelectorAll("[data-library-panel]").forEach(function (panel) { panel.classList.toggle("is-active", panel.dataset.libraryPanel === tab.dataset.libraryTab); });
      filterLibrary(); return;
    }
    var panelToggle = event.target.closest("[data-panel-toggle]");
    if (panelToggle) { openPanel(panelToggle.dataset.panelToggle); return; }
    var panelClose = event.target.closest("[data-panel-close]");
    if (panelClose) { collapsePanel(panelClose.dataset.panelClose); return; }
    if (event.target.closest("[data-panel-scrim]")) { closePanels(); return; }
    if (event.target.closest("[data-layers-toggle]")) {
      var layers = planner.querySelector("[data-layers-panel]");
      layers.hidden = !layers.hidden;
      planner.querySelector("[data-layers-toggle]").setAttribute("aria-expanded", layers.hidden ? "false" : "true");
      return;
    }
    if (event.target.closest("[data-layers-close]")) { planner.querySelector("[data-layers-panel]").hidden = true; planner.querySelector("[data-layers-toggle]").setAttribute("aria-expanded", "false"); }
  });

  objectLayer.addEventListener("dblclick", function (event) {
  if (state.mode !== "select") return;

  var element = event.target.closest("[data-object-id]");
  if (!element) return;

  var item = state.objects.find(function (candidate) {
    return candidate.id === element.dataset.objectId;
  });
  if (!item || !item.locked) return;

  event.preventDefault();
  event.stopPropagation();
  selectObject(item.id, true);
});

  objectLayer.addEventListener("pointerdown", function (event) {
    var element = event.target.closest("[data-object-id]");
    if (!element || state.mode !== "select" ||
        event.button !== 0 || interaction) return;

    var item = state.objects.find(function (candidate) {
      return candidate.id === element.dataset.objectId;
    });
    if (!item) return;

    if (item.locked) {
      event.stopPropagation();
      return;
    }
    var handle = event.target.closest("[data-handle]");
    var rotateHandle = event.target.closest("[data-rotate-handle]");
    var node = event.target.closest("[data-shape-node]");
    var edge = event.target.closest("[data-shape-edge]");

    if (state.selectedId !== item.id) {
      selectObject(item.id, false);
      element = objectLayer.querySelector(
        '.planner-selection-overlay[data-object-id="' +
        CSS.escape(item.id) + '"]'
      );
    }

    var before = beginChange();
    var nodeIndex = -1;

    if (isShapeEditing(item)) {
      // Body drags cannot accidentally move the whole object in this mode.
      if (!node && !edge) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      nodeIndex = edge
        ? insertShapePoint(item, Number(edge.dataset.shapeEdge))
        : Number(node.dataset.shapeNode);
      if (!Number.isInteger(nodeIndex) ||
          nodeIndex < 0 || nodeIndex >= item.points.length) return;
    }

    interaction = {
      type: nodeIndex >= 0 ? "node" :
        handle ? "resize" : rotateHandle ? "rotate" : "move",
      pointerId: event.pointerId,
      item: item,
      before: before,
      startX: event.clientX,
      startY: event.clientY,
      original: clone(item),
      handle: handle && handle.dataset.handle,
      nodeIndex: nodeIndex
    };

    if (interaction.type === "rotate") {
      var rect = element.getBoundingClientRect();
      interaction.centreX = rect.left + rect.width / 2;
      interaction.centreY = rect.top + rect.height / 2;
      interaction.lastPointerAngle = Math.atan2(
        event.clientY - interaction.centreY,
        event.clientX - interaction.centreX
      ) * 180 / Math.PI;
      interaction.rawRotation = item.rotation || 0;
      interaction.snapActive = event.shiftKey;
    }

    // The layer survives renderObjects(); individual object nodes do not.
    try {
      objectLayer.setPointerCapture(event.pointerId);
    } catch (error) {
      /* Window listeners also support synthetic pointer streams. */
    }

    if (edge) renderObjects();
    event.preventDefault();
    event.stopPropagation();
  });

  window.addEventListener("pointermove", function (event) {
    if (!interaction ||
        ["move", "resize", "rotate", "node"].indexOf(interaction.type) === -1 ||
        interaction.pointerId !== event.pointerId) return;

    var item = interaction.item;
    if (item.locked) return;
    var original = interaction.original;
    var screenDx = (event.clientX - interaction.startX) / renderScale();
    var screenDy = (event.clientY - interaction.startY) / renderScale();

    if (interaction.type === "move") {
      item.x = clamp(
        round(original.x + screenDx), 0, state.garden.width - item.width
      );
      item.y = clamp(
        round(original.y + screenDy), 0, state.garden.height - item.height
      );
    } else if (interaction.type === "resize" || interaction.type === "node") {
      var radians = -(original.rotation || 0) * Math.PI / 180;
      var localDx = screenDx * Math.cos(radians) -
        screenDy * Math.sin(radians);
      var localDy = screenDx * Math.sin(radians) +
        screenDy * Math.cos(radians);

      if (interaction.type === "node") {
        var originalPoint = original.points[interaction.nodeIndex];
        item.points[interaction.nodeIndex] = {
          x: round(clamp(originalPoint.x + localDx / original.width, 0, 1), 4),
          y: round(clamp(originalPoint.y + localDy / original.height, 0, 1), 4)
        };
      } else {
        resizeItem(item, original, interaction.handle, localDx, localDy);
      }
    } else {
      var angle = Math.atan2(
        event.clientY - interaction.centreY,
        event.clientX - interaction.centreX
      ) * 180 / Math.PI;
      interaction.rawRotation += signedAngleDelta(
        interaction.lastPointerAngle, angle
      );
      interaction.lastPointerAngle = angle;
      interaction.snapActive = event.shiftKey;
      item.rotation = normalizeAngle(
        interaction.snapActive
          ? Math.round(interaction.rawRotation / 15) * 15
          : Math.round(interaction.rawRotation)
      );
    }

    if (item.kind === "plant") syncAssignedBed(item);
    renderObjects();
    updateInspector();
    event.preventDefault();
  });

  window.addEventListener("pointerup", endObjectInteraction);
  window.addEventListener("pointercancel", endObjectInteraction);

  function endObjectInteraction(event) {
    if (!interaction ||
        ["move", "resize", "rotate", "node"].indexOf(interaction.type) === -1 ||
        interaction.pointerId !== event.pointerId) return;

    var completed = interaction;
    interaction = null;

    try {
      if (objectLayer.hasPointerCapture(completed.pointerId)) {
        objectLayer.releasePointerCapture(completed.pointerId);
      }
    } catch (error) {
      /* Capture may already have ended. */
    }

    if (completed.type === "node" &&
        (event.type === "pointercancel" || !validShape(completed.item))) {
      state.objects = JSON.parse(completed.before);
      if (event.type !== "pointercancel") {
        toast("Keep a non-zero area or path.");
      }
      render();
      return;
    }

    finishChange(completed.before);
    render();
  }

  var northDial = planner.querySelector("[data-north-dial]");
  northDial.addEventListener("pointerdown", function (event) {
    if (state.northLocked) {
      toast("Unlock north orientation to adjust it");
      return;
    }
    var rect = northDial.getBoundingClientRect();
    interaction = {
      type: "north",
      pointerId: event.pointerId,
      centreX: rect.left + rect.width / 2,
      centreY: rect.top + rect.height / 2,
      lastPointerAngle: Math.atan2(event.clientY - (rect.top + rect.height / 2), event.clientX - (rect.left + rect.width / 2)) * 180 / Math.PI,
      rawRotation: state.garden.north || 0,
      originalNorth: state.garden.north || 0
    };
    planner.querySelector("[data-compass]").classList.add("is-adjusting");
    try { northDial.setPointerCapture(event.pointerId); } catch (error) { /* Capture is an enhancement. */ }
    event.preventDefault();
    event.stopPropagation();
  });

  window.addEventListener("pointermove", function (event) {
    if (!interaction || interaction.type !== "north" || interaction.pointerId !== event.pointerId) return;
    var angle = Math.atan2(event.clientY - interaction.centreY, event.clientX - interaction.centreX) * 180 / Math.PI;
    interaction.rawRotation += signedAngleDelta(interaction.lastPointerAngle, angle);
    interaction.lastPointerAngle = angle;
    state.garden.north = normalizeAngle(event.shiftKey ? Math.round(interaction.rawRotation / 15) * 15 : Math.round(interaction.rawRotation));
    updateGardenCanvas();
    event.preventDefault();
  });

  window.addEventListener("pointerup", endNorthInteraction);
  window.addEventListener("pointercancel", endNorthInteraction);
  function endNorthInteraction(event) {
    if (!interaction || interaction.type !== "north" || interaction.pointerId !== event.pointerId) return;
    var changed = Math.round(interaction.originalNorth) !== Math.round(state.garden.north || 0);
    interaction = null;
    planner.querySelector("[data-compass]").classList.remove("is-adjusting");
    if (changed) {
      refreshDirtyState();
      updateSaveState();
    }
  }

  function resizeItem(item, original, handle, dx, dy) {
    if (item.locked) return;
    var minimumWidth = 0.25;
    var minimumHeight = 0.25;
    var stepX = 0.1;
    var stepY = 0.1;
    if (isLinear(item)) {
      minimumWidth = item.kind === "structure" ? 1 : 0.5;
      var linearWidth = original.width + (handle === "e" ? dx : -dx);
      item.width = clamp(Math.max(minimumWidth, Math.round(linearWidth / stepX) * stepX), minimumWidth, state.garden.width);
      if (handle === "w") item.x = clamp(round(original.x + original.width - item.width), 0, original.x + original.width - minimumWidth);
      item.width = round(Math.min(item.width, state.garden.width - item.x));
      item.height = original.height;
      return;
    }
    if (item.kind === "plant") {
      var grid = plantGrid(original);
      minimumWidth = grid.hasSpacingX ? grid.spacingX : 0.1;
      minimumHeight = grid.hasSpacingY ? grid.spacingY : 0.1;
      stepX = grid.hasSpacingX ? grid.spacingX : 0.1;
      stepY = grid.hasSpacingY ? grid.spacingY : 0.1;
    }
    var growsEast = handle.indexOf("e") !== -1;
    var growsSouth = handle.indexOf("s") !== -1;
    var rawWidth = original.width + (growsEast ? dx : -dx);
    var rawHeight = original.height + (growsSouth ? dy : -dy);
    item.width = Math.max(minimumWidth, Math.round(rawWidth / stepX) * stepX);
    item.height = Math.max(minimumHeight, Math.round(rawHeight / stepY) * stepY);
    if (item.variant === "round-pot") {
      var rawSize = Math.abs(dx) >= Math.abs(dy) ? rawWidth : rawHeight;
      var size = Math.max(minimumWidth, Math.round(rawSize / stepX) * stepX);
      item.width = size;
      item.height = size;
    }
    if (!growsEast) item.x = clamp(round(original.x + original.width - item.width), 0, original.x + original.width - minimumWidth);
    if (!growsSouth) item.y = clamp(round(original.y + original.height - item.height), 0, original.y + original.height - minimumHeight);
    item.width = Math.min(item.width, state.garden.width - item.x);
    item.height = Math.min(item.height, state.garden.height - item.y);
    item.width = round(item.width);
    item.height = round(item.height);
    if (item.kind === "plant") recalculatePlantQuantity(item);
  }

  stage.addEventListener("pointerdown", function (event) {
    if (event.target.closest("[data-object-id]")) return;
    if (state.mode === "select") { selectObject(null); return; }
    if (state.mode === "measure") {
      var point = pointOnStage(event);
      interaction = { type: "measure", pointerId: event.pointerId, start: point };
      measure.hidden = false;
      measure.style.left = (point.x * state.basePixelsPerMetre) + "px";
      measure.style.top = (point.y * state.basePixelsPerMetre) + "px";
      measure.style.width = "0";
      try { stage.setPointerCapture(event.pointerId); } catch (error) { /* Capture is an enhancement. */ }
      event.preventDefault();
    }
  });

  stage.addEventListener("pointermove", function (event) {
    if (!interaction || interaction.type !== "measure" || interaction.pointerId !== event.pointerId) return;
    var point = pointOnStage(event);
    var dx = point.x - interaction.start.x;
    var dy = point.y - interaction.start.y;
    var distance = Math.sqrt(dx * dx + dy * dy);
    var angle = Math.atan2(dy, dx) * 180 / Math.PI;
    measure.style.width = (distance * state.basePixelsPerMetre) + "px";
    measure.style.transform = "rotate(" + angle + "deg)";
    measure.style.setProperty("--measure-counter-rotation", (-angle) + "deg");
    measure.querySelector("output").value = formatLength(distance, true);
  });

  stage.addEventListener("pointerup", function (event) {
    if (interaction && interaction.type === "measure" && interaction.pointerId === event.pointerId) interaction = null;
  });

  viewport.addEventListener("pointerdown", function (event) {
    if (state.mode !== "pan" || event.target.closest("[data-object-id]")) return;
    interaction = { type: "pan", pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, scrollLeft: viewport.scrollLeft, scrollTop: viewport.scrollTop };
    viewport.classList.add("is-dragging");
    try { viewport.setPointerCapture(event.pointerId); } catch (error) { /* Capture is an enhancement. */ }
    event.preventDefault();
  });

  viewport.addEventListener("pointermove", function (event) {
    if (!interaction || interaction.type !== "pan" || interaction.pointerId !== event.pointerId) return;
    viewport.scrollLeft = interaction.scrollLeft - (event.clientX - interaction.startX);
    viewport.scrollTop = interaction.scrollTop - (event.clientY - interaction.startY);
    updateRulers();
  });

  viewport.addEventListener("pointerup", endPan);
  viewport.addEventListener("pointercancel", endPan);
  function endPan(event) {
    if (!interaction || interaction.type !== "pan" || interaction.pointerId !== event.pointerId) return;
    interaction = null;
    viewport.classList.remove("is-dragging");
    if (state.viewportResizePending) {
      state.viewportResizePending = false;
      requestAnimationFrame(function () {
        var fittedBaseScale = calculateFittedBaseScale();
        if (fittedBaseScale) setBasePixelsPerMetre(fittedBaseScale, true);
      });
    }
  }

  viewport.addEventListener("scroll", updateRulers, { passive: true });
  viewport.addEventListener("wheel", function (event) {
    if (!event.ctrlKey) return;
    event.preventDefault();
    setZoomMultiplier(steppedZoom(event.deltaY < 0 ? 1 : -1), true, { clientX: event.clientX, clientY: event.clientY });
  }, { passive: false });

  planner.querySelectorAll("[data-library-asset]").forEach(function (asset) {
    asset.addEventListener("dragstart", function (event) { draggedAsset = asset; event.dataTransfer.effectAllowed = "copy"; event.dataTransfer.setData("text/plain", asset.dataset.plantId || asset.dataset.variant || asset.dataset.kind); });
  });
  viewport.addEventListener("dragover", function (event) { event.preventDefault(); event.dataTransfer.dropEffect = "copy"; });
  viewport.addEventListener("drop", function (event) { event.preventDefault(); if (draggedAsset) addFromAsset(draggedAsset, pointOnStage(event)); draggedAsset = null; });

  planner.querySelector("[data-library-search]").addEventListener("input", filterLibrary);
  function filterLibrary() {
    var query = planner.querySelector("[data-library-search]").value.trim().toLowerCase();
    var activePanel = planner.querySelector("[data-library-panel].is-active");
    if (!activePanel) return;
    var visiblePlants = 0;
    var selectedPlant = selected() && selected().kind === "plant" ? plants[selected().plantId] : null;
    activePanel.querySelectorAll("[data-library-asset]").forEach(function (asset) {
      var matches = !query || asset.dataset.search.indexOf(query) !== -1;
      if (matches && asset.dataset.kind === "plant") {
        var plant = plants[asset.dataset.plantId] || {};
        matches = state.plantFilters.every(function (filter) {
          var parts = filter.split(":");
          if (parts[0] === "category") return String(plant.category || "").toLowerCase() === parts[1];
          if (parts[0] === "timing") {
            var calendar = plant.calendar || {};
            if (parts[1] === "sow") return [calendar.sow_indoors, calendar.sow_outdoors].some(function (entry) { return entry && entry.months.indexOf(currentMonth) !== -1; });
            var key = parts[1] === "transplant" ? "transplant_out" : "harvest";
            return calendar[key] && calendar[key].months.indexOf(currentMonth) !== -1;
          }
          if (parts[0] === "relationship") {
            var relationships = selectedPlant ? selectedPlant.companions || [] : plant.companions || [];
            return relationships.some(function (relationship) {
              if (relationship.relation !== parts[1]) return false;
              return selectedPlant ? relationship.other_plant_id === plant.plant_id : true;
            });
          }
          return true;
        });
        if (matches) visiblePlants += 1;
      }
      asset.hidden = !matches;
    });
    if (activePanel.dataset.libraryPanel === "plants") activePanel.querySelector(".planner-asset-panel__heading small").textContent = visiblePlants + " of " + catalog.length + " records";
  }

  planner.querySelectorAll("[data-layer]").forEach(function (toggle) {
    toggle.addEventListener("change", function () {
      state.hiddenLayers[toggle.dataset.layer] = !toggle.checked;
      render();
    });
  });

  planner.querySelector("[data-zoom-in]").addEventListener("click", function () { setZoomMultiplier(steppedZoom(1), true); });
  planner.querySelector("[data-zoom-out]").addEventListener("click", function () { setZoomMultiplier(steppedZoom(-1), true); });
  planner.querySelector("[data-zoom-fit]").addEventListener("click", fitZoom);

  var form = planner.querySelector("[data-inspector-form]");
  form.querySelectorAll("[data-field]").forEach(function (field) {
    field.addEventListener("focus", function () { field.dataset.before = beginChange(); });
    field.addEventListener("change", function () {
      var item = selected();
      if (!item || item.locked) return;
      var value = field.value;
      var geometryChanged = false;
      if (field.dataset.field === "name") item.name = value.trim() || item.name;
      if (field.dataset.field === "width") { item.width = clamp(fromDisplayUnits(Number(value)) || item.width, item.kind === "plant" ? (plantGrid(item).spacingX || 0.1) : 0.1, state.garden.width - item.x); geometryChanged = true; }
      if (field.dataset.field === "height") { item.height = clamp(fromDisplayUnits(Number(value)) || item.height, item.kind === "plant" ? (plantGrid(item).spacingY || 0.1) : 0.1, state.garden.height - item.y); geometryChanged = true; }
      if (field.dataset.field === "length" && isLinear(item)) {
        var parsedLength = Number(value);
        item.width = clamp(Number.isFinite(parsedLength) ? fromDisplayUnits(parsedLength) : item.width, item.kind === "structure" ? 1 : 0.5, state.garden.width - item.x);
      }
      if (field.dataset.field === "rotation") item.rotation = Number(value) || 0;
      if (item.kind === "plant") { if (geometryChanged) recalculatePlantQuantity(item); syncAssignedBed(item); }
      finishChange(field.dataset.before || beginChange());
      render();
    });
  });
  form.querySelector('[data-field="rotation"]').addEventListener("input", function (event) {
    var item = selected();
    if (!item || item.locked) return;
    item.rotation = Number(event.target.value);
    form.querySelector("[data-rotation-output]").value = item.rotation + "°";
    renderObjects();
  });

  var gardenForm = planner.querySelector("[data-garden-form]");
  gardenForm.addEventListener("change", function (event) {
    if (event.target.name === "measurement") syncGardenUnitLabels();
  });
  gardenForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var width = readDimension(gardenForm, "width");
    var height = readDimension(gardenForm, "height");
    var name = gardenForm.elements.gardenName.value.trim();
    var error = planner.querySelector("[data-garden-error]");
    if (!name || !Number.isFinite(width) || !Number.isFinite(height) || width < 1 || height < 1 || width > 100 || height > 100) {
      error.textContent = "Enter a garden name and dimensions between 1 and 100 metres (or the imperial equivalent). Inches must be 0–11 and centimetres 0–99.";
      error.hidden = false;
      return;
    }
    var editingGarden = planner.querySelector("[data-garden-dialog]").dataset.editing === "true";
    var changingDimensions =
      round(width) !== state.garden.width ||
      round(height) !== state.garden.height;

    if (editingGarden && changingDimensions && state.objects.some(function (item) {
      return item.locked;
    })) {
      error.textContent = "Unlock all objects before changing the garden dimensions.";
      error.hidden = false;
      return;
    }

    applyGardenSettings({ name: name, width: width, height: height, measurement: gardenForm.elements.measurement.value, north: Number(gardenForm.elements.north.value), template: gardenForm.elements.template.value }, planner.querySelector("[data-garden-dialog]").dataset.editing === "true");
    planner.querySelector("[data-garden-dialog]").close();
  });
  planner.querySelector("[data-garden-cancel]").addEventListener("click", function () { planner.querySelector("[data-garden-dialog]").close(); });

  document.addEventListener("keydown", function (event) {
    if (!planner.contains(document.activeElement) && document.activeElement !== document.body) return;
    if (interaction && interaction.type === "node") {
      if (event.key === "Escape") {
        event.preventDefault();
        endObjectInteraction({
          pointerId: interaction.pointerId,
          type: "pointercancel"
        });
        state.shapeEditId = null;
        render();
      } else {
        // Do not undo, save, delete, or nudge a half-finished node drag.
        event.preventDefault();
      }
      return;
    }

    if (event.key === "Escape" && state.shapeEditId) {
      event.preventDefault();
      state.shapeEditId = null;
      render();
      return;
    }
    var editing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") { event.preventDefault(); savePlan(); return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") { event.preventDefault(); event.shiftKey ? redo() : undo(); return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "y") { event.preventDefault(); redo(); return; }
    if (editing) return;
    var vertexButton = document.activeElement.closest("[data-shape-node]");
    if (vertexButton && isShapeEditing(selected()) &&
        /^Arrow/.test(event.key)) {
      event.preventDefault();
      var vertexItem = selected();
      var vertexIndex = Number(vertexButton.dataset.shapeNode);
      var vertexBefore = beginChange();
      var oldPoint = clone(vertexItem.points[vertexIndex]);
      var step = event.shiftKey ? 0.05 : 0.01;
      var nextPoint = clone(oldPoint);

      if (event.key === "ArrowLeft") nextPoint.x -= step;
      if (event.key === "ArrowRight") nextPoint.x += step;
      if (event.key === "ArrowUp") nextPoint.y -= step;
      if (event.key === "ArrowDown") nextPoint.y += step;
      nextPoint.x = round(clamp(nextPoint.x, 0, 1), 4);
      nextPoint.y = round(clamp(nextPoint.y, 0, 1), 4);
      vertexItem.points[vertexIndex] = nextPoint;

      if (validShape(vertexItem)) finishChange(vertexBefore);
      else vertexItem.points[vertexIndex] = oldPoint;
      render();
      var replacement = objectLayer.querySelector(
        '[data-shape-node="' + vertexIndex + '"]'
      );
      if (replacement) replacement.focus({ preventScroll: true });
      return;
    }

    if (state.shapeEditId && /^Arrow/.test(event.key)) {
      event.preventDefault();
      return;
    }
    if ((event.key === "Delete" || event.key === "Backspace") && selected()) { event.preventDefault(); deleteSelected(); return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "d" && selected()) { event.preventDefault(); duplicateSelected(); return; }
    var item = selected();
    if (!item || !/^Arrow/.test(event.key)) return;
    event.preventDefault();
    if (item.locked) return;
    var before = beginChange();
    var increment = event.shiftKey ? 0.5 : 0.1;
    if (event.key === "ArrowLeft") item.x = Math.max(0, item.x - increment);
    if (event.key === "ArrowRight") item.x = Math.min(state.garden.width - item.width, item.x + increment);
    if (event.key === "ArrowUp") item.y = Math.max(0, item.y - increment);
    if (event.key === "ArrowDown") item.y = Math.min(state.garden.height - item.height, item.y + increment);
    item.x = round(item.x); item.y = round(item.y);
    if (item.kind === "plant") syncAssignedBed(item);
    finishChange(before);
    render();
  });

  window.addEventListener("resize", function () {
    window.clearTimeout(window.__plannerResize);
    window.__plannerResize = window.setTimeout(function () {
      if (window.innerWidth > 1024) closePanels(); else updatePanelLayout();
      var metrics = viewportMetrics();
      var viewportChanged = Math.abs(metrics.width - state.fittedViewportWidth) > 4 || Math.abs(metrics.height - state.fittedViewportHeight) > 4;
      if (state.hasPlan && state.activeView === "plan" && viewportChanged) {
        if (interaction && interaction.type === "pan") state.viewportResizePending = true;
        else {
          var fittedBaseScale = calculateFittedBaseScale();
          if (fittedBaseScale) setBasePixelsPerMetre(fittedBaseScale, true);
        }
      } else updateRulers();
    }, 100);
  });

  setMode("select");
  setWorkingMode(state.workingMode);
  updatePanelLayout();
  render();
  updateFilterButtons();
  updateHistoryControls();
  setPlannerView("plan");
  requestAnimationFrame(function () {
    if (state.hasPlan) fitZoom(); else openGardenDialog(false);
  });
})();
