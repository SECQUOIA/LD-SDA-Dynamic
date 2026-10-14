"""Run maintained benchmarks without modifying the frozen paper artifacts."""

import argparse
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import importlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

from pyomo.environ import Constraint, SolverFactory, Suffix, TransformationFactory, Var
from pyomo.gdp import Disjunct
import pyomo.contrib.gdpopt.enumerate

ROOT = Path(__file__).resolve().parent
STAGE_NAMES = {3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven',
               8: 'eight', 9: 'nine', 10: 'ten'}
STRATEGIES = ('gdp.bigm', 'gdp.hull', 'gdpopt.enumerate', 'gdpopt.loa',
              'gdpopt.gloa', 'gdpopt.ldsda', 'gdpopt.lbb')


@dataclass(frozen=True)
class Case:
    strategy: str
    solver: str
    mode_transfer: bool = False
    direction_norm: str | None = None

    @property
    def stem(self):
        suffix = f'_{self.direction_norm}' if self.direction_norm else ''
        suffix += '_mode_transfer' if self.mode_transfer else ''
        return f'{self.strategy}_{self.solver}{suffix}'


def model_name(stages, unordered=False):
    if stages == 3:
        return 'three_stage_dynamic_model_switching' + ('' if unordered else '_ordering')
    return f'{STAGE_NAMES[stages]}_stage_dynamic_model_switching_nonlinear'


def discretize_model(model, nfe=30, ncp=3):
    TransformationFactory('dae.collocation').apply_to(
        model, nfe=nfe, ncp=ncp, scheme='LAGRANGE-RADAU'
    )
    # Preserve the benchmark workaround for Pyomo.DAE issue #3101.
    for disjunct in model.component_data_objects(Disjunct):
        for constraint in disjunct.component_objects(Constraint):
            constraint._constructed = False
            constraint.construct()
    for variable in model.component_data_objects(Var, descend_into=True):
        if 'dxdt' in variable.name:
            variable.setlb(-300)
            variable.setub(300)
    return model


def get_and_discretize_model(args, mode_transfer=False):
    module = importlib.import_module(f'models.{model_name(args.stages, args.unordered)}')
    return discretize_model(module.build_model(mode_transfer), args.nfe, args.ncp)


def cases_for(args):
    cases = []
    for strategy in dict.fromkeys(args.strategies):
        if strategy in ('gdp.bigm', 'gdp.hull', 'gdpopt.lbb'):
            cases.extend(Case(strategy, solver) for solver in dict.fromkeys(args.minlp_solvers)
                         if not (strategy == 'gdpopt.lbb' and solver == 'dicopt'))
        elif strategy == 'gdpopt.ldsda':
            modes = [False, True] if args.mode_transfer == 'both' else [args.mode_transfer == 'on']
            for solver in dict.fromkeys(args.nlp_solvers):
                for mode in modes:
                    if mode and args.stages == 3:
                        continue
                    cases.extend(Case(strategy, solver, mode, norm)
                                 for norm in dict.fromkeys(args.norms))
        else:
            cases.extend(Case(strategy, solver) for solver in dict.fromkeys(args.nlp_solvers))
    return cases


def gams_args(solver, time_limit=None):
    options = ['option threads=1;']
    if time_limit is not None:
        options.append(f'option reslim={time_limit};')
    if solver == 'dicopt':
        options += ['GAMS_MODEL.optfile=1', '$onecho > dicopt.opt', 'stop 1', '$offecho']
    if solver == 'knitro':
        options += ['GAMS_MODEL.optfile=1', '$onecho > knitro.opt', 'mip_multistart 1', '$offecho']
    return {'solver': solver, 'add_options': options}


def solver_options(model, case, args):
    if case.strategy in ('gdp.bigm', 'gdp.hull'):
        return {'tee': True, **gams_args(case.solver, args.time_limit)}
    options = {'tee': True, 'time_limit': args.time_limit}
    if case.strategy in ('gdpopt.ldsda', 'gdpopt.lbb'):
        options.update(minlp_solver='gams', minlp_solver_args=gams_args(case.solver))
    else:
        options.update(nlp_solver='gams', nlp_solver_args=gams_args(case.solver),
                       mip_solver='gams', mip_solver_args=gams_args(args.mip_solver))
    if case.strategy == 'gdpopt.ldsda':
        options['direction_norm'] = case.direction_norm
        if case.mode_transfer:
            options.update(starting_point=[1, 2], logical_constraint_list=[
                model.mode_transfer_lc1, model.mode_transfer_lc2,
            ])
        else:
            options['starting_point'] = ([1] * 3 if args.stages == 3 else
                                         [1, 2] + [3] * (args.stages - 2))
            # Pyomo expects component objects, not their string names (issue #5).
            options['disjunction_list'] = [model.d[stage] for stage in model.stage]
    return options


def prepare_case(args, case):
    model = get_and_discretize_model(args, case.mode_transfer)
    if case.strategy in ('gdp.bigm', 'gdp.hull'):
        model.BigM = Suffix(direction=Suffix.LOCAL)
        model.BigM[None] = 1000000
        TransformationFactory(case.strategy).apply_to(model)
        solver = SolverFactory('gams')
    else:
        solver = SolverFactory(case.strategy)
    options = solver_options(model, case, args)
    if case.strategy.startswith('gdpopt.'):
        solver.CONFIG(options)  # Validate the real GDPopt boundary without solving.
    return model, solver, options


