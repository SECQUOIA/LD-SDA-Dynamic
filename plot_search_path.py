import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


def visualize_dsda(
    incumbent_path, exploration, feas_x, feas_y, objs, file_name, x_label, y_label
):

    sc = plt.scatter(feas_x, feas_y, s=80, c=objs, cmap='viridis_r')

    for i in range(len(incumbent_path) - 1):
        plt.annotate(
            '',
            xy=incumbent_path[i + 1],
            xytext=incumbent_path[i],
            arrowprops=dict(arrowstyle="->", color='black', linestyle='solid'),
        )
    for i in exploration:
        plt.annotate(
            '',
            xy=i[1],
            xytext=i[0],
            arrowprops=dict(arrowstyle="->", color='black', linestyle='dotted'),
        )

    # Create a custom legend for the arrow
    custom_line1 = [
        Line2D(
            [0],
            [0],
            color='black',
            lw=1,
            linestyle='solid',
            marker='>',
            markeredgewidth=0.5,
            markersize=4,
        ),
        Line2D(
            [0],
            [0],
            color='black',
            lw=1,
            linestyle='dotted',
            marker='>',
            markeredgewidth=0.5,
            markersize=4,
        ),
    ]

    # Add the legend to the plot
    plt.legend(custom_line1, ['Incumbent', 'Exploration'])

    cbar = plt.colorbar(sc)
    cbar.set_label('Objective function', rotation=90)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.savefig(file_name)
    plt.figure().clear()


feasible_solution = {
    (1, 2): -197.14013122689622,
    (1, 3): -206.36041265432806,
    (1, 4): -212.00878719112268,
    (1, 5): -207.62611633572016,
    (1, 6): -196.93118428995865,
    (1, 7): -178.63847525562682,
    (1, 8): -146.87850122234687,
    (1, 9): -87.5338894428716,
    (2, 3): -117.07438084784795,
    (2, 4): -137.1797042946188,
    (2, 5): -192.870848809807,
    (2, 6): -192.88392569521721,
    (2, 7): -175.94473700875903,
    (2, 8): -144.71276519403037,
    (2, 9): -85.82696130620648,
    (3, 4): -77.19743879461578,
    (3, 5): -88.41538101128177,
    (3, 6): -119.38309938589616,
    (3, 7): -170.89539354574913,
    (3, 8): -141.82503814335138,
    (3, 9): -83.55206301486514,
    (4, 5): -55.81190616713566,
    (4, 6): -62.4732860007934,
    (4, 7): -77.86237831841856,
    (4, 8): -135.07901900226858,
    (4, 9): -80.51745201314861,
    (5, 6): -43.41238657553521,
    (5, 7): -47.28320969606174,
    (5, 8): -54.212220237141665,
    (5, 9): -66.30029047415469,
    (6, 7): -36.01889379296989,
    (6, 8): -37.96970292827284,
    (6, 9): -39.58228460866401,
    (7, 8): -31.679373632369185,
    (7, 9): -32.196321090299925,
    (8, 9): -29.327202909495576,
    (9, 9): -28.596739202011523,
}


feas_x = []
feas_y = []
objs = []
for key in feasible_solution:
    feas_x.append(key[0])
    feas_y.append(key[1])
    objs.append(feasible_solution[key])

# Plot search path of LD-SDA L2
incumbent_path = [(1, 2), (1, 3), (1, 4)]
exploration = [[(1, 4), (1, 5)], [(1, 4), (2, 4)]]
visualize_dsda(
    incumbent_path=incumbent_path,
    exploration=exploration,
    feas_x=feas_x,
    feas_y=feas_y,
    objs=objs,
    file_name='figures/search_path_LD-SDA_L2.pdf',
    x_label='$Z_{s,1}$',
    y_label='$Z_{s,2}$',
)

# Plot search path of LD-SDA Linf
incumbent_path = [(1, 2), (1, 3), (1, 4)]
exploration = [[(1, 2), (2, 3)], [(1, 4), (1, 5)], [(1, 4), (2, 4)], [(1, 4), (2, 5)]]
visualize_dsda(
    incumbent_path=incumbent_path,
    exploration=exploration,
    feas_x=feas_x,
    feas_y=feas_y,
    objs=objs,
    file_name='figures/search_path_LD-SDA_Linf.pdf',
    x_label='$Z_{s,1}$',
    y_label='$Z_{s,2}$',
)
