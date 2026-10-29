const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");

const { configPath, loadConfig, saveConfig } = require("../runtime");

describe("operator-desktop runtime config", () => {
  it("persists and loads runtime.json", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sageo-op-"));
    const file = path.join(dir, "runtime.json");
    saveConfig(file, {
      checkout_root: "/tmp/checkout",
      interpreter: "/tmp/python",
      runs_root: "/tmp/runs",
    });
    const loaded = loadConfig(file);
    assert.equal(loaded.checkout_root, "/tmp/checkout");
    assert.equal(loaded.interpreter, "/tmp/python");
    assert.equal(loaded.runs_root, "/tmp/runs");
  });

  it("returns null for missing or invalid config", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sageo-op-"));
    assert.equal(loadConfig(path.join(dir, "missing.json")), null);
    const bad = path.join(dir, "runtime.json");
    fs.writeFileSync(bad, "{nope", "utf8");
    assert.equal(loadConfig(bad), null);
  });

  it("builds config path under userData", () => {
    const p = configPath({ userDataPath: "/tmp/user-data" });
    assert.equal(p, path.join("/tmp/user-data", "runtime.json"));
  });
});
