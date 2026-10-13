const {test} = require('node:test');
const assert = require('node:assert/strict');
const {eligible, green} = require('../.github/scripts/dependabot-automerge.cjs');
const automate = require('../.github/scripts/dependabot-automerge.cjs');

const names = ['Test (Python 3.11)', 'Test (Python 3.12)', 'Test (Python 3.13)', 'Dependency audit'];
const passing = () => ({pageInfo: {hasNextPage: false}, nodes: names.map(name => ({
  __typename: 'CheckRun', name, status: 'COMPLETED', conclusion: 'SUCCESS',
}))});

test('requires all CI lanes and no unfinished or failed additional checks', () => {
  assert.equal(green(passing()), true);
  assert.equal(green(null), false);
  const missing = passing(); missing.nodes.pop();
  assert.equal(green(missing), false);
  for (const conclusion of ['FAILURE', 'CANCELLED', 'TIMED_OUT', null]) {
    const failed = passing(); failed.nodes[0].conclusion = conclusion;
    assert.equal(green(failed), false);
  }
  for (const state of ['PENDING', 'FAILURE', 'ERROR']) {
    const extra = passing(); extra.nodes.push({__typename: 'StatusContext', state});
    assert.equal(green(extra), false);
  }
  const pending = passing(); pending.nodes[0].status = 'IN_PROGRESS';
  assert.equal(green(pending), false);
  const truncated = passing(); truncated.pageInfo.hasNextPage = true;
  assert.equal(green(truncated), false);
});

test('merges only non-draft Dependabot PRs from this repository into main', () => {
  const repo = {owner: 'SECQUOIA', repo: 'LD-SDA-Dynamic'};
  const pr = {user: {login: 'dependabot[bot]'}, draft: false, base: {ref: 'main'},
    head: {ref: 'dependabot/pip/numpy-2', repo: {full_name: 'SECQUOIA/LD-SDA-Dynamic'}}};
  assert.equal(eligible(pr, repo), true);
  assert.equal(eligible({...pr, user: {login: 'someone'}}, repo), false);
  assert.equal(eligible({...pr, draft: true}, repo), false);
  assert.equal(eligible({...pr, base: {ref: 'other'}}, repo), false);
  assert.equal(eligible({...pr, head: {...pr.head, repo: null}}, repo), false);
  assert.equal(eligible({...pr, head: {...pr.head, ref: 'main'}}, repo), false);
});

function fixture({sha = 'tested-head', review = null, resolved = true,
  conclusion = 'success', branchSha = 'tested-head', mergeError = null} = {}) {
  const repo = {owner: 'SECQUOIA', repo: 'LD-SDA-Dynamic'};
  const pr = {number: 1, state: 'open', user: {login: 'dependabot[bot]'},
    draft: false, base: {ref: 'main'}, head: {sha: 'tested-head',
      ref: 'dependabot/pip/numpy-2', repo: {full_name: `${repo.owner}/${repo.repo}`}}};
  const calls = [];
  let merged = false;
  const github = {
    paginate: async () => [pr],
    graphql: async () => ({repository: {pullRequest: {
      headRefOid: sha, reviewDecision: review,
      reviewThreads: {nodes: [{isResolved: resolved}], pageInfo: {hasNextPage: false}},
      commits: {nodes: [{commit: {statusCheckRollup: {contexts: passing()}}}]},
    }}}),
    rest: {
      pulls: {
        list: () => {},
        get: async () => ({data: {...pr, merged}}),
        merge: async args => {
          calls.push(['merge', args]);
          if (mergeError) throw {status: mergeError};
          merged = true; return {data: {merged: true}};
        },
      },
      actions: {
        listWorkflowRuns: async args => {
          assert.equal(args.workflow_id, 'ci.yml');
          assert.equal(args.head_sha, pr.head.sha);
          assert.equal(args.event, 'pull_request');
          return {data: {workflow_runs: [{id: 1, head_sha: pr.head.sha,
            head_branch: pr.head.ref, status: 'completed', conclusion}]}};
        },
        createWorkflowDispatch: async args => { calls.push(['dispatch', args]); },
      },
      git: {
        getRef: async () => ({data: {object: {sha: branchSha}}}),
        deleteRef: async args => { calls.push(['delete', args]); },
      },
    },
  };
  return {args: {github, context: {repo}, core: {info: () => {}}}, calls};
}

test('verifies the tested head, then merges, deletes its branch, and dispatches main CI', async () => {
  const f = fixture();
  await automate(f.args);
  assert.deepEqual(f.calls.map(call => call[0]), ['merge', 'delete', 'dispatch']);
  assert.equal(f.calls[0][1].sha, 'tested-head');
  assert.equal(f.calls[1][1].ref, 'heads/dependabot/pip/numpy-2');
  assert.equal(f.calls[2][1].ref, 'main');
});

test('stale heads, blocking reviews, unresolved threads, and failed CI prevent merging', async () => {
  for (const options of [{sha: 'new-head'}, {review: 'CHANGES_REQUESTED'},
    {review: 'REVIEW_REQUIRED'}, {resolved: false}, {conclusion: 'failure'}]) {
    const f = fixture(options);
    await automate(f.args);
    assert.deepEqual(f.calls, []);
  }
});

test('never deletes a branch that moved after merging', async () => {
  const f = fixture({branchSha: 'new-work'});
  await automate(f.args);
  assert.deepEqual(f.calls.map(call => call[0]), ['merge', 'dispatch']);
});

test('GitHub merge gates and head races leave the PR and branch intact', async () => {
  for (const mergeError of [405, 409]) {
    const f = fixture({mergeError});
    await automate(f.args);
    assert.deepEqual(f.calls.map(call => call[0]), ['merge']);
  }
});
