const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

function codexRuntimeCandidates() {
  const runtimeRoot = path.join(os.homedir(), ".cache", "codex-runtimes");
  if (!fs.existsSync(runtimeRoot)) return [];

  return fs.readdirSync(runtimeRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(
      runtimeRoot,
      entry.name,
      "dependencies",
      "node",
      "node_modules",
      "playwright",
    ));
}

function loadPlaywright() {
  const configured = process.env.PLAYWRIGHT_MODULE_PATH;
  const candidates = [
    configured,
    configured && path.join(configured, "playwright"),
    "playwright",
    ...codexRuntimeCandidates(),
  ].filter(Boolean);

  const failures = [];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (error) {
      if (error.code !== "MODULE_NOT_FOUND") throw error;
      failures.push(candidate);
    }
  }

  throw new Error(
    "Playwright was not found. Install it in the project or set "
      + "PLAYWRIGHT_MODULE_PATH to the Playwright package (or its node_modules directory). "
      + `Checked: ${failures.join(", ")}`,
  );
}

async function launchChromium(chromium) {
  const executablePath = process.env.PLAYWRIGHT_BROWSER_PATH;
  const configuredChannel = process.env.PLAYWRIGHT_BROWSER_CHANNEL;
  const attempts = executablePath
    ? [{ executablePath }]
    : configuredChannel
      ? [{ channel: configuredChannel }]
      : [{}, { channel: "msedge" }, { channel: "chrome" }];
  const failures = [];

  for (const options of attempts) {
    try {
      return await chromium.launch({ headless: true, ...options });
    } catch (error) {
      failures.push(`${JSON.stringify(options)}: ${error.message.split("\n")[0]}`);
    }
  }

  throw new Error(
    "No Playwright-compatible Chromium browser could be launched. Install Playwright's "
      + "Chromium browser, or set PLAYWRIGHT_BROWSER_PATH / PLAYWRIGHT_BROWSER_CHANNEL. "
      + `Attempts: ${failures.join(" | ")}`,
  );
}

module.exports = { launchChromium, loadPlaywright };
