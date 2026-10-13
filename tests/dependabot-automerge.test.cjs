const {test} = require('node:test');
const assert = require('node:assert/strict');
const automate = require('../.github/scripts/dependabot-automerge.cjs');
const {eligible} = automate;

const repo = {owner: 'SECQUOIA', repo: 'LD-SDA-Dynamic'};
const pr = {number: 1, state: 'open', user: {login: 'dependabot[bot]'}, draft: false,
  base: {ref: 'main'}, head: {sha: 'tested-head', ref: 'dependabot/pip/numpy-2',
    repo: {full_name: 'SECQUOIA/LD-SDA-Dynamic'}}};

test('accepts only this repository’s non-draft Dependabot PRs targeting main', () => {
  assert.equal(eligible(pr, repo), true);
  assert.equal(eligible({...pr, user: {login: 'someone'}}, repo), false);
  assert.equal(eligible({...pr, draft: true}, repo), false);
  assert.equal(eligible({...pr, base: {ref: 'other'}}, repo), false);
  assert.equal(eligible({...pr, head: {...pr.head, repo: null}}, repo), false);
  assert.equal(eligible({...pr, head: {...pr.head, ref: 'main'}}, repo), false);
});

function fixture({sha = 'tested-head', review = null, resolved = true,
  mergeState = 'BLOCKED', enabled = false, merged = false,
  branchSha = 'tested-head', branchMissing = false, ciExists = false} = {}) {
  const calls = [];
  const closed = {...pr, state: 'closed', merged: true, merged_at: new Date().toISOString()};
  const github = {
    paginate: async (method, args) => args.state === 'open' ? [pr] : (merged ? [closed] : []),
    graphql: async (query, args) => {
      if (query.startsWith('mutation')) {
        calls.push(['enable', args]); return {};
      }
      return {repository: {pullRequest: {id: 'pr-id', headRefOid: sha,
        reviewDecision: review, mergeStateStatus: mergeState,
        autoMergeRequest: enabled ? {enabledAt: 'today'} : null,
        reviewThreads: {nodes: [{isResolved: resolved}], pageInfo: {hasNextPage: false}},
      }}};
    },
    rest: {
      pulls: {list: () => {}, get: async () => ({data: merged ? closed : pr})},
      repos: {getBranch: async () => ({data: {commit: {sha: 'main-head'}}})},
      actions: {
        listWorkflowRuns: async args => {
          assert.equal(args.workflow_id, 'ci.yml'); assert.equal(args.head_sha, 'main-head');
          return {data: {workflow_runs: ciExists ? [{head_sha: 'main-head', head_branch: 'main'}] : []}};
        },
        createWorkflowDispatch: async args => {calls.push(['dispatch', args]);},
      },
      git: {
        getRef: async () => {
          if (branchMissing) throw {status: 404};
          return {data: {object: {sha: branchSha}}};
        },
        deleteRef: async args => {calls.push(['delete', args]);},
      },
    },
  };
  return {args: {github, context: {repo}, core: {info: () => {}}}, calls};
}

test('enables native auto-merge while repository-required CI gates are pending', async () => {
  const f = fixture(); await automate(f.args);
  assert.deepEqual(f.calls, [['enable', {id: 'pr-id'}]]);
});

test('stale heads, blocking reviews, unresolved threads, and already enabled PRs are skipped', async () => {
  for (const options of [{sha: 'new-head'}, {review: 'CHANGES_REQUESTED'},
    {review: 'REVIEW_REQUIRED'}, {resolved: false}, {enabled: true}, {mergeState: 'CLEAN'}]) {
    const f = fixture(options); await automate(f.args); assert.deepEqual(f.calls, []);
  }
});

test('deletes only the unchanged merged bot branch and starts CI on main', async () => {
  const f = fixture({merged: true}); await automate(f.args);
  assert.deepEqual(f.calls.map(call => call[0]), ['delete', 'dispatch']);
  assert.equal(f.calls[0][1].ref, 'heads/dependabot/pip/numpy-2');
  assert.equal(f.calls[1][1].ref, 'main');
});

test('retains a moved branch and does not dispatch duplicate main CI', async () => {
  const f = fixture({merged: true, branchSha: 'new-work', ciExists: true});
  await automate(f.args); assert.deepEqual(f.calls, []);
});

test('already deleted bot branches still allow missing main CI to be dispatched', async () => {
  const f = fixture({merged: true, branchMissing: true}); await automate(f.args);
  assert.deepEqual(f.calls.map(call => call[0]), ['dispatch']);
});
