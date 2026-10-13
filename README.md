# LD-DSA-Dynamic
This repository includes the source code and results associated with the paper titled **"Addressing Discrete Dynamic Optimization via a Logic-Based Discrete-Steepest Descent Algorithm"**, authored by Zedong Peng, Albert Lee, and David E. Bernal Neira.

# Installation

All numerical models are written using the [DAE](https://pyomo.readthedocs.io/en/stable/modeling_extensions/dae.html) and [GDP](https://pyomo.readthedocs.io/en/latest/modeling_extensions/gdp/modeling.html) modules in [Pyomo](https://pyomo.readthedocs.io/en/latest/index.html). Use Python 3.11 or newer in a virtual environment. Install the runtime packages with:

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
node --test tests/dependabot-automerge.test.cjs
python -m pip_audit -r requirements-dev.txt
```

CI runs on pull requests and `main`, and weekly to catch new vulnerabilities.
It tests Python 3.11–3.13, builds and discretizes every model in both mode-transfer
configurations, applies Big-M and hull reformulations, checks GDPopt plugin
availability, and runs the plotting and LaTeX scripts against recorded results.
Generated outputs go into temporary directories. Licensed solver benchmarks
must be run separately with GAMS and the appropriate solver licenses.

Dependabot checks Python packages and GitHub Actions weekly. Its PRs are merged
only after all test lanes, the dependency audit, and other reported checks pass,
with no blocking reviews or unresolved review threads. The merge workflow uses
trusted `main` code and verifies the exact PR head. It deletes only the merged
Dependabot branch and explicitly starts CI on `main` because merges made with
`GITHUB_TOKEN` do not trigger push workflows. A half-hourly check retries PRs
whose other checks finish after CI.

# Usage

```shell
sh -x run.sh
```
