const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { launchChromium, loadPlaywright } = require("./browser_support.cjs");

const { chromium } = loadPlaywright();
const workspace = path.resolve(__dirname, "..");
const baseURL = process.env.FRONTEND_SMOKE_BASE_URL;
const expectSavedPlan = process.env.FRONTEND_SMOKE_EXPECT_SAVED === "1";
const stateName = expectSavedPlan ? "saved-plan" : "empty-plan";
const outputDirectory = path.resolve(
  workspace,
  process.env.FRONTEND_SMOKE_OUTPUT_DIR || path.join("artifacts", "frontend-smoke"),
);

assert(baseURL, "FRONTEND_SMOKE_BASE_URL is required");

const viewports = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "tablet", width: 900, height: 1000 },
  { name: "mobile", width: 390, height: 844 },
];

const representativeRoutes = [
  { name: "Workspace", path: "/", activeNav: "Workspace", content: ".workspace-page" },
  { name: "Planner", path: "/planner", activeNav: "Planner", content: "[data-planner]" },
  { name: "Garden Control", path: "/automation", activeNav: "Garden Control", content: ".garden-control-page" },
  { name: "Weather", path: "/weather", activeNav: "Weather", content: ".weather-v2" },
  { name: "History", path: "/history", activeNav: "History", content: "[data-history-hub]" },
  { name: "Encyclopedia", path: "/automation/plants", activeNav: "Encyclopedia", content: ".encyclopedia-index-header" },
];

function visibleBox(box) {
  return box && box.width > 0 && box.height > 0;
}

async function assertNoHorizontalOverflow(page, label) {
  const overflow = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  assert.ok(
    overflow.scrollWidth <= overflow.clientWidth + 1,
    `${label} has horizontal overflow (${overflow.scrollWidth}px > ${overflow.clientWidth}px)`,
  );

  const mainBox = await page.locator("#main-content").boundingBox();
  assert.ok(visibleBox(mainBox), `${label} main content has no visible dimensions`);
  assert.ok(mainBox.x >= -1, `${label} main content is clipped on the left`);
  assert.ok(mainBox.x + mainBox.width <= overflow.clientWidth + 1, `${label} main content is clipped on the right`);
}

async function assertShell(page, route, viewport) {
  await assert.doesNotReject(() => page.locator(".app-header").waitFor({ state: "visible" }));
  await assert.doesNotReject(() => page.locator(route.content).waitFor({ state: "visible" }));
  assert.equal(await page.locator(".app-sidebar").count(), 1, `${route.name} is missing the shared sidebar`);

  const activeNav = page.locator('.sidebar-nav__item[aria-current="page"]');
  assert.equal(await activeNav.count(), 1, `${route.name} must expose one active navigation item`);
  assert.equal((await activeNav.innerText()).trim(), route.activeNav);
  await assertNoHorizontalOverflow(page, `${route.name} at ${viewport.name}`);
}

async function assertResponsiveNavigation(page, viewport) {
  if (viewport.name === "desktop") {
    assert.ok(visibleBox(await page.locator(".app-sidebar").boundingBox()), "Desktop sidebar is not visible");
    return;
  }

  const toggle = page.locator("[data-mobile-sidebar-toggle]");
  await assert.doesNotReject(() => toggle.waitFor({ state: "visible" }));
  await toggle.click();
  await page.waitForFunction(() => {
    const shell = document.querySelector("[data-app-shell]");
    const sidebar = document.querySelector(".app-sidebar");
    return shell.dataset.sidebarOpen === "true"
      && Math.abs(sidebar.getBoundingClientRect().left) <= 1;
  });
  const sidebarBox = await page.locator(".app-sidebar").boundingBox();
  assert.ok(visibleBox(sidebarBox) && Math.abs(sidebarBox.x) <= 1, `${viewport.name} sidebar did not open on canvas`);
  await page.mouse.click(viewport.width - 10, Math.round(viewport.height / 2));
  await page.waitForFunction(() => document.querySelector("[data-app-shell]").dataset.sidebarOpen === "false");
}

async function assertWorkspace(page) {
  const openPlanner = page.getByRole("link", { name: "Open Planner" });
  assert.ok(await openPlanner.count() >= 1, "Workspace is missing the Open Planner action");
  assert.equal(await page.locator("[data-workspace-garden-scene]").count(), 0, "Workspace rendered the retired pseudo-map");

  if (expectSavedPlan) {
    await assert.doesNotReject(() => page.getByText("Planner layout ready", { exact: true }).waitFor({ state: "visible" }));
    await assert.doesNotReject(() => page.getByText("A richer Living Garden view", { exact: false }).waitFor({ state: "visible" }));
    assert.equal(await page.locator(".living-garden__interim").count(), 1);
    assert.equal(await page.locator(".living-garden__empty").count(), 0);
  } else {
    await assert.doesNotReject(() => page.getByText("No garden plan available", { exact: true }).waitFor({ state: "visible" }));
    assert.equal(await page.locator(".living-garden__empty").count(), 1);
    assert.equal(await page.locator(".living-garden__interim").count(), 0);
    assert.equal(await page.locator(".garden-snapshot__canvas").count(), 0, "Workspace substituted demo geometry for an empty plan");
  }
}

