// gh's `--auto` merge counts CLEAN, HAS_HOOKS and UNSTABLE as "already
// mergeable" (cli/cli, pkg/cmd/pr/merge/merge.go, `isImmediatelyMergeable`),
// so with this repo's `required_status_checks: []` a `gh pr merge --auto`
// attempt merged a Dependabot PR on the spot instead of waiting for CI —
// claude-memory-map#35, a major actions/checkout bump, merged before its own
// `test` check had even started. See
// https://github.com/Adam-S-Daniel/cms-platform/issues/437 for the fleet-wide
// incident and the fix: job `auto-merge` now merges nothing, and the
// scheduled `sweep` job is the ONLY merge path, gated on every check on the
// PR's head (at least one from outside this workflow itself) having
// concluded green, and pinned to the exact head those checks judged.
//
// This test parses the workflow with the `yaml` package (never a regex or
// line scan over the YAML — see this repo's AST/parser convention) and then
// actually EXECUTES the extracted `sweep` step's shell script — via
// `bash -c` against a stubbed `gh`/`git` on PATH — because a schedule-only
// workflow gets no run at PR time otherwise, and the sweep's own behaviour
// (what merges, what skips, what refreshes) is exactly what a parse of the
// YAML alone cannot prove.
const { test, before } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const YAML = require('yaml');

const WORKFLOW_PATH = path.join(__dirname, '..', '.github', 'workflows', 'dependabot-auto-merge.yml');
const SELF_WORKFLOW = 'Dependabot auto-merge';
const REPO = 'Adam-S-Daniel/claude-memory-map';
const SHA_A = 'a'.repeat(40);
const SHA_B = 'b'.repeat(40);

function loadWorkflow() {
  return YAML.parse(fs.readFileSync(WORKFLOW_PATH, 'utf8'));
}

function sweepScript() {
  const wf = loadWorkflow();
  const step = wf.jobs.sweep.steps.find((s) => s.name === 'Sweep open Dependabot PRs');
  assert.ok(step, 'expected job `sweep` to have a step named "Sweep open Dependabot PRs"');
  assert.equal(typeof step.run, 'string', 'expected that step to carry a `run:` script');
  return step.run;
}

function assertToolAvailable(cmd) {
  const res = spawnSync(cmd, ['--version']);
  if (res.error) {
    throw new Error(
      `required tool "${cmd}" is not on PATH (${res.error.message}) — this suite executes the ` +
        'real sweep script against it and cannot silently skip that.',
    );
  }
}

before(() => {
  assertToolAvailable('bash');
  assertToolAvailable('jq');
});

// Stub `gh`: logs every invocation (for assertions), and answers just the
// subcommands the sweep script actually calls.
//   - `pr list`          -> the fixture's PR-number list
//   - `pr view N`        -> pr-N.json on the first call for N, pr-N.after.json
//                           on later calls if that file exists (a per-PR
//                           counter file tracks call count) — this is what
//                           lets a test simulate the head moving between the
//                           script's initial snapshot and its post-merge
//                           re-check
//   - `pr merge ... N`    -> refuses (stderr + exit 1) when the trailing PR
//                           number is one of $MERGE_FAILS, else exit 0
//   - `pr update-branch`  -> exit 0
//   - `api ...`           -> a 404-shaped body on stdout + exit 1 (mirrors
//                           `gh api`'s real "error body on stdout" behaviour)
//   - anything else       -> exit 90, so an unexpected call fails loudly
//                           rather than silently returning success
const GH_STUB = [
  '#!/usr/bin/env bash',
  'echo "$*" >> "$FIXTURES/calls.log"',
  '',
  'if [ "$1" = "pr" ] && [ "$2" = "list" ]; then',
  '  cat "$FIXTURES/pr-numbers.txt"',
  '  exit 0',
  'fi',
  '',
  'if [ "$1" = "pr" ] && [ "$2" = "view" ]; then',
  '  num="$3"',
  '  counter="$FIXTURES/.view-count-${num}"',
  '  count=0',
  '  if [ -f "$counter" ]; then count=$(cat "$counter"); fi',
  '  count=$((count + 1))',
  '  echo "$count" > "$counter"',
  '  if [ "$count" -gt 1 ] && [ -f "$FIXTURES/pr-${num}.after.json" ]; then',
  '    cat "$FIXTURES/pr-${num}.after.json"',
  '  else',
  '    cat "$FIXTURES/pr-${num}.json"',
  '  fi',
  '  exit 0',
  'fi',
  '',
  'if [ "$1" = "pr" ] && [ "$2" = "merge" ]; then',
  '  last="${@: -1}"',
  '  case " ${MERGE_FAILS:-} " in',
  '    *" $last "*)',
  '      echo "refused: head no longer matches --match-head-commit" >&2',
  '      exit 1',
  '      ;;',
  '    *)',
  '      exit 0',
  '      ;;',
  '  esac',
  'fi',
  '',
  'if [ "$1" = "pr" ] && [ "$2" = "update-branch" ]; then',
  '  exit 0',
  'fi',
  '',
  'if [ "$1" = "api" ]; then',
  '  echo \'{"message":"Not Found"}\'',
  '  exit 1',
  'fi',
  '',
  'exit 90',
  '',
].join('\n');

