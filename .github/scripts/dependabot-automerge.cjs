const requiredChecks = [
  'Test (Python 3.11)', 'Test (Python 3.12)', 'Test (Python 3.13)',
  'Dependency audit',
];

function eligible(pr, repo) {
  return pr.user.login === 'dependabot[bot]' && !pr.draft &&
    pr.base.ref === 'main' && pr.head.repo?.full_name === `${repo.owner}/${repo.repo}` &&
    pr.head.ref.startsWith('dependabot/');
}

function green(rollup) {
  if (!rollup || rollup.pageInfo.hasNextPage) return false;
  const checks = rollup.nodes;
  return requiredChecks.every(name => checks.some(check =>
    check.name === name && check.status === 'COMPLETED' && check.conclusion === 'SUCCESS'
  )) && checks.every(check => check.__typename === 'CheckRun'
    ? check.status === 'COMPLETED' && ['SUCCESS', 'SKIPPED', 'NEUTRAL'].includes(check.conclusion)
    : check.state === 'SUCCESS');
}

async function automate({github, context, core}) {
  const repo = context.repo;
  const prs = await github.paginate(github.rest.pulls.list, {...repo, state: 'open', per_page: 100});
  for (const candidate of prs.filter(pr => eligible(pr, repo))) {
    const {data: pr} = await github.rest.pulls.get({...repo, pull_number: candidate.number});
    if (pr.state !== 'open' || !eligible(pr, repo)) continue;
    const result = await github.graphql(`query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $number) {
          headRefOid reviewDecision
          reviewThreads(first: 100) { nodes { isResolved } pageInfo { hasNextPage } }
          commits(last: 1) { nodes { commit {
            statusCheckRollup { contexts(first: 100) {
              nodes {
                __typename
                ... on CheckRun { name status conclusion }
                ... on StatusContext { state }
              }
              pageInfo { hasNextPage }
            } }
          } } }
        }
      }
    }`, {owner: repo.owner, repo: repo.repo, number: pr.number});
    const live = result.repository.pullRequest;
    if (live.headRefOid !== pr.head.sha || live.reviewDecision === 'CHANGES_REQUESTED' ||
        live.reviewDecision === 'REVIEW_REQUIRED' || live.reviewThreads.pageInfo.hasNextPage ||
        live.reviewThreads.nodes.some(thread => !thread.isResolved) ||
        !green(live.commits.nodes[0]?.commit.statusCheckRollup?.contexts)) continue;

    // A manually posted check with the same name must not substitute for our CI.
    const {data: runs} = await github.rest.actions.listWorkflowRuns({
      ...repo, workflow_id: 'ci.yml', head_sha: pr.head.sha,
      event: 'pull_request', per_page: 100,
    });
    const latest = runs.workflow_runs.filter(run => run.head_sha === pr.head.sha &&
      run.head_branch === pr.head.ref).sort((a, b) => b.id - a.id)[0];
    if (!latest || latest.status !== 'completed' || latest.conclusion !== 'success') continue;

    try {
      const {data: merged} = await github.rest.pulls.merge({
        ...repo, pull_number: pr.number, sha: pr.head.sha, merge_method: 'squash',
      });
      if (!merged.merged) continue;
    } catch (error) {
      if ([405, 409].includes(error.status)) {
        core.info(`PR #${pr.number} has moved or has an unmet merge gate; leaving it open.`);
        continue;
      }
      throw error;
    }
    const {data: closed} = await github.rest.pulls.get({...repo, pull_number: pr.number});
    if (!closed.merged || closed.head.sha !== pr.head.sha) {
      throw new Error(`Could not verify merge of PR #${pr.number}`);
    }
    try {
      const {data: branch} = await github.rest.git.getRef({...repo, ref: `heads/${pr.head.ref}`});
      if (branch.object.sha === pr.head.sha) {
        await github.rest.git.deleteRef({...repo, ref: `heads/${pr.head.ref}`});
      }
    } catch (error) {
      if (error.status !== 404) throw error;
    } finally {
      // GITHUB_TOKEN merges suppress push workflows; dispatch main CI explicitly.
      await github.rest.actions.createWorkflowDispatch({...repo, workflow_id: 'ci.yml', ref: 'main'});
    }
    core.info(`Merged PR #${pr.number}, removed its unchanged head branch, and dispatched main CI.`);
    // Let the updated base be tested before processing another dependency PR.
    break;
  }
}

module.exports = automate;
module.exports.eligible = eligible;
module.exports.green = green;
