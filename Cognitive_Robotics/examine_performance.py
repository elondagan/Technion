from stn_taxis_domain import solve_taxis_problem as stn_solver
from classic_taxis_domain import solve_taxis_problem as classic_solver
import pickle
import pandas as pd
from tqdm import tqdm


def count_taxis_actions(sol):
    actions = sol.actions
    counter = 0
    for a in actions:
        str_a = str(a)
        if 'v_to_h' not in str_a and 'h_to_v' not in str_a and 'wait' not in str_a:
            counter += 1

    return counter


O = 0
X = 1
S = 2
I = 5
P = 6


if __name__ == '__main__':

    " Solve problems "

    with open(r"problems/problems_list.pkl", 'rb') as file:
        all_tasks = pickle.load(file)


    classic_results = {'solutions': [], 'sol_times': []}
    for task in tqdm(all_tasks):
        sol, sol_time = classic_solver({'map': task['map'], 'p_locs': task['p_locs'], 'p_dest': task['p_dests'],
                                        't_locs': task['t_locs']})
        classic_results['solutions'].append(sol)
        classic_results['sol_times'].append(sol_time)
    with open("results/classic_results.pkl", 'wb') as file:
        pickle.dump(classic_results, file)


    stn_results = {'solutions': [], 'sol_times': []}
    for task in tqdm(all_tasks):
        task_dict = {'map': task['map'], 'p_locs': task['p_locs'], 'p_dest': task['p_dests'], 't_locs': task['t_locs']}
        sol, sol_time = stn_solver(task_dict)
        stn_results['solutions'].append(sol)
        stn_results['sol_times'].append(sol_time)
    with open("results/stn_results.pkl", 'wb') as file:
        pickle.dump(stn_results, file)


    # ____________________________________________


    results_comparison = {
        'methods': ['classic', 'STN'],
        'overall time': [0, 0],
        'average time': [0, 0],
        'overall actions': [0, 0],
        'average actions': [0, 0]
    }

    for i in range(len(all_tasks)):

        results_comparison['overall actions'][0] += count_taxis_actions(classic_results['solutions'][i])
        results_comparison['overall actions'][1] += count_taxis_actions(stn_results['solutions'][i])

        results_comparison['overall time'][0] += classic_results['sol_times'][i]
        results_comparison['overall time'][1] += stn_results['sol_times'][i]

    results_comparison['average time'][0] = results_comparison['overall time'][0] / len(all_tasks)
    results_comparison['average time'][1] = results_comparison['overall time'][1] / len(all_tasks)

    results_comparison['average actions'][0] = results_comparison['overall actions'][0] / len(all_tasks)
    results_comparison['average actions'][1] = results_comparison['overall actions'][1] / len(all_tasks)


    print(pd.DataFrame(results_comparison))
