# LD-SDA-Dynamic
This repository includes the source code and results associated with the paper titled **"Addressing Discrete Dynamic Optimization via a Logic-Based Discrete-Steepest Descent Algorithm"**, authored by Zedong Peng, Albert Lee, and David E. Bernal Neira.

Published in *2024 IEEE CDC*, pp. 1664–1669, DOI: [10.1109/CDC56724.2024.10886477](https://doi.org/10.1109/CDC56724.2024.10886477). See [paper provenance and frozen releases](paper/README.md) for the preserved historical revision, solver versions, experimental settings, and integrity checks. `main` remains maintained; use the protected paper release tags for permanent references.

This repository is licensed under the [MIT license](LICENSE). Citation metadata is available in [CITATION.cff](CITATION.cff).

# Installation

All numerical models are written using the [DAE](https://pyomo.readthedocs.io/en/stable/modeling_extensions/dae.html) and [GDP](https://pyomo.readthedocs.io/en/latest/modeling_extensions/gdp/modeling.html) modules in [Pyomo](https://pyomo.readthedocs.io/en/latest/index.html). Use Python 3.12 or newer in a virtual environment. Install the runtime packages with:

```shell
pip3 install -r requirements.txt
```

We use [KNITRO](https://www.artelys.com/solvers/knitro/) and [BARON](https://www.minlp.com/baron-solver) to solve the Mixed-Integer Nonlinear Programs (MINLP) and Nonlinear Programs (NLP). The implementation is based on [GAMS](https://www.gams.com) to access these solvers.

`requirements.txt` contains the dependencies used by this repository, replacing
the old machine-specific Conda/Anaconda export. IDEs, notebook servers, and
unrelated packages from that export are not needed to run these scripts.

# Development and CI

```shell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/verify_paper_snapshot.py
node --test tests/dependabot-automerge.test.cjs
python -m pip_audit -r requirements-dev.txt
```

CI runs on pull requests and `main`, and weekly to catch new vulnerabilities.
It tests Python 3.12–3.13, builds and discretizes every model in both mode-transfer
configurations, applies Big-M and hull reformulations, checks GDPopt plugin
availability, and runs the plotting and LaTeX scripts against recorded results.
Generated outputs go into temporary directories. Licensed solver benchmarks
must be run separately with GAMS and the appropriate solver licenses.

Dependabot checks Python packages and GitHub Actions weekly. A trusted `main`
workflow enables GitHub's native auto-merge for its PRs. Repository rules require
both test lanes, the dependency audit, and CodeQL, with the branch up to date
before merging. The workflow avoids PRs with blocking reviews or unresolved
threads and never runs PR code with write credentials. It deletes only unchanged
merged Dependabot branches and explicitly starts CI on `main` when a token-made
merge suppresses the push event. A half-hourly check reconciles delayed merges.

# Usage

```shell
sh run.sh --help
sh run.sh --stages 4 --strategies gdpopt.ldsda --nlp-solvers knitro --dry-run
```

The launcher runs in the foreground and returns failures to the calling shell.
Set `PYTHON=/path/to/python` to select an interpreter. Actual solves require GAMS
on `PATH` and licenses for the selected solvers. New output is written under
`benchmark-runs/`, with a unique directory per invocation; published results in
`results/` remain frozen. See the [reproduction commands](paper/README.md#running-maintained-benchmarks)
for the paper's stage counts, discretization settings, and time limits.
