import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


def visualize_dsda(
    feas_x,
    feas_y,
    objs,
    x_label,
    y_label,
    route_L2,
    exploration_L2,
    route_Linfinity,
    exploration_Linfinity,
    L2_color,
    Linfinity_color,
    offset=0.1,
):
    sc = plt.scatter(feas_x, feas_y, s=80, c=objs, cmap='viridis_r')

    # Parameters for enlarged arrows and increased font size
    arrow_width = 2.5  # Increased linewidth for arrows
    arrow_head_size = 12  # Increased markersize for arrowheads
    font_size = 15  # Increased font size for labels and legend
    number_font_size = 14  # Increased font size for the number ticks on axes

    # Plotting L2 search path in specified color
    for i in range(len(route_L2) - 1):
        plt.annotate(
            '',
            xy=route_L2[i + 1],
            xytext=route_L2[i],
            arrowprops=dict(
                arrowstyle="->",
                color=L2_color,
                linestyle='solid',
                lw=arrow_width,
                mutation_scale=arrow_head_size,
            ),
        )

    # Plotting Linfinity search path in specified color with offset
    for i in range(len(route_Linfinity) - 1):
        start_point = (route_Linfinity[i][0] + offset, route_Linfinity[i][1])
        end_point = (route_Linfinity[i + 1][0] + offset, route_Linfinity[i + 1][1])
        plt.annotate(
            '',
            xy=end_point,
            xytext=start_point,
            arrowprops=dict(
                arrowstyle="->",
                color=Linfinity_color,
                linestyle='solid',
                lw=arrow_width,
                mutation_scale=arrow_head_size,
            ),
        )

    # Plotting L2 exploration steps in lighter shade of red with dashed lines
    for i in exploration_L2:
        plt.annotate(
            '',
            xy=i[1],
            xytext=i[0],
            arrowprops=dict(
                arrowstyle="->",
                color=L2_color,
                linestyle='dashed',
                alpha=1,
                lw=arrow_width,
                mutation_scale=arrow_head_size,
            ),
        )

    # Plotting Linfinity exploration steps in lighter shade of blue with dotted lines
    for i in exploration_Linfinity:
        start_point = (i[0][0] + offset, i[0][1])
        end_point = (i[1][0] + offset, i[1][1])
        plt.annotate(
            '',
            xy=end_point,
            xytext=start_point,
            arrowprops=dict(
                arrowstyle="->",
                color=Linfinity_color,
                linestyle='dotted',
                alpha=0.6,
                lw=arrow_width,
                mutation_scale=arrow_head_size,
            ),
        )

    # Create custom legend
    custom_lines = [
        Line2D(
            [0],
            [0],
            color=L2_color,
            lw=1,
            linestyle='solid',
            marker='>',
            markeredgewidth=0.5,
            markersize=arrow_head_size,
        ),
        Line2D(
            [0],
            [0],
            color=Linfinity_color,
            lw=1,
            linestyle='solid',
            marker='>',
            markeredgewidth=0.5,
            markersize=arrow_head_size,
        ),
        Line2D(
            [0],
            [0],
            color=L2_color,
            lw=1,
            linestyle='dashed',
            alpha=1,
            marker='>',
            markeredgewidth=0.5,
            markersize=arrow_head_size,
        ),
        Line2D(
            [0],
            [0],
            color=Linfinity_color,
            lw=1,
            linestyle='dotted',
            alpha=1,
            marker='>',
            markeredgewidth=0.5,
            markersize=arrow_head_size,
        ),
    ]
    plt.legend(
        custom_lines,
        [
            '$L_2$ Path',
            '$L_{\infty}$ Path',
            '$L_2$ Exploration',
            '$L_{\infty}$ Exploration',
        ],
        fontsize=font_size,
    )

    cbar = plt.colorbar(sc)
    cbar.set_label('Objective function', rotation=270, labelpad=15, fontsize=font_size)
    cbar.ax.tick_params(
        labelsize=number_font_size
    )  # Set font size for colorbar tick labels
    plt.xlabel(x_label, fontsize=font_size)
    plt.ylabel(y_label, fontsize=font_size)
    plt.xticks(fontsize=number_font_size)  # Set font size for x-axis tick labels
    plt.yticks(fontsize=number_font_size)  # Set font size for y-axis tick labels


# Main block for plotting
plt.figure(figsize=(8, 6))

# Complete Enumeration Scatter Plot
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


# Define search paths and colors
route_L2 = [(1, 2), (1, 3), (1, 4)]
exploration_L2 = [[(1, 4), (1, 5)], [(1, 4), (2, 4)]]
route_Linfinity = [(1, 2), (1, 3), (1, 4)]
exploration_Linfinity = [
    [(1, 2), (2, 3)],
    [(1, 4), (1, 5)],
    [(1, 4), (2, 4)],
    [(1, 4), (2, 5)],
]

# Call the visualization function with specified colors for each path
visualize_dsda(
    feas_x=feas_x,
    feas_y=feas_y,
    objs=objs,
    x_label='$Z_{s,1}$, Position of Mode 1 to 2 transition',
    y_label='$Z_{s,2}$, Position of Mode 2 to 3 transition',
    route_L2=route_L2,
    exploration_L2=exploration_L2,
    route_Linfinity=route_Linfinity,
    exploration_Linfinity=exploration_Linfinity,
    L2_color='red',
    Linfinity_color='blue',
    offset=0.1,
)

plt.tight_layout()

# Save the figure to a PDF file
plt.savefig(
    '/home/albertlee/repos/visualization/LDSDA_path.pdf', # Change the path to your desired location
    format='pdf',
    bbox_inches='tight',
)

# Display the figure
plt.show()
