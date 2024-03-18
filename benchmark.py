import sys
from pyomo.environ import *
from pyomo.dae import *
from pyomo.gdp import Disjunct
import pyomo.contrib.gdpopt.enumerate
from datetime import datetime
import os
import json

# =================================================================================================
# from models.three_stage_dynamic_model_switching import build_model

# example = "three_stage_dynamic_model_switching"
# timelimit = 900
# =================================================================================================
from models.three_stage_dynamic_model_switching_ordering import build_model

example = "three_stage_dynamic_model_switching"
timelimit = 900
# =================================================================================================
# from models.four_stage_dynamic_model_switching_nonlinear import build_model

# example = "four_stage_dynamic_model_switching_nonlinear"
# timelimit = 900

# =================================================================================================
# from models.five_stage_dynamic_model_switching_nonlinear import build_model

# example = "five_stage_dynamic_model_switching_nonlinear"
# timelimit = 900
# =================================================================================================
# from models.six_stage_dynamic_model_switching_nonlinear import build_model

# example = "six_stage_dynamic_model_switching_nonlinear"
# timelimit = 900
# =================================================================================================
# from models.seven_stage_dynamic_model_switching_nonlinear import build_model

# example = "seven_stage_dynamic_model_switching_nonlinear"
# timelimit = 1800
# =================================================================================================
# from models.eight_stage_dynamic_model_switching_nonlinear import build_model

# example = "eight_stage_dynamic_model_switching_nonlinear"
# timelimit = 1800
# =================================================================================================
# from models.nine_stage_dynamic_model_switching_nonlinear import build_model

# example = "nine_stage_dynamic_model_switching_nonlinear"
# timelimit = 3600
# =================================================================================================
# from models.ten_stage_dynamic_model_switching_nonlinear import build_model

# example = "ten_stage_dynamic_model_switching_nonlinear"
# timelimit = 3600
# =================================================================================================
nfe = 30
current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
result_dir = 'results/' + example + '/' + 'nfe' + str(nfe) + '/' + current_time
os.makedirs(result_dir, exist_ok=True)

MIP_solver = 'gurobi'
MINLP_solvers = ['dicopt', 'knitro', 'baron']
NLP_solvers = ['ipopth', 'knitro', 'conopt', 'baron']

strategy_list = [
    'gdp.bigm',
    'gdp.hull',
    'gdpopt.enumerate',
    'gdpopt.loa',
    'gdpopt.gloa',
    'gdpopt.ldsda',
]

json_result = {}


def get_and_discretize_model(mode_transfer=False):
    # Build the dynamic model
    model = build_model(mode_transfer)

    # Discretize the model using dae.collocation
    discretizer = TransformationFactory('dae.collocation')
    discretizer.apply_to(model, nfe=nfe, ncp=3, scheme='LAGRANGE-RADAU')
    # We need to reconstruct the constraints in disjuncts after discretization.
    # This is a bug in Pyomo.dae. https://github.com/Pyomo/pyomo/issues/3101
    for disjunct in model.component_data_objects(ctype=Disjunct):
        for constraint in disjunct.component_objects(ctype=Constraint):
            constraint._constructed = False
            constraint.construct()

    for dxdt in model.component_data_objects(ctype=Var, descend_into=True):
        if 'dxdt' in dxdt.name:
            dxdt.setlb(-300)
            dxdt.setub(300)

    return model