// Stub `git`: the sweep script only ever fetches refs (discarded output) and
// diffs a PR head against its base to re-run the manifest-path allowlist.
// Always answering "package-lock.json" keeps every fixture's diff inside the
// allowlist so the manifest re-check never becomes what a test is about.
const GIT_STUB = [
  '#!/usr/bin/env bash',
  'if [ "$1" = "fetch" ]; then',
  '  exit 0',
  'fi',
  'if [ "$1" = "diff" ]; then',
  '  echo "package-lock.json"',
  '  exit 0',
  'fi',
  'exit 0',
  '',
].join('\n');

function makeSandbox() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'dam-sweep-'));
  const bin = path.join(root, 'bin');
  const fixtures = path.join(root, 'fixtures');
  const work = path.join(root, 'work');
  fs.mkdirSync(bin);
  fs.mkdirSync(fixtures);
  fs.mkdirSync(work);
  const ghPath = path.join(bin, 'gh');
  const gitPath = path.join(bin, 'git');
  fs.writeFileSync(ghPath, GH_STUB);
  fs.writeFileSync(gitPath, GIT_STUB);
  fs.chmodSync(ghPath, 0o755);
  fs.chmodSync(gitPath, 0o755);
  return { bin, fixtures, work };
}

function basePr(num, overrides = {}) {
  return {
    number: num,
    baseRefName: 'main',
    headRefOid: SHA_A,
    mergeable: 'MERGEABLE',
    mergeStateStatus: 'CLEAN',
    statusCheckRollup: [],
    ...overrides,
  };
}

// Runs the real sweep script against one fixture PR (#1). `after`, if given,
// is what the stub returns from the SECOND `gh pr view 1` call onward (the
// post-merge-attempt head re-check) — everything else including the first
// `pr view` call keeps reading `pr`.
function runOnePr({ pr, after, mergeFails = '' }) {
  const { bin, fixtures, work } = makeSandbox();
  fs.writeFileSync(path.join(fixtures, 'pr-numbers.txt'), '1\n');
  fs.writeFileSync(path.join(fixtures, 'pr-1.json'), JSON.stringify(pr));
  if (after) {
    fs.writeFileSync(path.join(fixtures, 'pr-1.after.json'), JSON.stringify(after));
  }
  const result = spawnSync('bash', ['-c', sweepScript()], {
    cwd: work,
    env: {
      PATH: `${bin}:${process.env.PATH || '/usr/bin:/bin'}`,
      FIXTURES: fixtures,
      GITHUB_REPOSITORY: REPO,
      SELF_WORKFLOW,
      MERGE_FAILS: mergeFails,
      HOME: work,
    },
    encoding: 'utf8',
  });
  const callsPath = path.join(fixtures, 'calls.log');
  const calls = fs.existsSync(callsPath) ? fs.readFileSync(callsPath, 'utf8').split('\n').filter(Boolean) : [];
  return { result, calls };
}

test('T1: job `auto-merge` carries no merge/arm step', () => {
  const wf = loadWorkflow();
  const stepNames = wf.jobs['auto-merge'].steps.map((s) => s.name);
  assert.deepEqual(
    stepNames,
    [
      'Checkout',
      'Fetch base ref',
      'Get Dependabot metadata',
      'Verify only manifest paths changed',
      'Disable auto-merge (path check failed)',
    ],
    'job `auto-merge` grew a step back that can merge or arm a merge. Per ' +
      'cms-platform#437, gh treats a CLEAN/HAS_HOOKS/UNSTABLE PR as already ' +
      'mergeable and merges it on `gh pr merge --auto` immediately — no ' +
      'matter the trailing `|| true` — so a merge/arm step here races real ' +
      'CI instead of waiting for it. Only job `sweep` may merge.',
  );
});

test('sweep (a): merges once an outside check and an own-workflow check are both green, pinned to the head', () => {
  const pr = basePr(1, {
    statusCheckRollup: [
      { workflowName: 'CI', name: 'test', conclusion: 'SUCCESS' },
      { workflowName: SELF_WORKFLOW, name: 'auto-merge', conclusion: 'SUCCESS' },
    ],
  });
  const { result, calls } = runOnePr({ pr });
  const mergeCalls = calls.filter((l) => l.startsWith('pr merge '));
  assert.equal(mergeCalls.length, 1, `expected exactly one \`pr merge\` call; calls were:\n${calls.join('\n')}`);
  assert.ok(mergeCalls[0].includes(`--match-head-commit ${SHA_A}`), mergeCalls[0]);
  assert.equal(mergeCalls[0].trim().split(/\s+/).pop(), '1', mergeCalls[0]);
  assert.ok(
    result.stdout.includes('merged=1 updated=0 skipped=0 blocked=0 failed=0'),
    `stdout was:\n${result.stdout}`,
  );
  assert.equal(result.status, 0, result.stderr);
});

