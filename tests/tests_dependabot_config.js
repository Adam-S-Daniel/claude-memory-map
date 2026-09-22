// GitHub validates .github/dependabot.yml only once it reaches main (the
// `dependabot` check never runs on a pull request), so an invalid key can
// merge green and silently disable every update. That's exactly what
// happened here: `semver-major-days` under a `github-actions` cooldown
// disabled the whole file for five weeks
// (https://github.com/Adam-S-Daniel/claude-memory-map/issues/31). This test
// is the pre-merge guard a PR-time check can't provide.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const YAML = require('yaml');

const CONFIG_PATH = path.join(__dirname, '..', '.github', 'dependabot.yml');

function loadConfig() {
  return YAML.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
}

test('dependabot.yml parses and declares a github-actions update', () => {
  const config = loadConfig();
  assert.equal(config.version, 2);
  assert.ok(Array.isArray(config.updates));
  assert.ok(config.updates.length > 0);
  assert.ok(
    config.updates.some((entry) => entry['package-ecosystem'] === 'github-actions'),
    'expected at least one update entry with package-ecosystem: github-actions',
  );
});

test('no github-actions cooldown sets a per-SemVer-tier key', () => {
  const config = loadConfig();
  const forbiddenKeys = ['semver-major-days', 'semver-minor-days', 'semver-patch-days'];
  config.updates.forEach((entry, index) => {
    if (entry['package-ecosystem'] !== 'github-actions') return;
    if (!entry.cooldown) return;
    forbiddenKeys.forEach((key) => {
      assert.ok(
        !Object.prototype.hasOwnProperty.call(entry.cooldown, key),
        `updates[${index}] (github-actions) cooldown has "${key}": GitHub's ` +
          'Dependabot options reference does not support per-SemVer-tier ' +
          'cooldown for the github-actions ecosystem, so this is a schema ' +
          'validation error that disables the WHOLE FILE, not a key ' +
          'Dependabot quietly ignores. dependabot/dependabot-core#14628 is ' +
          'the open upstream request to add the support.',
      );
    });
  });
});
