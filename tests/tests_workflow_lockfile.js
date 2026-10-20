// Guards for the workflow lockfile (.github/workflows/actions.lock): workflows
// name actions by release tag, the lockfile pins each tag to a commit, and the
// CI "Verify action lockfile" step runs `gh actions-lock --verify`.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const YAML = require('yaml');

const WORKFLOWS_DIR = path.join(__dirname, '..', '.github', 'workflows');
const CMS_PLATFORM = 'Adam-S-Daniel/cms-platform/';

function loadWorkflows() {
  return fs
    .readdirSync(WORKFLOWS_DIR)
    .filter((f) => /\.ya?ml$/.test(f))
    .sort()
    .map((f) => ({
      file: f,
      doc: YAML.parse(fs.readFileSync(path.join(WORKFLOWS_DIR, f), 'utf8')),
    }));
}

function loadLockfile() {
  return YAML.parse(fs.readFileSync(path.join(WORKFLOWS_DIR, 'actions.lock'), 'utf8'));
}

function stepUses(doc) {
  const out = [];
  for (const job of Object.values(doc.jobs || {})) {
    for (const step of job.steps || []) {
      if (typeof step.uses === 'string') out.push(step.uses);
    }
  }
  return out;
}

const isLocked = (uses) =>
  !uses.startsWith('./') && !uses.startsWith('$/') &&
  !uses.startsWith('docker://') && !uses.startsWith(CMS_PLATFORM);

test('every third-party step uses: is locked in actions.lock', () => {
  const lock = loadLockfile();
  for (const { file, doc } of loadWorkflows()) {
    const listed = (lock.workflows || {})[`.github/workflows/${file}`] || [];
    for (const uses of stepUses(doc).filter(isLocked)) {
      const dep = (lock.dependencies || {})[uses];
      assert.ok(dep, `${file}: ${uses} has no actions.lock dependency`);
      assert.match(dep.commit, /^sha1-[0-9a-f]{40}$/, `${uses}: commit is not sha1-<40 lowercase hex>`);
      assert.equal(dep.ref, uses.slice(uses.lastIndexOf('@') + 1), `${uses}: ref disagrees with the tag`);
      assert.ok(listed.includes(uses), `${file}: actions.lock workflows entry lacks ${uses}`);
    }
  }
});

// actions.lock does not lock reusable workflows, and neither `--verify` nor
// `sha_pinning_required` flags a tag there, so each needs a full commit SHA.
test('job-level reusable workflow uses: end in a full 40-hex commit SHA', () => {
  for (const { file, doc } of loadWorkflows()) {
    for (const [id, job] of Object.entries(doc.jobs || {})) {
      if (typeof job.uses !== 'string') continue;
      if (job.uses.startsWith('./') || job.uses.startsWith('$/') || job.uses.startsWith(CMS_PLATFORM)) continue;
      assert.match(job.uses, /@[0-9a-f]{40}$/, `${file} job ${id}: ${job.uses} is not pinned to a 40-hex SHA`);
    }
  }
});

test('ci.yml "Verify action lockfile" step runs the pinned gh actions-lock --verify', () => {
  const ci = loadWorkflows().find((w) => w.file === 'ci.yml').doc;
  const steps = ci.jobs.test.steps.filter((s) => s.name === 'Verify action lockfile');
  assert.equal(steps.length, 1, 'expected exactly one "Verify action lockfile" step in the test job');
  const step = steps[0];
  assert.ok(!('continue-on-error' in step), 'the verify step must not set continue-on-error');
  assert.ok(!('if' in step), 'the verify step must not carry an if: that could skip it');
  assert.ok(!('if' in ci.jobs.test), 'the test job must not carry an if: that could skip the verify step');
  assert.equal(step.env.GH_TOKEN, '${{ github.token }}');
  const lines = step.run.split('\n');
  const required = [
    'set -euo pipefail',
    'gh release download v0.2.0 -R github/gh-actions-lock -p linux-amd64 -O "$ext/gh-actions-lock"',
    'echo "79ec84c191667fd935a277e6fd3662cf5d3669cccc9e99998731d8f306f373b6  $ext/gh-actions-lock" | sha256sum -c -',
    '(cd "$ext" && gh extension install .)',
    'out=$(gh actions-lock --verify --no-interactive --json=valid,findings) || rc=$?',
    `if [[ "$rc" -ne 0 ]] || ! jq -e '.valid == true and ([.findings[] | select(.category != "cooldown-config-ignored")] | length) == 0' <<<"$out" >/dev/null; then`,
  ];
  assert.ok(
    lines.some((line) => line.trim() === 'exit 1'),
    'verify step must `exit 1` when verification fails',
  );
  for (const line of required) {
    assert.ok(lines.includes(line), `verify step is missing the line: ${line}`);
  }
});
