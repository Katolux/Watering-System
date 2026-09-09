const assert = require("node:assert/strict");
const { launchChromium, loadPlaywright } = require("./browser_support.cjs");

const { chromium } = loadPlaywright();

async function main() {
  const baseURL = process.env.PLANNER_TEST_BASE_URL;
  assert(baseURL, "PLANNER_TEST_BASE_URL is required");

  const browser = await launchChromium(chromium);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });

  try {
    await page.goto(`${baseURL}/planner`, { waitUntil: "networkidle" });

    const valid = page.locator('.planner-object[data-object-id="plant-valid"]');
    const missing = page.locator('.planner-object[data-object-id="plant-missing"]');
    const missingWithoutQuantity = page.locator('.planner-object[data-object-id="plant-missing-no-quantity"]');
    await assert.doesNotReject(() => valid.waitFor({ state: "visible" }));
    await assert.doesNotReject(() => missing.waitFor({ state: "visible" }));
    await assert.doesNotReject(() => missingWithoutQuantity.waitFor({ state: "visible" }));

    assert.equal(await page.locator('.planner-object[data-object-id="plant-valid"] .planner-plant-instance').count(), 4);
    assert.equal(await page.locator("[data-save-plan]").isDisabled(), true);

    // Working modes initialize independently of tools and preserve layer visibility.
    const planner = page.locator('[data-planner]');
    assert.equal(await planner.getAttribute('data-working-mode'), 'garden');
    await valid.first().click();
    for (const [mode, opacity] of [['irrigation', '0.35'], ['sensors', '0.35'], ['garden', '1']]) {
      await page.locator(`button[data-working-mode="${mode}"]`).click();
      assert.equal(await planner.getAttribute('data-working-mode'), mode);
      assert.equal(await page.locator('button[data-working-mode][aria-pressed="true"]').count(), 1);
      assert.equal(await page.locator(`button[data-working-mode="${mode}"]`).getAttribute('aria-pressed'), 'true');
      assert.equal(await valid.first().evaluate(el => getComputedStyle(el).opacity), opacity);
      assert.equal(await page.locator('.planner-selection-overlay').evaluate(el => getComputedStyle(el).opacity), '1');
      await page.locator('[data-layers-toggle]').click();
      await page.locator('input[data-layer="plants"]').uncheck();
      assert.equal(await valid.count(), 0);
      assert.equal(await page.locator('.planner-selection-overlay').count(), 0);
      await page.locator('input[data-layer="plants"]').check();
      await page.locator('[data-layers-close]').click();
      assert.equal(await valid.first().evaluate(el => getComputedStyle(el).opacity), opacity);
      assert.equal(await page.locator('[data-tool="select"]').getAttribute('aria-pressed'), 'true');
      assert.equal(await page.locator('[data-save-plan]').isDisabled(), true);
    }

    await missing.first().click();
    assert.match(await page.locator('.planner-object[data-object-id="plant-missing"] .planner-plant-unavailable').first().innerText(), /Plant unavailable/);
    assert.equal(await page.locator("[data-inspector-name]").innerText(), "Heritage tomato row");
    assert.match(await page.locator("[data-inspector-type]").innerText(), /Plant unavailable/);
    assert.equal(await page.locator("[data-plant-quantity]").innerText(), "7");

    await missingWithoutQuantity.first().click();
    assert.equal(await page.locator("[data-plant-quantity]").innerText(), "Unavailable");

    await page.locator('[data-planner-view-button="calendar"]').click();
    const calendarText = await page.locator("[data-calendar-body]").innerText();
    assert.match(calendarText, /Heritage tomato row/);
    assert.match(calendarText, /Plant unavailable/);
    await page.locator('[data-planner-view-button="plan"]').click();

    await page.locator('.planner-object[data-object-id="plant-valid"]').first().click();
    assert.equal(await page.locator("[data-plant-quantity]").innerText(), "4");
    assert.equal(await page.locator("[data-save-plan]").isDisabled(), true, "selection and repeated rendering must not dirty the plan");

    await page.locator("[data-geometry-section]").evaluate((details) => { details.open = true; });
    const width = page.locator('[data-inspector-form] [data-field="width"]');
    await width.fill("1.5");
    await width.dispatchEvent("change");
    assert.equal(await page.locator("[data-plant-quantity]").innerText(), "6");
    assert.equal(await page.locator("[data-save-plan]").isEnabled(), true);

    await page.keyboard.press("ArrowRight");
    assert.equal(await page.locator("[data-plant-quantity]").innerText(), "6", "repositioning must not change quantity");
    await page.locator("[data-save-plan]").click();
    await page.waitForFunction(() => document.querySelector("[data-save-state]").textContent.includes("Saved"));

    const saved = await page.evaluate(async () => (await fetch("/api/planner/layout")).json());
    const savedValid = saved.objects.find((item) => item.id === "plant-valid");
    const savedMissing = saved.objects.find((item) => item.id === "plant-missing");
    const savedMissingWithoutQuantity = saved.objects.find((item) => item.id === "plant-missing-no-quantity");
    assert.equal(savedValid.quantity, 6);
    assert.equal(savedMissing.plantId, "retired-tomato");
    assert.equal(savedMissing.bedId, "legacy-bed");
    assert.equal(savedMissing.quantity, 7);
    assert.equal(Object.hasOwn(savedMissingWithoutQuantity, "quantity"), false);

    await page.reload({ waitUntil: "networkidle" });
    assert.match(await page.locator('.planner-object[data-object-id="plant-missing"] .planner-plant-unavailable').first().innerText(), /Plant unavailable/);
    assert.equal(await page.locator('.planner-object[data-object-id="plant-valid"] .planner-plant-instance').count(), 6);
    assert.equal(await page.locator("[data-save-plan]").isDisabled(), true);
    assert.deepEqual(errors, []);

    // Labels, halos and artwork remain presentation-only changes.
    await valid.first().click();
    const label = valid.first().locator('.planner-object__label');
    assert.equal(await label.isVisible(), false);
    await page.locator('[data-layers-toggle]').click();
    await page.locator('[data-layer="labels"]').check();
    assert.equal(await label.isVisible(), true);
    await page.locator('[data-layer="labels"]').uncheck();
    const halo = valid.first().locator('.planner-plant-instance__halo').first();
    await page.locator('[data-layer="halos"]').uncheck();
    assert.equal(await halo.isVisible(), false);
    await page.locator('[data-layer="halos"]').check();
    assert.equal(await halo.isVisible(), true);
    assert.equal(await halo.evaluate(el => getComputedStyle(el).borderTopStyle), 'solid');
    assert.equal(await valid.first().locator('img').first().evaluate(el => getComputedStyle(el).transform), 'matrix(1.25, 0, 0, 1.25, 0, 0)');
    await page.locator('[data-layers-close]').click();
    assert.equal(await page.locator("[data-save-plan]").isDisabled(), true);

    const geometry = () => valid.first().evaluate(el =>
      ['x', 'y', 'width', 'height', 'rotation'].map(key => el.style.getPropertyValue('--object-' + key)));
    const originalGeometry = await geometry();
    await page.locator('[data-action="toggle-lock"]').click();
    const overlay = page.locator('.planner-selection-overlay');
    assert.equal(await overlay.locator('[data-handle], [data-rotate-handle]').count(), 0);
    assert.doesNotMatch(await overlay.innerText(), /undefined/);
    assert.equal(await overlay.evaluate(el => getComputedStyle(el, '::after').borderTopStyle), 'dashed');
    assert.equal(await page.locator('[data-field="width"]').isDisabled(), true);
    assert.equal(await page.locator('[data-inspector-form] [data-action="delete"]').isDisabled(), true);

    // Single-click cannot select a locked object; double-click deliberately can.
    await missing.first().click();
    await valid.first().click();
    assert.equal(await page.locator('[data-inspector-name]').innerText(), 'Heritage tomato row');
    await valid.first().dblclick();
    assert.equal(await page.locator('[data-action="toggle-lock"]').innerText(), 'Unlock');
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Delete');
    const box = await valid.first().boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 40, box.y + box.height / 2 + 30);
    await page.mouse.up();
    assert.deepEqual(await geometry(), originalGeometry);
    await page.locator('[data-save-plan]').click();
    await page.waitForFunction(() => document.querySelector('[data-save-state]').textContent.includes('Saved'));
    await page.reload({ waitUntil: 'networkidle' });
    await valid.first().dblclick();
    assert.equal(await page.locator('[data-action="toggle-lock"]').innerText(), 'Unlock');
    await page.locator('[data-action="toggle-lock"]').click();
    assert.equal(await page.locator('[data-field="width"]').isDisabled(), false);
    await page.locator('[data-inspector-form] [data-action="duplicate"]').click();
    assert.equal(await page.locator('[data-inspector-name]').innerText(), 'Tomato group 2');
    await page.locator('[data-inspector-form] [data-action="duplicate"]').click();
    assert.equal(await page.locator('[data-inspector-name]').innerText(), 'Tomato group 3');

    for (const viewport of [{ width: 1440, height: 1000 }, { width: 600, height: 900 }]) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(200);
      const catalogue = page.locator('[data-panel-toggle="library"]');
      const initiallyOpen = await catalogue.getAttribute('aria-expanded');
      await catalogue.click();
      assert.notEqual(await catalogue.getAttribute('aria-expanded'), initiallyOpen);
      await catalogue.click();
      assert.equal(await catalogue.getAttribute('aria-expanded'), initiallyOpen);
      assert.equal(await catalogue.locator('span').isVisible(), true);
    }
    assert.deepEqual(errors, []);
    await require('./planner_geometry_contract.cjs')(page, baseURL);
    await require('./planner_catalogue_contract.cjs')(page, baseURL);
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }

  console.log("Planner frontend persistence contract passed");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
