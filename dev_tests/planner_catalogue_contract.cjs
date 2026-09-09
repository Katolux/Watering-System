const assert = require('node:assert/strict');

module.exports = async function catalogueContract(page, baseURL) {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const layout = await (await page.request.get(`${baseURL}/api/planner/layout`)).json();
  assert.equal((await page.request.put(`${baseURL}/api/planner/layout`, {
    data: { ...layout, objects: [] }
  })).status(), 200);
  await page.goto(`${baseURL}/planner`, { waitUntil: 'networkidle' });

  const cases = [
    ['mulch', 'surfaces', 'surfaces', 'area', 'rgb(156, 128, 98)'],
    ['woodchips', 'surfaces', 'surfaces', 'area', 'rgb(181, 153, 114)'],
    ['concrete', 'surfaces', 'paths', 'area', 'rgb(198, 196, 188)'],
    ['decking', 'surfaces', 'paths', 'area', 'rgb(178, 152, 118)'],
    ['soaker-hose', 'irrigation', 'irrigation', 'path', 'rgb(87, 87, 75)'],
    ['garden-hose', 'irrigation', 'irrigation', 'path', 'rgb(109, 135, 97)'],
  ];
  for (const [variant, category, layer, geometry, color] of cases) {
    await page.locator(`[data-library-tab="${category}"]`).click();
    const asset = page.locator(`[data-library-asset][data-variant="${variant}"]`);
    assert.equal(await asset.count(), 1);
    await asset.locator('[data-add-asset]').click();
    const selected = page.locator('.planner-selection-overlay');
    const id = await selected.getAttribute('data-object-id');
    const object = page.locator(`.planner-object[data-object-id="${id}"]:not(.planner-selection-overlay)`);
    assert.equal(await object.getAttribute('data-layer'), layer);
    assert.equal(await object.getAttribute('data-geometry-type'), geometry);
    const shape = object.locator(geometry === 'area' ? 'polygon' : 'polyline');
    assert.equal(await shape.evaluate((el, property) => getComputedStyle(el)[property],
      geometry === 'area' ? 'fill' : 'stroke'), color);

    await page.locator('[data-edit-shape]').click();
    await page.locator('[data-shape-edge="0"]').click();
    assert.equal(await page.locator('[data-shape-node]').count(), geometry === 'area' ? 5 : 3);
    await page.locator('[data-edit-shape]').click();
    await page.locator('[data-field="rotation"]').evaluate(el => {
      el.value = '30';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    for (const mode of ['garden', 'irrigation', 'sensors']) {
      await page.locator(`button[data-working-mode="${mode}"]`).click();
      const opacity = mode === 'garden' ? '1' : layer === 'irrigation'
        ? (mode === 'irrigation' ? '1' : '0.65') : '0.35';
      assert.equal(await object.evaluate(el => getComputedStyle(el).opacity), opacity);
    }
    await page.locator('[data-layers-toggle]').click();
    await page.locator(`input[data-layer="${layer}"]`).uncheck();
    assert.equal(await object.count(), 0);
    await page.locator(`input[data-layer="${layer}"]`).check();
    await page.locator('[data-layers-close]').click();
    await page.locator('[data-action="toggle-lock"]').first().click();
    assert.equal(await page.locator('[data-edit-shape]').isDisabled(), true);
  }
  await page.locator('[data-save-plan]').click();
  await page.waitForFunction(() => document.querySelector('[data-save-state]').textContent.includes('Saved'));
  const saved = (await (await page.request.get(`${baseURL}/api/planner/layout`)).json()).objects;
  assert.equal(saved.length, cases.length);
  for (const [variant, , layer, geometry] of cases) {
    const item = saved.find(item => item.variant === variant);
    assert.equal(item.geometryType, geometry);
    assert.equal(item.layer, layer);
    assert.equal(item.locked, true);
    assert.equal(item.rotation, 30);
    assert.equal(item.points.length, geometry === 'area' ? 5 : 3);
  }
  await page.reload({ waitUntil: 'networkidle' });
  assert.equal(await page.locator('.planner-object.is-locked:not(.planner-selection-overlay)').count(), cases.length);
  console.log('Planner catalogue geometry, styles, modes, layers and persistence passed');
};