test('sweep (b): skips when every check on the head comes from this workflow itself', () => {
  const pr = basePr(1, {
    statusCheckRollup: [
      { workflowName: SELF_WORKFLOW, name: 'auto-merge', conclusion: 'SUCCESS' },
      { workflowName: SELF_WORKFLOW, name: 'sweep', conclusion: 'SKIPPED' },
    ],
  });
  const { result, calls } = runOnePr({ pr });
  assert.equal(calls.filter((l) => l.startsWith('pr merge ')).length, 0);
  assert.ok(result.stdout.includes('skipped=1'), `stdout was:\n${result.stdout}`);
  assert.ok(
    result.stdout.includes('every check on its head comes from this workflow'),
    `stdout was:\n${result.stdout}`,
  );
  assert.equal(result.status, 0, result.stderr);
});

test('sweep (c): a still-pending outside check (conclusion null) is not counted as green', () => {
  const pr = basePr(1, {
    statusCheckRollup: [
      { workflowName: 'CI', name: 'test', conclusion: null },
      { workflowName: SELF_WORKFLOW, name: 'auto-merge', conclusion: 'SUCCESS' },
    ],
  });
  const { result, calls } = runOnePr({ pr });
  assert.equal(calls.filter((l) => l.startsWith('pr merge ')).length, 0);
  assert.ok(result.stdout.includes('skipped=1'), `stdout was:\n${result.stdout}`);
  assert.equal(result.status, 0, result.stderr);
});

test('sweep (d): a refused merge whose head has since moved is skipped, never retried as update-branch', () => {
  const pr = basePr(1, {
    statusCheckRollup: [
      { workflowName: 'CI', name: 'test', conclusion: 'SUCCESS' },
      { workflowName: SELF_WORKFLOW, name: 'auto-merge', conclusion: 'SUCCESS' },
    ],
  });
  const after = basePr(1, { headRefOid: SHA_B });
  const { result, calls } = runOnePr({ pr, after, mergeFails: '1' });
  assert.equal(calls.filter((l) => l.startsWith('pr update-branch')).length, 0);
  assert.ok(result.stdout.includes('skipped=1'), `stdout was:\n${result.stdout}`);
  assert.ok(result.stdout.includes('its head moved'), `stdout was:\n${result.stdout}`);
  assert.equal(result.status, 0, result.stderr);
});

test('sweep (e): an empty SELF_WORKFLOW refuses to run rather than merging blind', () => {
  const { bin, fixtures, work } = makeSandbox();
  fs.writeFileSync(path.join(fixtures, 'pr-numbers.txt'), '1\n');
  fs.writeFileSync(
    path.join(fixtures, 'pr-1.json'),
    JSON.stringify(
      basePr(1, { statusCheckRollup: [{ workflowName: 'CI', name: 'test', conclusion: 'SUCCESS' }] }),
    ),
  );
  const result = spawnSync('bash', ['-c', sweepScript()], {
    cwd: work,
    env: {
      PATH: `${bin}:${process.env.PATH || '/usr/bin:/bin'}`,
      FIXTURES: fixtures,
      GITHUB_REPOSITORY: REPO,
      SELF_WORKFLOW: '',
      MERGE_FAILS: '',
      HOME: work,
    },
    encoding: 'utf8',
  });
  const callsPath = path.join(fixtures, 'calls.log');
  const calls = fs.existsSync(callsPath) ? fs.readFileSync(callsPath, 'utf8').split('\n').filter(Boolean) : [];
  assert.notEqual(result.status, 0, `stdout was:\n${result.stdout}\nstderr was:\n${result.stderr}`);
  assert.equal(calls.filter((l) => l.startsWith('pr merge ')).length, 0);
});

test('sweep (f): a non-40-hex headRefOid is skipped rather than merged unpinned', () => {
  const pr = basePr(1, {
    headRefOid: 'abc',
    statusCheckRollup: [
      { workflowName: 'CI', name: 'test', conclusion: 'SUCCESS' },
      { workflowName: SELF_WORKFLOW, name: 'auto-merge', conclusion: 'SUCCESS' },
    ],
  });
  const { result, calls } = runOnePr({ pr });
  assert.equal(calls.filter((l) => l.startsWith('pr merge ')).length, 0);
  assert.ok(result.stdout.includes('skipped=1'), `stdout was:\n${result.stdout}`);
  assert.equal(result.status, 0, result.stderr);
});

test('sweep (g): a refused merge with an unchanged head and BEHIND status still refreshes the branch', () => {
  const pr = basePr(1, {
    mergeStateStatus: 'BEHIND',
    statusCheckRollup: [
      { workflowName: 'CI', name: 'test', conclusion: 'SUCCESS' },
      { workflowName: SELF_WORKFLOW, name: 'auto-merge', conclusion: 'SUCCESS' },
    ],
  });
  const { result, calls } = runOnePr({ pr, mergeFails: '1' });
  assert.equal(calls.filter((l) => l.startsWith('pr update-branch')).length, 1);
  assert.ok(result.stdout.includes('updated=1'), `stdout was:\n${result.stdout}`);
  assert.equal(result.status, 0, result.stderr);
});
