from pyomo.environ import *
from pyomo.dae import *
from pyomo.gdp import Disjunct, Disjunction
import pyomo.contrib.gdpopt.enumerate
from pyomo.contrib.fbbt.fbbt import fbbt


def build_model(mode_transfer=False):
    model = ConcreteModel()

    # Set
    model.stage = Set(initialize=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    model.mode = Set(initialize=[1, 2, 3])

    model.t1 = ContinuousSet(bounds=(0, 1))
    model.t2 = ContinuousSet(bounds=(1, 2))
    model.t3 = ContinuousSet(bounds=(2, 3))
    model.t4 = ContinuousSet(bounds=(3, 4))
    model.t5 = ContinuousSet(bounds=(4, 5))
    model.t6 = ContinuousSet(bounds=(5, 6))
    model.t7 = ContinuousSet(bounds=(6, 7))
    model.t8 = ContinuousSet(bounds=(7, 8))
    model.t9 = ContinuousSet(bounds=(8, 9))
    model.t10 = ContinuousSet(bounds=(9, 10))

    # Variables
    model.x1 = Var(model.t1, bounds=(0, 10))
    model.x2 = Var(model.t2, bounds=(0, 10))
    model.x3 = Var(model.t3, bounds=(0, 10))
    model.x4 = Var(model.t4, bounds=(0, 10))
    model.x5 = Var(model.t5, bounds=(0, 10))
    model.x6 = Var(model.t6, bounds=(0, 10))
    model.x7 = Var(model.t7, bounds=(0, 10))
    model.x8 = Var(model.t8, bounds=(0, 10))
    model.x9 = Var(model.t9, bounds=(0, 10))
    model.x10 = Var(model.t10, bounds=(0, 10))

    model.u1 = Var(bounds=(-4, 4))
    model.u2 = Var(bounds=(-4, 4))
    model.u3 = Var(bounds=(-4, 4))
    model.u4 = Var(bounds=(-4, 4))
    model.u5 = Var(bounds=(-4, 4))
    model.u6 = Var(bounds=(-4, 4))
    model.u7 = Var(bounds=(-4, 4))
    model.u8 = Var(bounds=(-4, 4))
    model.u9 = Var(bounds=(-4, 4))
    model.u10 = Var(bounds=(-4, 4))

    # Dynamic model
    model.dxdt1 = DerivativeVar(model.x1, wrt=model.t1)
    model.dxdt2 = DerivativeVar(model.x2, wrt=model.t2)
    model.dxdt3 = DerivativeVar(model.x3, wrt=model.t3)
    model.dxdt4 = DerivativeVar(model.x4, wrt=model.t4)
    model.dxdt5 = DerivativeVar(model.x5, wrt=model.t5)
    model.dxdt6 = DerivativeVar(model.x6, wrt=model.t6)
    model.dxdt7 = DerivativeVar(model.x7, wrt=model.t7)
    model.dxdt8 = DerivativeVar(model.x8, wrt=model.t8)
    model.dxdt9 = DerivativeVar(model.x9, wrt=model.t9)
    model.dxdt10 = DerivativeVar(model.x10, wrt=model.t10)

    # logic constraint
    model.stage_mode = Disjunct(model.stage * model.mode)
    model.d = Disjunction(model.stage)

    # Stage 1

    def stage1_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt1[t] == -model.x1[t] * exp(model.x1[t] - 1) + model.u1

    model.stage_mode[1, 1].mode1_dynamic_constraint = Constraint(
        model.t1, rule=stage1_mode1_dynamic
    )

    def stage1_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt1[t] == (0.5 * model.x1[t] ** 3 + model.u1) / 20

    model.stage_mode[1, 2].mode2_dynamic_constraint = Constraint(
        model.t1, rule=stage1_mode2_dynamic
    )

    def stage1_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt1[t] == (model.x1[t] ** 2 + model.u1) / (t + 20)

    model.stage_mode[1, 3].mode3_dynamic_constraint = Constraint(
        model.t1, rule=stage1_mode3_dynamic
    )

    # Stage 2

    def stage2_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt2[t] == -model.x2[t] * exp(model.x2[t] - 1) + model.u2

    model.stage_mode[2, 1].mode1_dynamic_constraint = Constraint(
        model.t2, rule=stage2_mode1_dynamic
    )

    def stage2_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt2[t] == (0.5 * model.x2[t] ** 3 + model.u2) / 20

    model.stage_mode[2, 2].mode2_dynamic_constraint = Constraint(
        model.t2, rule=stage2_mode2_dynamic
    )

    def stage2_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt2[t] == (model.x2[t] ** 2 + model.u2) / (t + 20)

    model.stage_mode[2, 3].mode3_dynamic_constraint = Constraint(
        model.t2, rule=stage2_mode3_dynamic
    )

    # Stage 3

    def stage3_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt3[t] == -model.x3[t] * exp(model.x3[t] - 1) + model.u3

    model.stage_mode[3, 1].mode1_dynamic_constraint = Constraint(
        model.t3, rule=stage3_mode1_dynamic
    )

    def stage3_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt3[t] == (0.5 * model.x3[t] ** 3 + model.u3) / 20

    model.stage_mode[3, 2].mode2_dynamic_constraint = Constraint(
        model.t3, rule=stage3_mode2_dynamic
    )

    def stage3_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt3[t] == (model.x3[t] ** 2 + model.u3) / (t + 20)

    model.stage_mode[3, 3].mode3_dynamic_constraint = Constraint(
        model.t3, rule=stage3_mode3_dynamic
    )

    # Stage 4

    def stage4_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt4[t] == -model.x4[t] * exp(model.x4[t] - 1) + model.u4

    model.stage_mode[4, 1].mode1_dynamic_constraint = Constraint(
        model.t4, rule=stage4_mode1_dynamic
    )

    def stage4_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt4[t] == (0.5 * model.x4[t] ** 3 + model.u4) / 20

    model.stage_mode[4, 2].mode2_dynamic_constraint = Constraint(
        model.t4, rule=stage4_mode2_dynamic
    )

    def stage4_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt4[t] == (model.x4[t] ** 2 + model.u4) / (t + 20)

    model.stage_mode[4, 3].mode3_dynamic_constraint = Constraint(
        model.t4, rule=stage4_mode3_dynamic
    )

    # Stage 5

    def stage5_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt5[t] == -model.x5[t] * exp(model.x5[t] - 1) + model.u5

    model.stage_mode[5, 1].mode1_dynamic_constraint = Constraint(
        model.t5, rule=stage5_mode1_dynamic
    )

    def stage5_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt5[t] == (0.5 * model.x5[t] ** 3 + model.u5) / 20

    model.stage_mode[5, 2].mode2_dynamic_constraint = Constraint(
        model.t5, rule=stage5_mode2_dynamic
    )

    def stage5_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt5[t] == (model.x5[t] ** 2 + model.u5) / (t + 20)

    model.stage_mode[5, 3].mode3_dynamic_constraint = Constraint(
        model.t5, rule=stage5_mode3_dynamic
    )

    # Stage 6

    def stage6_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt6[t] == -model.x6[t] * exp(model.x6[t] - 1) + model.u6

    model.stage_mode[6, 1].mode1_dynamic_constraint = Constraint(
        model.t6, rule=stage6_mode1_dynamic
    )

    def stage6_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt6[t] == (0.5 * model.x6[t] ** 3 + model.u6) / 20

    model.stage_mode[6, 2].mode2_dynamic_constraint = Constraint(
        model.t6, rule=stage6_mode2_dynamic
    )

    def stage6_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt6[t] == (model.x6[t] ** 2 + model.u6) / (t + 20)

    model.stage_mode[6, 3].mode3_dynamic_constraint = Constraint(
        model.t6, rule=stage6_mode3_dynamic
    )

    # Stage 7

    def stage7_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt7[t] == -model.x7[t] * exp(model.x7[t] - 1) + model.u7

    model.stage_mode[7, 1].mode1_dynamic_constraint = Constraint(
        model.t7, rule=stage7_mode1_dynamic
    )

    def stage7_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt7[t] == (0.5 * model.x7[t] ** 3 + model.u7) / 20

    model.stage_mode[7, 2].mode2_dynamic_constraint = Constraint(
        model.t7, rule=stage7_mode2_dynamic
    )

    def stage7_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt7[t] == (model.x7[t] ** 2 + model.u7) / (t + 20)

    model.stage_mode[7, 3].mode3_dynamic_constraint = Constraint(
        model.t7, rule=stage7_mode3_dynamic
    )

    # Stage 8

    def stage8_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt8[t] == -model.x8[t] * exp(model.x8[t] - 1) + model.u8

    model.stage_mode[8, 1].mode1_dynamic_constraint = Constraint(
        model.t8, rule=stage8_mode1_dynamic
    )

    def stage8_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt8[t] == (0.5 * model.x8[t] ** 3 + model.u8) / 20

    model.stage_mode[8, 2].mode2_dynamic_constraint = Constraint(
        model.t8, rule=stage8_mode2_dynamic
    )

    def stage8_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt8[t] == (model.x8[t] ** 2 + model.u8) / (t + 20)

    model.stage_mode[8, 3].mode3_dynamic_constraint = Constraint(
        model.t8, rule=stage8_mode3_dynamic
    )

    # Stage 9

    def stage9_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt9[t] == -model.x9[t] * exp(model.x9[t] - 1) + model.u9

    model.stage_mode[9, 1].mode1_dynamic_constraint = Constraint(
        model.t9, rule=stage9_mode1_dynamic
    )

    def stage9_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt9[t] == (0.5 * model.x9[t] ** 3 + model.u9) / 20

    model.stage_mode[9, 2].mode2_dynamic_constraint = Constraint(
        model.t9, rule=stage9_mode2_dynamic
    )

    def stage9_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt9[t] == (model.x9[t] ** 2 + model.u9) / (t + 20)

    model.stage_mode[9, 3].mode3_dynamic_constraint = Constraint(
        model.t9, rule=stage9_mode3_dynamic
    )

    # Stage 10

    def stage10_mode1_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt10[t] == -model.x10[t] * exp(model.x10[t] - 1) + model.u10

    model.stage_mode[10, 1].mode1_dynamic_constraint = Constraint(
        model.t10, rule=stage10_mode1_dynamic
    )

    def stage10_mode2_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt10[t] == (0.5 * model.x10[t] ** 3 + model.u10) / 20

    model.stage_mode[10, 2].mode2_dynamic_constraint = Constraint(
        model.t10, rule=stage10_mode2_dynamic
    )

    def stage10_mode3_dynamic(disjunct, t):
        model = disjunct.model()
        return model.dxdt10[t] == (model.x10[t] ** 2 + model.u10) / (t + 20)

    model.stage_mode[10, 3].mode3_dynamic_constraint = Constraint(
        model.t10, rule=stage10_mode3_dynamic
    )

    model.d[1] = [
        model.stage_mode[1, 1],
        model.stage_mode[1, 2],
        model.stage_mode[1, 3],
    ]
    model.d[2] = [
        model.stage_mode[2, 1],
        model.stage_mode[2, 2],
        model.stage_mode[2, 3],
    ]
    model.d[3] = [
        model.stage_mode[3, 1],
        model.stage_mode[3, 2],
        model.stage_mode[3, 3],
    ]
    model.d[4] = [
        model.stage_mode[4, 1],
        model.stage_mode[4, 2],
        model.stage_mode[4, 3],
    ]
    model.d[5] = [
        model.stage_mode[5, 1],
        model.stage_mode[5, 2],
        model.stage_mode[5, 3],
    ]
    model.d[6] = [
        model.stage_mode[6, 1],
        model.stage_mode[6, 2],
        model.stage_mode[6, 3],
    ]
    model.d[7] = [
        model.stage_mode[7, 1],
        model.stage_mode[7, 2],
        model.stage_mode[7, 3],
    ]
    model.d[8] = [
        model.stage_mode[8, 1],
        model.stage_mode[8, 2],
        model.stage_mode[8, 3],
    ]
    model.d[9] = [
        model.stage_mode[9, 1],
        model.stage_mode[9, 2],
        model.stage_mode[9, 3],
    ]
    model.d[10] = [
        model.stage_mode[10, 1],
        model.stage_mode[10, 2],
        model.stage_mode[10, 3],
    ]

    if mode_transfer:
        model.lc1 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[1, 1].indicator_var,
                model.stage_mode[1, 2].indicator_var,
                model.stage_mode[1, 3].indicator_var,
            )
        )
        model.lc2 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[2, 1].indicator_var,
                model.stage_mode[2, 2].indicator_var,
                model.stage_mode[2, 3].indicator_var,
            )
        )
        model.lc3 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[3, 1].indicator_var,
                model.stage_mode[3, 2].indicator_var,
                model.stage_mode[3, 3].indicator_var,
            )
        )
        model.lc4 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[4, 1].indicator_var,
                model.stage_mode[4, 2].indicator_var,
                model.stage_mode[4, 3].indicator_var,
            )
        )
        model.lc5 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[5, 1].indicator_var,
                model.stage_mode[5, 2].indicator_var,
                model.stage_mode[5, 3].indicator_var,
            )
        )
        model.lc6 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[6, 1].indicator_var,
                model.stage_mode[6, 2].indicator_var,
                model.stage_mode[6, 3].indicator_var,
            )
        )
        model.lc7 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[7, 1].indicator_var,
                model.stage_mode[7, 2].indicator_var,
                model.stage_mode[7, 3].indicator_var,
            )
        )
        model.lc8 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[8, 1].indicator_var,
                model.stage_mode[8, 2].indicator_var,
                model.stage_mode[8, 3].indicator_var,
            )
        )
        model.lc9 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[9, 1].indicator_var,
                model.stage_mode[9, 2].indicator_var,
                model.stage_mode[9, 3].indicator_var,
            )
        )
        model.lc10 = LogicalConstraint(
            expr=exactly(
                1,
                model.stage_mode[10, 1].indicator_var,
                model.stage_mode[10, 2].indicator_var,
                model.stage_mode[10, 3].indicator_var,
            )
        )

        model.transfer_stage = Set(initialize=[2, 3, 4, 5, 6, 7, 8, 9, 10])
        model.mode_stransfer_set = Set(initialize=[1, 2])
        model.mode_transfer = BooleanVar(model.transfer_stage, model.mode_stransfer_set)
        model.mode_transfer_lc1 = LogicalConstraint(
            expr=exactly(
                1,
                model.mode_transfer[2, 1],
                model.mode_transfer[3, 1],
                model.mode_transfer[4, 1],
                model.mode_transfer[5, 1],
                model.mode_transfer[6, 1],
                model.mode_transfer[7, 1],
                model.mode_transfer[8, 1],
                model.mode_transfer[9, 1],
                model.mode_transfer[10, 1],
            )
        )
        model.mode_transfer_lc2 = LogicalConstraint(
            expr=exactly(
                1,
                model.mode_transfer[2, 2],
                model.mode_transfer[3, 2],
                model.mode_transfer[4, 2],
                model.mode_transfer[5, 2],
                model.mode_transfer[6, 2],
                model.mode_transfer[7, 2],
                model.mode_transfer[8, 2],
                model.mode_transfer[9, 2],
                model.mode_transfer[10, 2],
            )
        )

        def _mode_transfer_rule1(model, stage):
            return model.mode_transfer[stage, 1].equivalent_to(
                land(
                    model.stage_mode[stage - 1, 1].indicator_var,
                    model.stage_mode[stage, 2].indicator_var,
                )
            )

        model.mode_transfer2mode_choice_lc1 = LogicalConstraint(
            model.transfer_stage, rule=_mode_transfer_rule1
        )

        def _mode_transfer_rule2(model, stage):
            return model.mode_transfer[stage, 2].equivalent_to(
                land(
                    model.stage_mode[stage - 1, 2].indicator_var,
                    model.stage_mode[stage, 3].indicator_var,
                )
            )

        model.mode_transfer2mode_choice_lc2 = LogicalConstraint(
            model.transfer_stage, rule=_mode_transfer_rule2
        )

        def _mode_transfer_rule3(model, stage):
            return model.mode_transfer[stage, 2].implies(
                lor(
                    model.mode_transfer[stage1, 1]
                    for stage1 in model.transfer_stage
                    if stage1 < stage
                )
            )

        model.mode_transfer2mode_choice_lc3 = LogicalConstraint(
            model.transfer_stage, rule=_mode_transfer_rule3
        )

    # Sequence constraint
    def _sequence_rule1(model, stage):
        if stage == 1:
            return Constraint.Skip
        else:
            return model.stage_mode[stage, 2].indicator_var.implies(
                lor(
                    model.stage_mode[stage2, 1].indicator_var
                    for stage2 in model.stage
                    if stage2 < stage
                )
            )

    model.seq1 = LogicalConstraint(model.stage, rule=_sequence_rule1)
    model.stage_mode[1, 2].indicator_var.fix(False)

    def _sequence_rule2(model, stage):
        if stage == 10:
            return Constraint.Skip
        else:
            return model.stage_mode[stage, 2].indicator_var.implies(
                lnot(
                    lor(
                        model.stage_mode[stage2, 1].indicator_var
                        for stage2 in model.stage
                        if stage2 > stage
                    )
                )
            )

    model.seq2 = LogicalConstraint(model.stage, rule=_sequence_rule2)

    def _sequence_rule3(model, stage):
        if stage <= 2:
            return Constraint.Skip
        else:
            return model.stage_mode[stage, 3].indicator_var.implies(
                lor(
                    model.stage_mode[stage2, 2].indicator_var
                    for stage2 in model.stage
                    if stage2 < stage
                )
            )

    model.seq3 = LogicalConstraint(model.stage, rule=_sequence_rule3)
    model.stage_mode[1, 3].indicator_var.fix(False)
    model.stage_mode[2, 3].indicator_var.fix(False)

    def _sequence_rule4(model, stage):
        if stage == 10:
            return Constraint.Skip
        else:
            return model.stage_mode[stage, 3].indicator_var.implies(
                lnot(
                    lor(
                        model.stage_mode[stage2, 2].indicator_var
                        for stage2 in model.stage
                        if stage2 > stage
                    )
                )
            )

    model.seq4 = LogicalConstraint(model.stage, rule=_sequence_rule4)

    model.c1 = Constraint(expr=model.x1[0] == 1)
    model.c2 = Constraint(expr=model.x1[1] == model.x2[1])
    model.c3 = Constraint(expr=model.x2[2] == model.x3[2])
    model.c4 = Constraint(expr=model.x3[3] == model.x4[3])
    model.c5 = Constraint(expr=model.x4[4] == model.x5[4])
    model.c6 = Constraint(expr=model.x5[5] == model.x6[5])
    model.c7 = Constraint(expr=model.x6[6] == model.x7[6])
    model.c8 = Constraint(expr=model.x7[7] == model.x8[7])
    model.c9 = Constraint(expr=model.x8[8] == model.x9[8])
    model.c10 = Constraint(expr=model.x9[9] == model.x10[9])

    # Objective function
    model.intx1 = Integral(
        model.t1, wrt=model.t1, rule=lambda model, t: model.x1[t] ** 2
    )
    model.intx2 = Integral(
        model.t2, wrt=model.t2, rule=lambda model, t: model.x2[t] ** 2
    )
    model.intx3 = Integral(
        model.t3, wrt=model.t3, rule=lambda model, t: model.x3[t] ** 2
    )
    model.intx4 = Integral(
        model.t4, wrt=model.t4, rule=lambda model, t: model.x4[t] ** 2
    )
    model.intx5 = Integral(
        model.t5, wrt=model.t5, rule=lambda model, t: model.x5[t] ** 2
    )
    model.intx6 = Integral(
        model.t6, wrt=model.t6, rule=lambda model, t: model.x6[t] ** 2
    )
    model.intx7 = Integral(
        model.t7, wrt=model.t7, rule=lambda model, t: model.x7[t] ** 2
    )
    model.intx8 = Integral(
        model.t8, wrt=model.t8, rule=lambda model, t: model.x8[t] ** 2
    )
    model.intx9 = Integral(
        model.t9, wrt=model.t9, rule=lambda model, t: model.x9[t] ** 2
    )
    model.intx10 = Integral(
        model.t10, wrt=model.t10, rule=lambda model, t: model.x10[t] ** 2
    )

    model.obj = Objective(
        expr=-(
            model.intx1
            + model.intx2
            + model.intx3
            + model.intx4
            + model.intx5
            + model.intx6
            + model.intx7
            + model.intx8
            + model.intx9
            + model.intx10
        ),
        sense=minimize,
    )
    return model
