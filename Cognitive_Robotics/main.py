import random
import simulation_manager
import pickle
from stn_taxis_domain import solve_taxis_problem as stn_solver


if __name__ == '__main__':

    # load tasks
    with open(r"problems/problems_list.pkl", 'rb') as file:
        all_tasks = pickle.load(file)

    # choose a task randomly
    cur_task = random.choice(all_tasks)

    # solve the task
    plan, _ = stn_solver(cur_task)

    # simulate results
    sim = simulation_manager.SimulationManager(
        world_map=cur_task['map'],
        t_locs=cur_task['t_locs'],
        p_locs=cur_task['p_locs'],
        p_dest=cur_task['p_dest'],
        actions=plan.actions
    )
    sim.run()
