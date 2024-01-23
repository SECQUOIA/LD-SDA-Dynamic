import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from glob import glob
import json
import seaborn as sns
import numpy as np

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
plt.rcParams['axes.labelsize'] = 12  # For x and y labels
plt.rcParams['xtick.labelsize'] = 12  # For x tick labels
plt.rcParams['ytick.labelsize'] = 12  # For y tick labels

json_file_folder_dict = {
    4: 'results/four_stage_dynamic_model_switching_nonlinear/nfe30/2024-02-25_14-19-02',
    5: 'results/five_stage_dynamic_model_switching_nonlinear/nfe30/2024-02-26_00-17-16',
    6: 'results/six_stage_dynamic_model_switching_nonlinear/nfe30/2024-02-25_14-19-26',
    7: 'results/seven_stage_dynamic_model_switching_nonlinear/nfe30/2024-02-26_00-17-55',
    8: 'results/eight_stage_dynamic_model_switching_nonlinear/nfe30/2024-02-25_14-19-39',
    9: 'results/nine_stage_dynamic_model_switching_nonlinear/nfe30/2024-02-26_00-19-35',
}


def read_data(file_folder):
    data = []
    for f_name in glob(file_folder + '/*.json'):
        with open(f_name, 'r') as f:
            json_data = json.load(f)
            if f_name.split('/')[-1].split('_')[0] == 'gdpopt.ldsda':
                json_data['strategy'] = (
                    f_name[:-5].split('/')[-1].split('_')[0]
                    + '-'
                    + f_name[:-5].split('/')[-1].split('_')[2]
                )
            else:
                json_data['strategy'] = f_name[:-5].split('/')[-1].split('_')[0]
            json_data['solver'] = f_name[:-5].split('/')[-1].split('_')[1]
            if isinstance(json_data['Problem'], list):
                json_data['Problem'] = json_data['Problem'][0]
            if isinstance(json_data['Solver'], list):
                json_data['Solver'] = json_data['Solver'][0]
            data.append(json_data)
    df = pd.json_normalize(data)
    result = df[
        [
            'strategy',
            'solver',
            'Problem.Lower bound',
            'Problem.Upper bound',
            'Solver.User time',
            'Solver.Termination condition',
        ]
    ]
    result = result.fillna('-')
    result.rename(
        columns={
            'Problem.Lower bound': 'Lower bound',
            'Problem.Upper bound': 'Upper bound',
            'Solver.User time': 'Time',
            'Solver.Termination condition': 'Termination condition',
        },
        inplace=True,
    )
    return result


optimal_objective_value = {
    4: -23.304689,
    5: -52.79223,
    6: -122.423721,
    7: -160.08149,
    8: -188.449493,
    9: -212.00879,
}

result_list = []
for stage in json_file_folder_dict:
    result = read_data(json_file_folder_dict[stage])
    result['Stage'] = stage
    result['Optimal objective value'] = optimal_objective_value[stage]
    result_list.append(result)

result = pd.concat(result_list).reset_index(drop=True)

time_limit = {4: 900, 5: 900, 6: 900, 7: 1800, 8: 1800, 9: 3600}
for stage in time_limit:
    temp_result = result[
        (result['Time'] >= time_limit[stage])
        & (result['Stage'] == stage)
        & (
            abs(result['Upper bound'] - result['Optimal objective value'])
            < abs(result['Optimal objective value']) * 0.001
        )
    ]
    step = 0.1
    if len(temp_result) > 1:
        for idx, index in enumerate(temp_result.index):
            result.iloc[index, result.columns.get_loc('Stage')] += step * (
                -len(temp_result) + 1 + 2 * idx
            )

strategy_maker_dict = {
    'gdp.bigm': "X",
    'gdp.hull': "^",
    'gdpopt.enumerate': "D",
    'gdpopt.loa': "*",
    'gdpopt.gloa': "P",
    'gdpopt.ldsda-L2': "o",
    'gdpopt.ldsda-Linf': "s",
    # 'gdpopt.lbb': color_palette[7],
}

fig, ax = plt.subplots()
color_palette = sns.color_palette("Spectral", 8)
solver_color_dict = {'baron': color_palette[0], 'knitro': color_palette[7]}
plt.xticks(ticks=[4, 5, 6, 7, 8, 9], labels=[4, 5, 6, 7, 8, 9])

for strategy in strategy_maker_dict:
    maker = strategy_maker_dict[strategy]
    for solver in solver_color_dict:
        color = solver_color_dict[solver]
        subset = result[
            (result['strategy'] == strategy)
            & (result['solver'] == solver)
            & (
                abs(result['Upper bound'] - result['Optimal objective value'])
                < abs(result['Optimal objective value']) * 0.001
            )
        ]
        plt.plot(
            subset['Stage'],
            subset['Time'],
            label=f'{strategy} - {solver}',
            mec='black',
            marker=maker,
            linestyle='',
            color=color,
            markersize=8,
            markeredgewidth=0.5,
            alpha=0.9,
        )
plt.xlabel('Number of Stages')
plt.ylabel("Solution Time [s]\n(within 0.1% of known optimal value)")
plt.yscale('log')

handles, labels = ax.get_legend_handles_labels()
sorted_indices = np.argsort(labels)
sorted_handles = [handles[idx] for idx in sorted_indices]
sorted_labels = [labels[idx] for idx in sorted_indices]
ax.legend(sorted_handles, sorted_labels, loc='upper center', ncol=3)


# Sort the legend labels and handles
GDPopt_handles, GDPopt_labels = [], []
DSDA_handles, DSDA_labels = [], []
MINLP_handles, MINLP_labels = [], []
Enum_handles, Enum_labels = [], []

for handle, label in zip(*ax.get_legend_handles_labels()):

    if 'gdpopt.ldsda' in label:
        DSDA_handles.append(handle)
        DSDA_labels.append(
            label.replace('gdpopt.ldsda-', '')
            .replace('baron', 'BARON')
            .replace('knitro', 'KNITRO')
        )
    elif 'gdpopt.' in label:
        GDPopt_handles.append(handle)
        GDPopt_labels.append(
            label.replace('gdpopt.', '')
            .replace('enumerate', 'Enum')
            .replace('gloa', 'GLOA')
            .replace('loa', 'LOA')
            .replace('baron', 'BARON')
            .replace('knitro', 'KNITRO')
        )
    elif 'gdp.' in label:
        MINLP_handles.append(handle)
        MINLP_labels.append(
            label.replace('gdp.', '')
            .replace('bigm', 'BigM')
            .replace('hull', 'Hull')
            .replace('baron', 'BARON')
            .replace('knitro', 'KNITRO')
        )

# Create custom legends
legend_GDPopt = ax.legend(
    GDPopt_handles,
    GDPopt_labels,
    title='GDPOpt',
    loc='lower center',
    bbox_to_anchor=(1.24, 0.05),
    fontsize=10,  #'small',
    ncol=1,
)
legend_DSDA = ax.legend(
    DSDA_handles,
    DSDA_labels,
    title='LD-SDA',
    loc='lower center',
    bbox_to_anchor=(1.22, 0.72),
    fontsize=10,  #'small',
    ncol=1,
)
legend_MINLP = ax.legend(
    MINLP_handles,
    MINLP_labels,
    title='MINLP',
    loc='lower center',
    bbox_to_anchor=(1.23, 0.45),
    fontsize=10,  #'small',
    ncol=1,
)

plt.tight_layout()
ax.add_artist(legend_GDPopt)
ax.add_artist(legend_DSDA)
ax.add_artist(legend_MINLP)

plt.savefig('figures/computational_results_comparison.pdf')