async function assertPlanner(page) {
  const state = JSON.parse(await page.locator("[data-planner-state]").textContent());
  assert.equal(state.planExists, true, "Planner did not receive the saved plan");
  assert.equal(state.garden.name, "Browser smoke garden");

  const objects = page.locator("[data-planner-objects] .planner-object");
  await assert.doesNotReject(() => objects.first().waitFor({ state: "visible" }));
  assert.equal(await objects.count(), 4, "Planner did not render all saved objects");
  assert.equal(await page.locator("[data-planner-bed], [data-planner-panel]").count(), 0, "Obsolete Planner selectors reappeared");
  await assert.doesNotReject(() => page.locator('.planner-object[data-object-id="smoke-missing-plant"] .planner-plant-unavailable').waitFor({ state: "visible" }));
}

async function assertGardenControl(page, viewport) {
  assert.match(
    await page.locator(".garden-snapshot-card .garden-control-section-header p").textContent(),
    /Read-only view from Planner\./,
  );
  await assert.doesNotReject(() => page.locator(".garden-snapshot__viewport").waitFor({ state: "visible" }));
  assert.equal(await page.locator('.garden-snapshot__canvas[aria-label^="Browser smoke garden Planner layout"]').count(), 1);
  assert.equal(await page.locator(".garden-snapshot__object").count(), 4, "Garden Control did not project the saved Planner geometry");
  assert.equal(await page.locator('.garden-snapshot__object[draggable="true"]').count(), 0, "Garden Snapshot must remain read-only");

  const overview = page.locator("[data-context-overview]");
  await assert.doesNotReject(() => overview.waitFor({ state: "visible" }));
  assert.ok(visibleBox(await page.locator(".garden-context-panel").boundingBox()), `${viewport.name} Garden Overview is clipped or hidden`);

  if (viewport.name === "desktop") {
    const heroBox = await page.locator(".garden-control-hero").boundingBox();
    const snapshotBox = await page.locator(".garden-snapshot-card").boundingBox();
    const overviewBox = await page.locator(".garden-context-panel").boundingBox();
    assert.ok(visibleBox(heroBox) && visibleBox(snapshotBox) && visibleBox(overviewBox));
    assert.ok(overviewBox.x > snapshotBox.x, "Desktop Garden Overview is not beside the snapshot");

    const linkedBed = page.locator('[data-bed-select="raised-1"]');
    await assert.doesNotReject(() => linkedBed.waitFor({ state: "visible" }));
    await linkedBed.click({ position: { x: 5, y: 5 } });
    await assert.doesNotReject(() => page.locator('[data-bed-panel="raised-1"]').waitFor({ state: "visible" }));
    assert.equal(await linkedBed.getAttribute("aria-pressed"), "true");
  }
}

async function captureFailure(page, viewport) {
  try {
    fs.mkdirSync(outputDirectory, { recursive: true });
    const filename = `${stateName}-${viewport?.name || "startup"}-failure.png`;
    await page.screenshot({ path: path.join(outputDirectory, filename), fullPage: true });
    return path.relative(workspace, path.join(outputDirectory, filename));
  } catch {
    return null;
  }
}

async function main() {
  const browser = await launchChromium(chromium);
  const page = await browser.newPage();
  const consoleErrors = [];
  let currentLocation = "startup";
  let currentViewport = null;

  page.on("pageerror", (error) => consoleErrors.push(`${currentLocation}: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(`${currentLocation}: ${message.text()}`);
  });

  try {
    for (const viewport of viewports) {
      currentViewport = viewport;
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      const routes = expectSavedPlan ? representativeRoutes : representativeRoutes.slice(0, 1);

      for (const route of routes) {
        currentLocation = `${stateName}/${viewport.name}${route.path}`;
        const response = await page.goto(`${baseURL}${route.path}`, { waitUntil: "networkidle" });
        assert.equal(response.status(), 200, `${route.name} returned HTTP ${response.status()}`);
        await assertShell(page, route, viewport);

        if (route.name === "Workspace") {
          await assertWorkspace(page);
          await assertResponsiveNavigation(page, viewport);
        } else if (route.name === "Planner") {
          await assertPlanner(page);
        } else if (route.name === "Garden Control") {
          await assertGardenControl(page, viewport);
        }
      }
    }

    assert.deepEqual(consoleErrors, [], `JavaScript console errors:\n${consoleErrors.join("\n")}`);
    console.log(JSON.stringify({
      state: stateName,
      routes: expectSavedPlan ? representativeRoutes.map((route) => route.path) : ["/"],
      viewports: viewports.map(({ name, width, height }) => ({ name, width, height })),
      consoleErrors,
    }));
  } catch (error) {
    const screenshot = await captureFailure(page, currentViewport);
    if (screenshot) console.error(`Failure screenshot: ${screenshot}`);
    throw error;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
