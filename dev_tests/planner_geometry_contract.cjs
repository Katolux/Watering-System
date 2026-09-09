const assert = require('node:assert/strict');

module.exports = async function geometryContract(page, baseURL) {
  // The parent runner uses an isolated temporary database.
  const layout = await (await page.request.get(`${baseURL}/api/planner/layout`)).json();
  assert.equal((await page.request.put(`${baseURL}/api/planner/layout`, {
    data: { ...layout, objects: [] }
  })).status(), 200);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload({ waitUntil: 'networkidle' });

  const edit = page.locator('[data-edit-shape]');
  const nodes = page.locator('[data-shape-node]');
  const selected = page.locator('.planner-selection-overlay');
  const points = type => page.locator(`.planner-shape ${type}`).evaluate(el =>
    Array.from(el.points, point => ({ x: point.x, y: point.y })));
  const drag = async (locator, dx, dy, cancel = false) => {
    const box = await locator.boundingBox();
    assert(box);
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + dx, box.y + box.height / 2 + dy, { steps: 4 });
    if (cancel) await page.keyboard.press('Escape');
    await page.mouse.up();
  };
  const save = async () => {
    await page.locator('[data-save-plan]').click();
    await page.waitForFunction(() => document.querySelector('[data-save-plan]').disabled);
    await page.waitForFunction(() => document.querySelector('[data-save-state]').textContent.includes('Saved'));
    return (await (await page.request.get(`${baseURL}/api/planner/layout`)).json()).objects;
  };

  await page.locator('[data-library-tab="surfaces"]').click();
  await page.locator('[data-variant="grass"] [data-add-asset]').click();
  assert.equal(await selected.getAttribute('data-geometry-type'), 'area');
  await edit.click();
  assert.equal(await nodes.count(), 4);
  assert.equal(await selected.locator('[data-handle]').count(), 0);
  const rectangle = await points('polygon');
  await drag(nodes.nth(0), 25, 25);
  const reshaped = await points('polygon');
  assert.notDeepEqual(reshaped, rectangle);
  await page.locator('[data-action="undo"]').click();
  assert.deepEqual(await points('polygon'), rectangle);
  await page.locator('[data-action="redo"]').click();
  assert.deepEqual(await points('polygon'), reshaped);

  await edit.click();
  await drag(page.locator('[data-shape-edge="3"]'), 15, 0);
  assert.equal(await nodes.count(), 5, 'closing edge supports insertion');
  const inserted = await points('polygon');
  await drag(page.locator('[data-shape-edge="0"]'), 10, 10, true);
  assert.deepEqual(await points('polygon'), inserted, 'Escape rolls back insertion plus drag');
  assert.equal(await nodes.count(), 0);

  await edit.click();
  await nodes.nth(0).focus();
  await page.keyboard.press('ArrowRight');
  assert.notDeepEqual(await points('polygon'), inserted);
  await page.locator('[data-action="toggle-lock"]').click();
  assert.equal(await nodes.count(), 0);
  assert.equal(await edit.isDisabled(), true);
  const lockedPoints = await points('polygon');
  const lockedPosition = await selected.evaluate(el => el.style.cssText);
  await drag(page.locator('.planner-shape polygon'), 20, 20);
  assert.deepEqual(await points('polygon'), lockedPoints);
  assert.equal(await selected.evaluate(el => el.style.cssText), lockedPosition);
  const lockedSaved = await save();
  await page.reload({ waitUntil: 'networkidle' });
  assert.deepEqual(await points('polygon'), lockedPoints);
  await page.locator('.planner-shape polygon').dblclick();
  assert.equal(await edit.isDisabled(), true);
  await page.locator('[data-action="toggle-lock"]').click();
  assert.equal(await edit.isEnabled(), true);
  await edit.click();
  assert.equal(await nodes.count(), 5);
  await page.locator('[data-tool="pan"]').click();
  assert.equal(await nodes.count(), 0);
  await page.locator('[data-tool="select"]').click();

  await page.locator('[data-library-tab="structures"]').click();
  await page.locator('[data-variant="fence"] [data-add-asset]').click();
  assert.equal(await selected.getAttribute('data-geometry-type'), 'path');
  await edit.click();
  assert.equal(await nodes.count(), 2);
  await drag(page.locator('[data-shape-edge="0"]'), 0, 25);
  assert.equal(await nodes.count(), 3);
  const bent = await points('polyline');
  assert(bent[1].y > 0.5);
  await edit.click();
  await page.locator('[data-field="rotation"]').fill('90');
  await page.locator('[data-field="rotation"]').dispatchEvent('change');
  await page.locator('[data-zoom-in]').click();
  await edit.click();
  await drag(nodes.nth(1), -10, 0);
  const rotated = await points('polyline');
  assert(rotated[1].y > bent[1].y, 'screen left increases local y at 90 degrees');
  assert(Math.abs(rotated[1].x - bent[1].x) < 0.001);
  await edit.click();
  const finalObjects = await save();
  assert.equal(finalObjects.length, 2);
  assert.equal(lockedSaved[0].locked, true);
  await page.reload({ waitUntil: 'networkidle' });
  assert.deepEqual(await points('polyline'), rotated);
  assert.deepEqual((await (await page.request.get(`${baseURL}/api/planner/layout`)).json()).objects, finalObjects);
  await page.goto(`${baseURL}/automation`, { waitUntil: 'networkidle' });
  assert.equal(await page.locator('.garden-snapshot__shape polygon').count(), 1);
  assert.equal(await page.locator('.garden-snapshot__shape polyline').count(), 1);
  console.log('Planner editable geometry contract passed');
};
