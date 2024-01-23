from pyomo.environ import *
from pyomo.dae import *
from pyomo.gdp import Disjunct, Disjunction


model = ConcreteModel()

# Set
model.stage = Set(initialize=[1, 2, 3])
model.mode = Set(initialize=[1, 2])

model.t1 = ContinuousSet(bounds=(0, 1))
model.t2 = ContinuousSet(bounds=(1, 2))
model.t3 = ContinuousSet(bounds=(2, 3))

# Variables
model.x1 = Var(model.t1, bounds=(0, 10))
model.x2 = Var(model.t2, bounds=(0, 10))
model.x3 = Var(model.t3, bounds=(0, 10))
model.u1 = Var(model.t1, bounds=(-4, 4))
model.u2 = Var(model.t2, bounds=(-4, 4))
model.u3 = Var(model.t3, bounds=(-4, 4))

# Dynamic model
model.dxdt1 = DerivativeVar(model.x1, wrt=model.t1)
model.dxdt2 = DerivativeVar(model.x2, wrt=model.t2)
model.dxdt3 = DerivativeVar(model.x3, wrt=model.t3)


# logic constraint
model.stage_mode = Disjunct(model.stage * model.mode)
model.d = Disjunction(model.stage)

# Stage 1


def stage1_mode1_dynamic(disjunct, t):
    model = disjunct.model()
    return model.dxdt1[t] == -model.x1[t] * exp(model.x1[t] - 1) + model.u1[t]


model.stage_mode[1, 1].mode1_dynamic_constraint = Constraint(
    model.t1, rule=stage1_mode1_dynamic
)


def stage1_mode2_dynamic(disjunct, t):
    model = disjunct.model()
    return model.dxdt1[t] == (0.5 * model.x1[t] ** 3 + model.u1[t]) / 20


model.stage_mode[1, 2].mode2_dynamic_constraint = Constraint(
    model.t1, rule=stage1_mode2_dynamic
)

model.d[1] = [model.stage_mode[1, 1], model.stage_mode[1, 2]]


# Stage 2


def stage2_mode1_dynamic(disjunct, t):
    model = disjunct.model()
    return model.dxdt2[t] == -model.x2[t] * exp(model.x2[t] - 1) + model.u2[t]


model.stage_mode[2, 1].mode1_dynamic_constraint = Constraint(
    model.t2, rule=stage2_mode1_dynamic
)


def stage2_mode2_dynamic(disjunct, t):
    model = disjunct.model()
    return model.dxdt2[t] == (0.5 * model.x2[t] ** 3 + model.u2[t]) / 20


model.stage_mode[2, 2].mode2_dynamic_constraint = Constraint(
    model.t2, rule=stage2_mode2_dynamic
)

model.d[2] = [model.stage_mode[2, 1], model.stage_mode[2, 2]]


# Stage 3


def stage3_mode1_dynamic(disjunct, t):
    model = disjunct.model()
    return model.dxdt3[t] == -model.x3[t] * exp(model.x3[t] - 1) + model.u3[t]


model.stage_mode[3, 1].mode1_dynamic_constraint = Constraint(
    model.t3, rule=stage3_mode1_dynamic
)


def stage3_mode2_dynamic(disjunct, t):
    model = disjunct.model()
    return model.dxdt3[t] == (0.5 * model.x3[t] ** 3 + model.u3[t]) / 20


model.stage_mode[3, 2].mode2_dynamic_constraint = Constraint(
    model.t3, rule=stage3_mode2_dynamic
)

model.d[3] = [model.stage_mode[3, 1], model.stage_mode[3, 2]]

# model.pprint()

# Objective function
model.intx1 = Integral(model.t1, wrt=model.t1, rule=lambda model, t: model.x1[t] ** 2)
model.intx2 = Integral(model.t2, wrt=model.t2, rule=lambda model, t: model.x2[t] ** 2)
model.intx3 = Integral(model.t3, wrt=model.t3, rule=lambda model, t: model.x3[t] ** 2)

model.obj = Objective(expr=-(model.intx1 + model.intx2 + model.intx3), sense=minimize)

# Discretize model using Orthogonal Collocation
discretizer = TransformationFactory('dae.collocation')
discretizer.apply_to(model, nfe=30, ncp=3, scheme='LAGRANGE-RADAU')

model.c1 = Constraint(expr=model.x1[0] == 1)
model.c2 = Constraint(expr=model.x1[1] == model.x2[1])
model.c3 = Constraint(expr=model.x2[2] == model.x3[2])

model.c4 = Constraint(expr=model.u1[0] == 4)
model.c5 = Constraint(expr=model.u1[1] == model.u2[1])
model.c6 = Constraint(expr=model.u2[2] == model.u3[2])


model.stage_mode[1, 1].mode1_dynamic_constraint._constructed = False
model.stage_mode[1, 1].mode1_dynamic_constraint.construct()
model.stage_mode[1, 2].mode2_dynamic_constraint._constructed = False
model.stage_mode[1, 2].mode2_dynamic_constraint.construct()

model.stage_mode[2, 1].mode1_dynamic_constraint._constructed = False
model.stage_mode[2, 1].mode1_dynamic_constraint.construct()
model.stage_mode[2, 2].mode2_dynamic_constraint._constructed = False
model.stage_mode[2, 2].mode2_dynamic_constraint.construct()

model.stage_mode[3, 1].mode1_dynamic_constraint._constructed = False
model.stage_mode[3, 1].mode1_dynamic_constraint.construct()
model.stage_mode[3, 2].mode2_dynamic_constraint._constructed = False
model.stage_mode[3, 2].mode2_dynamic_constraint.construct()

model.BigM = Suffix(direction=Suffix.LOCAL)
model.BigM[None] = 1000000
TransformationFactory('gdp.bigm').apply_to(model)

solver = SolverFactory("gams")
results = solver.solve(model, tee=True, solver='baron')
print(results)
model.x1.pprint()
model.x2.pprint()
model.x3.pprint()
model.u1.pprint()
model.u2.pprint()
model.u3.pprint()
