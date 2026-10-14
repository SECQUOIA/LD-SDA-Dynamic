"""Exercise the actual runner boundary without requiring GAMS licenses."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import benchmark


def options(*extra):
    return benchmark.parse_args(['--stages', '4', '--nfe', '2', '--ncp', '2',
                                 '--strategies', 'gdpopt.ldsda', '--nlp-solvers', 'baron', *extra])


@pytest.mark.parametrize('stages', range(3, 11))
@pytest.mark.parametrize('mode_transfer', [False, True])
def test_ldsda_options_use_real_components(stages, mode_transfer):
    if stages == 3 and mode_transfer:
        return  # No mode-transfer formulation exists for the three-stage models.
    args = options('--stages', str(stages))
    case = benchmark.Case('gdpopt.ldsda', 'baron', mode_transfer, 'L2')
    model, solver, kwargs = benchmark.prepare_case(args, case)
    config = solver.CONFIG(kwargs)
    if mode_transfer:
        assert list(config.logical_constraint_list) == [model.mode_transfer_lc1, model.mode_transfer_lc2]
        assert config.starting_point == [1, 2]
    else:
        assert list(config.disjunction_list) == [model.d[stage] for stage in model.stage]
        assert len(config.starting_point) == stages
    # The same API rejects the strings used by the historical runner (issue #5).
    key = 'logical_constraint_list' if mode_transfer else 'disjunction_list'
    with pytest.raises(ValueError, match='invalid value'):
        solver.CONFIG({key: [component.name for component in getattr(config, key)]})
    # Exercise the setup stage that plugin-availability checks missed: this
    # requires SymPy, even before an external NLP solver is called.
    benchmark.TransformationFactory('core.logical_to_linear').apply_to(model)


@pytest.mark.parametrize('strategy', benchmark.STRATEGIES)
def test_every_strategy_prepares_and_validates(strategy):
    args = options('--strategies', strategy)
    benchmark.prepare_case(args, benchmark.Case(strategy, 'baron', False,
                                               'Linf' if strategy == 'gdpopt.ldsda' else None))


class Result:
    def __init__(self, marker):
        self.marker = marker

    def json_repn(self):
        return {'case': self.marker}


def fake_solver(monkeypatch, fail=False):
    class Solver:
        def solve(self, model, **kwargs):
            print('solver output')
            if fail:
                raise RuntimeError('deliberate solver failure')
            return Result(kwargs['marker'])
    monkeypatch.setattr(benchmark, 'check_solvers', lambda args, cases: '/mock/gams')
    monkeypatch.setattr(benchmark, 'prepare_case', lambda args, case: (None, Solver(), {'marker': case.stem}))


def test_mode_transfer_results_and_repeated_runs_are_distinct(tmp_path, monkeypatch):
    fake_solver(monkeypatch)
    args = options('--output-dir', str(tmp_path))
    first = benchmark.run_benchmarks(args)
    second = benchmark.run_benchmarks(args)
    assert first != second
    stems = {case.stem for case in benchmark.cases_for(args)}
    assert len(stems) == 4
    for directory in (first, second):
        assert {p.stem for p in directory.glob('*.log')} == stems
        assert {p.stem for p in directory.glob('*.json')} == stems | {'run'}
        for stem in stems:
            assert json.loads((directory / f'{stem}.json').read_text()) == {'case': stem}
        metadata = json.loads((directory / 'run.json').read_text())
        assert metadata['status'] == 'complete'
        assert set(metadata['completed']) == stems


def test_failed_solver_preserves_log_metadata_and_stdout(tmp_path, monkeypatch):
    fake_solver(monkeypatch, fail=True)
    original_stdout = sys.stdout
    args = options('--output-dir', str(tmp_path))
    with pytest.raises(RuntimeError, match='deliberate solver failure'):
        benchmark.run_benchmarks(args)
    assert sys.stdout is original_stdout
    directory, = tmp_path.iterdir()
    metadata = json.loads((directory / 'run.json').read_text())
    assert metadata['status'] == 'failed'
    assert metadata['completed'] == []
    log, = directory.glob('*.log')
    assert 'deliberate solver failure' in log.read_text()
    assert set(p.name for p in directory.glob('*.json')) == {'run.json'}


def test_missing_gams_fails_before_creating_output(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark.shutil, 'which', lambda name: None)
    args = options('--output-dir', str(tmp_path / 'runs'))
    with pytest.raises(RuntimeError, match='GAMS is not on PATH'):
        benchmark.run_benchmarks(args)
    assert not (tmp_path / 'runs').exists()


def test_gams_registry_checks_selected_solvers(tmp_path, monkeypatch):
    executable = tmp_path / 'gams'
    executable.touch()
    (tmp_path / 'gmscmpun.txt').write_text('BARON 111 5 BA 1 0 1 NLP MINLP\n')
    monkeypatch.setattr(benchmark.shutil, 'which', lambda name: str(executable))
    args = options()
    assert benchmark.check_solvers(args, benchmark.cases_for(args)) == str(executable)
    args = options('--nlp-solvers', 'missing')
    with pytest.raises(RuntimeError, match='MISSING'):
        benchmark.check_solvers(args, benchmark.cases_for(args))


@pytest.mark.parametrize('directory', ['results', 'models', 'figures', 'latex', 'paper'])
def test_rejects_outputs_inside_paper_artifacts(directory):
    with pytest.raises(ValueError, match='frozen'):
        benchmark.output_root(benchmark.ROOT / directory / 'new')


def test_shell_launcher_forwards_arguments_and_failure(tmp_path):
    interpreter = tmp_path / 'python with spaces'
    interpreter.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nexit 7\n')
    interpreter.chmod(0o755)
    result = subprocess.run(['sh', str(benchmark.ROOT / 'run.sh'), '--stages', '4'],
                            cwd=tmp_path, env={**os.environ, 'PYTHON': str(interpreter)},
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 7
    assert result.stdout.splitlines() == [str(benchmark.ROOT / 'benchmark.py'), '--stages', '4']


def test_real_cli_dry_run_needs_no_solvers_and_writes_no_results(tmp_path):
    result = subprocess.run([sys.executable, str(benchmark.ROOT / 'benchmark.py'),
                             '--stages', '4', '--strategies', 'gdpopt.ldsda', '--nlp-solvers', 'baron',
                             '--nfe', '2', '--ncp', '2', '--dry-run'], cwd=tmp_path,
                            text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'gdpopt.ldsda_baron_L2_mode_transfer' in result.stdout
    assert not list(tmp_path.iterdir())


def test_rejects_solver_option_injection_and_invalid_formulation():
    for flags in [('--nlp-solvers', 'baron;option'), ('--stages', '3', '--mode-transfer', 'on')]:
        with pytest.raises(SystemExit):
            options(*flags)