def check_solvers(args, cases):
    executable = shutil.which('gams')
    if executable is None:
        raise RuntimeError('GAMS is not on PATH. Install/configure GAMS or use --dry-run.')
    registry = Path(executable).resolve().with_name('gmscmpun.txt')
    if not registry.is_file():
        raise RuntimeError(f'Cannot verify installed GAMS solvers: missing {registry}')
    installed = set(re.findall(r'^([A-Z][A-Z0-9_]*)\s+\d+\s', registry.read_text(), re.M))
    requested = {case.solver.upper() for case in cases}
    if any(case.strategy in ('gdpopt.loa', 'gdpopt.gloa', 'gdpopt.enumerate') for case in cases):
        requested.add(args.mip_solver.upper())
    missing = requested - installed
    if missing:
        raise RuntimeError('Solvers not registered in this GAMS installation: ' + ', '.join(sorted(missing)))
    # Registration is checked here; GAMS checks solver licenses at solve time.
    return str(Path(executable).resolve())


def output_root(value):
    root = Path(value).resolve()
    for name in ('models', 'results', 'figures', 'latex', 'paper'):
        frozen = ROOT / name
        if root == frozen or frozen in root.parents:
            raise ValueError(f'New runs must be outside the frozen {name}/ directory.')
    return root


def write_json(path, data, mode='x'):
    with path.open(mode, encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')


def run_benchmarks(args):
    cases = cases_for(args)
    if not cases:
        raise ValueError('No applicable cases were selected.')
    if args.dry_run:
        for case in cases:
            prepare_case(args, case)
            print(case.stem)
        return None
    root = output_root(args.output_dir)
    executable = check_solvers(args, cases)
    root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=model_name(args.stages, args.unordered) + '_', dir=root))
    try:
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                  capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout)
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    metadata = {'created_at': datetime.now(timezone.utc).isoformat(), 'revision': revision,
                'working_tree_dirty': dirty, 'python': sys.version, 'gams_executable': executable,
                'packages': {name: version(name) for name in ('pyomo', 'sympy', 'numpy', 'pandas')},
                'configuration': vars(args), 'cases': [asdict(case) for case in cases],
                'completed': [], 'status': 'running'}
    metadata_path = directory / 'run.json'
    write_json(metadata_path, metadata)
    print(f'Results: {directory}', flush=True)
    try:
        for case in cases:
            print(f'Benchmarking {case.stem}', flush=True)
            # Exclusive creation also protects against an accidental repeated case.
            with (directory / f'{case.stem}.log').open('x', encoding='utf-8') as log:
                with redirect_stdout(log):
                    try:
                        model, solver, options = prepare_case(args, case)
                        results = solver.solve(model, **options)
                        print(results)
                    except Exception:
                        traceback.print_exc(file=log)
                        raise
            write_json(directory / f'{case.stem}.json', results.json_repn())
            metadata['completed'].append(case.stem)
            write_json(metadata_path, metadata, 'w')
        metadata['status'] = 'complete'
    except Exception as error:
        metadata['status'] = 'failed'
        metadata['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        write_json(metadata_path, metadata, 'w')
    return directory


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stages', type=int, choices=STAGE_NAMES, default=3)
    parser.add_argument('--unordered', action='store_true', help='Use the original unordered three-stage model.')
    parser.add_argument('--strategies', nargs='+', choices=STRATEGIES, default=list(STRATEGIES[:-1]))
    parser.add_argument('--minlp-solvers', nargs='+', default=['dicopt', 'knitro', 'baron'])
    parser.add_argument('--nlp-solvers', nargs='+', default=['ipopth', 'knitro', 'conopt', 'baron'])
    parser.add_argument('--mip-solver', default='gurobi', help='GAMS MIP subsolver for decomposition methods.')
    parser.add_argument('--mode-transfer', choices=('off', 'on', 'both'), default='both')
    parser.add_argument('--norms', nargs='+', choices=('L2', 'Linf'), default=['L2', 'Linf'])
    parser.add_argument('--nfe', type=positive_int, default=30)
    parser.add_argument('--ncp', type=positive_int, default=3)
    parser.add_argument('--time-limit', type=positive_int, help='Seconds per case; default: 900/1800/3600 by stage count.')
    parser.add_argument('--output-dir', default='benchmark-runs')
    parser.add_argument('--dry-run', action='store_true', help='Build and validate selected cases without external solvers or outputs.')
    args = parser.parse_args(argv)
    if args.unordered and args.stages != 3:
        parser.error('--unordered applies only to --stages 3')
    if args.stages == 3 and args.mode_transfer == 'on':
        parser.error('mode-transfer reformulation requires at least four stages')
    # Solver names become GAMS option values and filenames; reject arbitrary text.
    for name in [*args.minlp_solvers, *args.nlp_solvers, args.mip_solver]:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
            parser.error(f'Invalid GAMS solver name: {name!r}')
    if args.time_limit is None:
        args.time_limit = 900 if args.stages <= 6 else 1800 if args.stages <= 8 else 3600
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        run_benchmarks(args)
    except (RuntimeError, ValueError, OSError) as error:
        print(f'Benchmark failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
