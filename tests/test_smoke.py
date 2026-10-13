"""Exercise dependency compatibility without licensed optimization solvers."""

import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from pyomo.dae import ContinuousSet
from pyomo.environ import Constraint, Objective, SolverFactory, TransformationFactory, Var
from pyomo.gdp import Disjunct, Disjunction


ROOT = Path(__file__).resolve().parents[1]
MODELS = sorted(path.stem for path in (ROOT / 'models').glob('*.py'))


@pytest.mark.parametrize('module_name', MODELS)
@pytest.mark.parametrize('mode_transfer', [False, True])
def test_models_discretize_and_reformulate(module_name, mode_transfer):
    module = importlib.import_module(f'models.{module_name}')
    assert Path(module.__file__).resolve().parent == ROOT / 'models'
    model = module.build_model(mode_transfer=mode_transfer)
    assert len(model.stage) == len(list(model.component_objects(ContinuousSet)))
    assert len(model.d) == len(model.stage)
    assert len(list(model.component_data_objects(Objective, active=True))) == 1

    TransformationFactory('dae.collocation').apply_to(
        model, nfe=3, ncp=3, scheme='LAGRANGE-RADAU'
    )
    # Match the benchmark's reconstruction workaround for Pyomo issue #3101.
    for disjunct in model.component_data_objects(Disjunct):
        for constraint in disjunct.component_objects(Constraint):
            constraint._constructed = False
            constraint.construct()
            assert len(constraint) == len(constraint.index_set())
    for time in model.component_objects(ContinuousSet):
        assert len(time) > 2
    for variable in model.component_data_objects(Var, descend_into=True):
        if 'dxdt' in variable.name:
            variable.setlb(-300)
            variable.setub(300)

    for transformation in ['gdp.bigm', 'gdp.hull']:
        reformulated = model.clone()
        options = {'bigM': 1000000} if transformation == 'gdp.bigm' else {}
        TransformationFactory(transformation).apply_to(reformulated, **options)
        assert not list(reformulated.component_data_objects(Disjunction, active=True))


@pytest.mark.parametrize('name', ['gdpopt.ldsda', 'gdpopt.enumerate', 'gdpopt.loa', 'gdpopt.gloa'])
def test_benchmark_solver_plugins_registered(name):
    assert SolverFactory(name).available(exception_flag=True)


@pytest.mark.parametrize('script,outputs', [
    ('plot_search_path.py', ['figures/search_path_LD-SDA_L2.pdf', 'figures/search_path_LD-SDA_Linf.pdf']),
    ('LDSDA_visualization.py', ['figures/LDSDA_path.pdf']),
    ('plot_computational_results.py', ['figures/computational_results_comparison.pdf']),
    ('result2latex.py', [f'latex/results_{stage}stage_ordering.tex' for stage in range(3, 10)]),
])
def test_result_scripts(script, outputs, tmp_path):
    # Generate into scratch so published figures and tables remain intact.
    shutil.copy2(ROOT / script, tmp_path / script)
    (tmp_path / 'results').symlink_to(ROOT / 'results', target_is_directory=True)
    (tmp_path / 'figures').mkdir()
    (tmp_path / 'latex').mkdir()
    result = subprocess.run(
        [sys.executable, str(tmp_path / script)], cwd=tmp_path,
        env={**os.environ, 'MPLBACKEND': 'Agg', 'MPLCONFIGDIR': str(tmp_path / 'mpl')},
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for output in outputs:
        assert (tmp_path / output).stat().st_size > 100
