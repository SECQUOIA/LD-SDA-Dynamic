# Paper record and frozen snapshots

Zedong Peng, Albert Lee, and David E. Bernal Neira, “Addressing Discrete Dynamic
Optimization via a Logic-Based Discrete-Steepest Descent Algorithm,” *2024 IEEE
63rd Conference on Decision and Control (CDC)*, pp. 1664–1669, 2024.

- Publisher DOI: <https://doi.org/10.1109/CDC56724.2024.10886477>.
- Author manuscript: <https://arxiv.org/abs/2409.09237v1> (14 September 2024).
- Machine-readable citation: [CITATION.cff](../CITATION.cff).

## Which version to use

The repository stays maintained on `main`. Cite an exact commit or one of these
protected, immutable releases rather than a moving branch:

- [`paper-cdc-2024-original`](https://github.com/SECQUOIA/LD-SDA-Dynamic/releases/tag/paper-cdc-2024-original)
  preserves the complete historical tree at
  `482e14ebf9caabbd35d959986942cb028778a1d7` (18 March 2024), before the
  2026 dependency and runner maintenance. This is the last repository revision
  before the paper appeared. The paper does not name a Git SHA, so this is a
  preserved historical snapshot, not independent proof of the exact producing
  checkout. Its Conda export contains obsolete dependencies; use an isolated
  historical environment if inspecting it.
- [`paper-cdc-2024-maintenance-1`](https://github.com/SECQUOIA/LD-SDA-Dynamic/releases/tag/paper-cdc-2024-maintenance-1)
  freezes the modern runner, MIT license, tests, documentation, and unchanged
  historical artifacts. It uses the current Python 3.12+ dependency set and is
  the recommended runnable starting point. It is a maintenance release, not a
  claim that the experiments were rerun or their timing reproduced in 2026.

Release immutability locks release tags and assets. A tag ruleset also prevents
updates and deletion of `paper-cdc-2024-*` tags. Corrections require a new release;
never move a paper tag. Future development and security updates belong on `main`.

## Experimental setup and provenance

The following settings come from the author manuscript, §IV-A–C:

| Item | Reported setting |
| --- | --- |
| Modeling | Pyomo.DAE, Pyomo.GDP, and GDPopt LD-SDA |
| Solvers | KNITRO and BARON for (MI)NLP subproblems |
| KNITRO option | `mip_multistart=1` |
| Hardware | Linux; 48 AMD EPYC 7643 CPUs at 2.3 GHz; 1 TB RAM |
| Threads | One thread per experiment |
| Discretization | Orthogonal collocation; 30 finite elements and 3 collocation points per stage |
| Three-stage time limit | 900 seconds |
| Multi-stage instances | 4–9 stages; time limits up to one hour |

Additional version details come from the committed artifacts, **not** from a
version specification in the paper:

| Evidence | Recorded detail |
| --- | --- |
| Historical `requirements.txt` at the original tag | Python 3.11.5; Pyomo 6.7.0; NumPy 1.24.3; pandas 2.1.4; Matplotlib 3.7.2; seaborn 0.12.2; SymPy 1.12 |
| `results/three_stage_dynamic_model_switching/nfe30/2024-03-07_11-29-45/gdp.hull_baron.log` | GAMS 44.3.0; BARON 23.6.22 |
| Same directory, `gdp.hull_knitro.log` | Artelys Knitro 13.2.0 |
| Recorded run configuration/logs | 900 s for stages 3–6; 1800 s for 7–8; 3600 s for 9 |

The exported environment does not pin the historical GDPopt development commit.
A Pyomo version label alone cannot reconstruct that development implementation.
The maintained runner adapts to current Pyomo; it must not be described as an exact
recreation of the original software environment.

The three-stage ordered results used by `result2latex.py` are under
`results/three_stage_dynamic_model_switching/nfe30/2024-03-07_11-29-45/`.
The 4–9-stage data directories are explicitly selected in `result2latex.py` and
`plot_computational_results.py`. Ten-stage source is also retained, but the paper's
multi-stage comparison covers 4–9. Keep recorded termination conditions and
bounds as reported. LD-SDA has no general global-optimality guarantee for these
nonconvex problems (manuscript §II-D).

## Integrity and regeneration

[manifest.json](manifest.json) fixes SHA-256 hashes for all 433 historical files
in `models/`, `results/`, `figures/`, and `latex/`. These trees were compared with
the original revision before the manifest was created. CI checks them without
regenerating published output:

```sh
python scripts/verify_paper_snapshot.py
```

Do not rewrite published artifacts or refresh this manifest to accommodate new
results. New runs go to `benchmark-runs/` or a separate location, and existing
plot/table scripts should be executed in a scratch copy if regeneration is
needed. No new numerical results replace the recorded paper results in this
maintenance release.

## Running maintained benchmarks

Install the current dependencies using the root README. Supply a GAMS
installation on `PATH` and licenses for the selected subsolvers. The preflight
checks the executable and GAMS solver registry; it does not establish that a
license permits a particular model size. GAMS validates licenses when solving.
The runner uses GAMS for MINLP/NLP subsolvers and for decomposition MIP subsolvers
(the latter previously depended on a separately available native Gurobi).

A small setup check requires no GAMS or solver license:

```sh
sh run.sh --stages 4 --strategies gdpopt.ldsda --nlp-solvers knitro \
  --nfe 2 --ncp 2 --dry-run
```

Run the ordered three-stage LD-SDA comparison:

```sh
sh run.sh --stages 3 --strategies gdpopt.ldsda --nlp-solvers knitro baron \
  --nfe 30 --ncp 3 --time-limit 900 --mode-transfer off
```

Run both reformulations of the nine-stage LD-SDA comparison:

```sh
sh run.sh --stages 9 --strategies gdpopt.ldsda --nlp-solvers knitro baron \
  --nfe 30 --ncp 3 --time-limit 3600 --mode-transfer both
```

For baseline methods, select `gdp.bigm gdp.hull gdpopt.enumerate gdpopt.loa
gdpopt.gloa`. Use `--minlp-solvers knitro baron` for direct reformulations,
`--nlp-solvers knitro baron` for decomposition, and `--mip-solver gurobi` for its
GAMS MIP subsolver. `--help` describes all selections. The default three-stage
model includes ordering constraints; `--unordered` selects the other historical
three-stage formulation.

Each invocation allocates a unique output directory. Both logs and JSON include
the norm and mode-transfer flag. `run.json` records the selected configuration,
source revision/dirty state, runtime versions, completion status, and completed
cases. GAMS/solver versions remain in solver logs. Failures retain logs and return
a nonzero process status; the launcher waits for the run to finish.
