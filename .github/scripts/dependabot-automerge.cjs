function eligible(pr, repo) {
  return pr.user.login === 'dependabot[bot]' && !pr.draft &&
    pr.base.ref === 'main' && pr.head.repo?.full_name === `${repo.owner}/${repo.repo}` &&
    pr.head.ref.startsWith('dependabot/');
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
          id headRefOid reviewDecision mergeStateStatus autoMergeRequest { enabledAt }
          reviewThreads(first: 100) { nodes { isResolved } pageInfo { hasNextPage } }
        }
      }
    }`, {owner: repo.owner, repo: repo.repo, number: pr.number});
    const live = result.repository.pullRequest;
    if (live.headRefOid !== pr.head.sha || live.autoMergeRequest ||
        live.reviewDecision === 'CHANGES_REQUESTED' || live.reviewDecision === 'REVIEW_REQUIRED' ||
        live.reviewThreads.pageInfo.hasNextPage ||
        live.reviewThreads.nodes.some(thread => !thread.isResolved)) continue;
    if (live.mergeStateStatus === 'CLEAN') {
      core.info(`PR #${pr.number} already has green checks; awaiting its next branch refresh to enable native auto-merge.`);
      continue;
    }
    // Native auto-merge can land workflow updates without a stored PAT.
    // Required repository checks enforce CI, CodeQL, and an up-to-date base.
    await github.graphql(`mutation($id: ID!) {
      enablePullRequestAutoMerge(input: {pullRequestId: $id, mergeMethod: SQUASH}) {
        pullRequest { number autoMergeRequest { enabledAt } }
      }
    }`, {id: live.id});
    core.info(`Enabled native auto-merge for Dependabot PR #${pr.number}.`);
  }

  // Native auto-merge may finish just after the last CI completion event.
  if (context.payload?.workflow_run?.status === 'completed') {
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  const closed = await github.paginate(github.rest.pulls.list, {
    ...repo, state: 'closed', sort: 'updated', direction: 'desc', per_page: 100,
  });
  // Recent merged bot PRs are enough for closeout; retain all other branches.
  const cutoff = Date.now() - 48 * 60 * 60 * 1000;
  let botMerged = false;
  for (const candidate of closed.filter(pr => eligible(pr, repo) &&
    pr.merged_at && Date.parse(pr.merged_at) >= cutoff)) {
    const {data: pr} = await github.rest.pulls.get({...repo, pull_number: candidate.number});
    if (!pr.merged || !eligible(pr, repo)) continue;
    botMerged = true;
    try {
      const {data: branch} = await github.rest.git.getRef({...repo, ref: `heads/${pr.head.ref}`});
      if (branch.object.sha === pr.head.sha) {
        await github.rest.git.deleteRef({...repo, ref: `heads/${pr.head.ref}`});
        core.info(`Removed merged Dependabot branch ${pr.head.ref}.`);
      }
    } catch (error) {
      if (error.status !== 404) throw error;
    }
  }
  if (botMerged) {
    const {data: main} = await github.rest.repos.getBranch({...repo, branch: 'main'});
    const {data: runs} = await github.rest.actions.listWorkflowRuns({
      ...repo, workflow_id: 'ci.yml', head_sha: main.commit.sha, per_page: 100,
    });
    if (!runs.workflow_runs.some(run => run.head_sha === main.commit.sha && run.head_branch === 'main')) {
      // GITHUB_TOKEN auto-merges suppress push workflows; dispatch main CI explicitly.
      await github.rest.actions.createWorkflowDispatch({...repo, workflow_id: 'ci.yml', ref: 'main'});
      core.info(`Dispatched CI for main at ${main.commit.sha}.`);
    }
  }
}

module.exports = automate;
module.exports.eligible = eligible;
