const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const YAML = require('yaml');

const root = path.resolve(__dirname, '..');
const suiteDir = path.join(root, 'suite');
const generatorPath = path.join(root, 'src', 'generate_suite.py');
const expectedNames = fs.readdirSync(suiteDir)
  .filter(name => name.endsWith('.mermaid')).sort();
let tempDir;
let generatedDir;

test.before(() => {
  tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'claude-memory-suite-'));
  const srcDir = path.join(tempDir, 'src');
  fs.mkdirSync(srcDir);
  fs.copyFileSync(generatorPath, path.join(srcDir, 'generate_suite.py'));

  const result = spawnSync('python3', [path.join(srcDir, 'generate_suite.py')], {
    cwd: tempDir,
    encoding: 'utf8',
    env: process.env,
  });
  assert.equal(result.status, 0,
    `generator failed (${result.status ?? result.signal}): ${result.stderr}`);
  generatedDir = path.join(tempDir, 'suite');
});

test.after(() => {
  if (tempDir) fs.rmSync(tempDir, {recursive: true, force: true});
});

test('generator output has exactly the committed Mermaid file set', () => {
  const generatedNames = fs.readdirSync(generatedDir)
    .filter(name => name.endsWith('.mermaid')).sort();
  assert.deepEqual(generatedNames, expectedNames,
    'generated Mermaid files must match the committed suite membership');
});

for (const name of expectedNames) {
  test(`${name} matches fresh generator output byte for byte`, () => {
    assert.deepEqual(
      fs.readFileSync(path.join(generatedDir, name)),
      fs.readFileSync(path.join(suiteDir, name)),
      `${name} is stale relative to src/generate_suite.py`,
    );
  });
}

test('required CI job runs the generated-suite check as an enabled step', () => {
  const workflow = YAML.parse(fs.readFileSync(
    path.join(root, '.github', 'workflows', 'ci.yml'), 'utf8'));
  const steps = workflow?.jobs?.test?.steps;
  assert.ok(Array.isArray(steps), 'CI workflow must define jobs.test.steps');
  assert.ok(steps.some(step => step.run?.trim() === 'npm run test:suite'
    && step.if === undefined
    && (step['continue-on-error'] === undefined || step['continue-on-error'] === false)),
  'required test job must run npm run test:suite without conditional or soft-failure settings');
});
