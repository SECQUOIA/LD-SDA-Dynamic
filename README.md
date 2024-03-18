# LD-DSA-Dynamic
This repository includes the source code and results associated with the paper titled **"Addressing Discrete Dynamic Optimization via a Logic-Based Discrete-Steepest Descent Algorithm"**, authored by Zedong Peng, Albert Lee, and David E. Bernal Neira.

# Installation

All numerical models are written using the [DAE](https://pyomo.readthedocs.io/en/stable/modeling_extensions/dae.html) and [GDP](https://pyomo.readthedocs.io/en/latest/modeling_extensions/gdp/modeling.html) modules in [Pyomo](https://pyomo.readthedocs.io/en/latest/index.html). The necessary Python packages can be installed by running the following script.

```shell
pip3 install -r requirements.txt
```

We use [KNITRO](https://www.artelys.com/solvers/knitro/) and [BARON](https://www.minlp.com/baron-solver) to solve the Mixed-Integer Nonlinear Programs (MINLP) and Nonlinear Programs (NLP). The implementation is based on [GAMS](https://www.gams.com) to access these solvers.

# Usage

```shell
sh -x run.sh
```