stdout = sys.stdout
for strategy in strategy_list:
    # Solve the dynamic optimization problem
    if strategy in ['gdp.bigm', 'gdp.hull']:
        for MINLP_solver in MINLP_solvers:
            print('Benchmarking', strategy, MINLP_solver)
            model = get_and_discretize_model()
            # Reformulation
            model.BigM = Suffix(direction=Suffix.LOCAL)
            model.BigM[None] = 1000000
            TransformationFactory(strategy).apply_to(model)
            with open(
                result_dir + '/' + strategy + '_' + MINLP_solver + '.log', 'w'
            ) as sys.stdout:
                solver = SolverFactory("gams")
                add_options = ['option reslim=' + str(timelimit) + ';']
                if MINLP_solver == 'dicopt':
                    add_options.append('GAMS_MODEL.optfile=1')
                    add_options.append('$onecho > dicopt.opt')
                    add_options.append('stop 1')
                    add_options.append('$offecho')
                if MINLP_solver == 'knitro':
                    add_options.append('GAMS_MODEL.optfile=1')
                    add_options.append('$onecho > knitro.opt')
                    add_options.append('mip_multistart 1')
                    add_options.append('$offecho')
                results = solver.solve(
                    model, tee=True, solver=MINLP_solver, add_options=add_options
                )
                print(results)
            sys.stdout = stdout
            with open(
                result_dir + '/' + strategy + '_' + MINLP_solver + '.json', 'w'
            ) as f:
                json.dump(results.json_repn(), f)
    elif strategy in ['gdpopt.loa', 'gdpopt.gloa', 'gdpopt.enumerate']:
        for NLP_solver in NLP_solvers:
            print('Benchmarking', strategy, NLP_solver)
            model = get_and_discretize_model()
            solver = SolverFactory(strategy)
            with open(
                result_dir + '/' + strategy + '_' + NLP_solver + '.log', 'w'
            ) as sys.stdout:
                results = solver.solve(
                    model,
                    tee=True,
                    nlp_solver='gams',
                    nlp_solver_args=dict(solver=NLP_solver),
                    mip_solver=MIP_solver,
                    time_limit=timelimit,
                )
                print(results)
            sys.stdout = stdout
            with open(
                result_dir + '/' + strategy + '_' + NLP_solver + '.json', 'w'
            ) as f:
                json.dump(results.json_repn(), f)
    elif strategy == 'gdpopt.lbb':
        for MINLP_solver in MINLP_solvers:
            # DICOPT does not work with gdpopt.lbb
            if MINLP_solver == 'dicopt':
                continue
            print('Benchmarking', strategy, MINLP_solver)
            model = get_and_discretize_model()
            solver = SolverFactory(strategy)
            with open(
                result_dir + '/' + strategy + '_' + MINLP_solver + '.log', 'w'
            ) as sys.stdout:
                results = solver.solve(
                    model,
                    tee=True,
                    minlp_solver='gams',
                    minlp_solver_args=dict(solver=MINLP_solver),
                    time_limit=timelimit,
                )
                print(results)
            sys.stdout = stdout
            with open(
                result_dir + '/' + strategy + '_' + MINLP_solver + '.json', 'w'
            ) as f:
                json.dump(results.json_repn(), f)
    elif strategy == 'gdpopt.ldsda':
        for NLP_solver in NLP_solvers:
            print('Benchmarking', strategy, NLP_solver)
            mode_transfer_list = [False, True]
            direction_norm_list = ['L2', 'Linf']
            for mode_transfer in mode_transfer_list:
                for direction_norm in direction_norm_list:
                    model = get_and_discretize_model(mode_transfer)
                    solver = SolverFactory(strategy)
                    if mode_transfer:
                        if "three" in example:
                            continue
                        with open(
                            result_dir
                            + '/'
                            + strategy
                            + '_'
                            + NLP_solver
                            + '_'
                            + str(direction_norm)
                            + '_mode_transfer'
                            + '.log',
                            'w',
                        ) as sys.stdout:
                            results = solver.solve(
                                model,
                                tee=True,
                                direction_norm=direction_norm,
                                minlp_solver='gams',
                                minlp_solver_args=dict(solver=NLP_solver),
                                starting_point=[1, 2],
                                logical_constraint_list=[
                                    model.mode_transfer_lc1.name,
                                    model.mode_transfer_lc2.name,
                                ],
                                time_limit=timelimit,
                            )
                            print(results)
                    else:
                        if 'three' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                            ]
                            starting_point = [1, 1, 1]
                        elif 'four' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                            ]
                            starting_point = [1, 2, 3, 3]
                        elif 'five' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                                model.d[5].name,
                            ]
                            starting_point = [1, 2, 3, 3, 3]
                        elif 'six' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                                model.d[5].name,
                                model.d[6].name,
                            ]
                            starting_point = [1, 2, 3, 3, 3, 3]
                        elif 'seven' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                                model.d[5].name,
                                model.d[6].name,
                                model.d[7].name,
                            ]
                            starting_point = [1, 2, 3, 3, 3, 3, 3]
                        elif 'eight' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                                model.d[5].name,
                                model.d[6].name,
                                model.d[7].name,
                                model.d[8].name,
                            ]
                            starting_point = [1, 2, 3, 3, 3, 3, 3, 3]
                        elif 'nine' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                                model.d[5].name,
                                model.d[6].name,
                                model.d[7].name,
                                model.d[8].name,
                                model.d[9].name,
                            ]
                            starting_point = [1, 2, 3, 3, 3, 3, 3, 3, 3]
                        elif 'ten' in example:
                            disjunction_list = [
                                model.d[1].name,
                                model.d[2].name,
                                model.d[3].name,
                                model.d[4].name,
                                model.d[5].name,
                                model.d[6].name,
                                model.d[7].name,
                                model.d[8].name,
                                model.d[9].name,
                                model.d[10].name,
                            ]
                            starting_point = [1, 2, 3, 3, 3, 3, 3, 3, 3, 3]
                        with open(
                            result_dir
                            + '/'
                            + strategy
                            + '_'
                            + NLP_solver
                            + '_'
                            + str(direction_norm)
                            + '.log',
                            'w',
                        ) as sys.stdout:
                            results = solver.solve(
                                model,
                                tee=True,
                                direction_norm=direction_norm,
                                minlp_solver='gams',
                                minlp_solver_args=dict(solver=NLP_solver),
                                starting_point=starting_point,
                                disjunction_list=disjunction_list,
                                time_limit=timelimit,
                            )
                            print(results)
                    sys.stdout = stdout
                    with open(
                        result_dir
                        + '/'
                        + strategy
                        + '_'
                        + NLP_solver
                        + '_'
                        + str(direction_norm)
                        + '.json',
                        'w',
                    ) as f:
                        json.dump(results.json_repn(), f)
