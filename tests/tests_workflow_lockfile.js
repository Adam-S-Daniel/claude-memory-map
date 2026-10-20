// Guards for the workflow lockfile (.github/workflows/actions.lock): workflows
// name actions by release tag, the lockfile pins each tag to a commit, and the
// CI "Verify action lockfile" step runs the shared verify-actions-lock action.
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
      // gh actions-lock lowercases the owner/repo part of a key (GitHub treats it
      // case-insensitively); the ref after the last `@` keeps its case.
      const at = uses.lastIndexOf('@');
      const key = uses.slice(0, at).toLowerCase() + uses.slice(at);
      const dep = (lock.dependencies || {})[key];
      assert.ok(dep, `${file}: ${uses} has no actions.lock dependency`);
      assert.match(dep.commit, /^sha1-[0-9a-f]{40}$/, `${uses}: commit is not sha1-<40 lowercase hex>`);
      assert.equal(dep.ref, uses.slice(uses.lastIndexOf('@') + 1), `${uses}: ref disagrees with the tag`);
      assert.ok(listed.includes(key), `${file}: actions.lock workflows entry lacks ${uses}`);
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

test('ci.yml "Verify action lockfile" step uses the shared verify-actions-lock action', () => {
  const ci = loadWorkflows().find((w) => w.file === 'ci.yml').doc;
  const steps = ci.jobs.test.steps.filter((s) => s.name === 'Verify action lockfile');
  assert.equal(steps.length, 1, 'expected exactly one "Verify action lockfile" step in the test job');
  const step = steps[0];
  assert.match(step.uses, /^Adam-S-Daniel\/verify-actions-lock@v\d+\.\d+\.\d+$/);
  assert.ok(!('continue-on-error' in step), 'the verify step must not set continue-on-error');
  assert.ok(!('if' in step), 'the verify step must not carry an if: that could skip it');
  assert.ok(!('if' in ci.jobs.test), 'the test job must not carry an if: that could skip the verify step');
});
