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
  } finally {
    await browser.close();
  }

  console.log("Planner frontend persistence contract passed");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
