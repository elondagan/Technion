import random
import pickle

O = 0
X = 1
S = 2
I = 5
P = 6


MAPS = {

    'map1': [
        [I, I, P, 0, 0, 0, I, I],
        [I, I, 0, 0, 0, P, I, I],
        [0, P, X, X, X, X, 0, P],
        [0, 0, X, X, X, X, P, 0],
        [0, 0, X, X, X, X, I, I],
        [P, 0, X, X, X, X, I, I],
        [I, I, X, S, S, S, S, S],
        [I, I, X, S, S, S, S, S]
    ],

    'map2': [
        [I, I, P, 0, I, I],
        [I, I, 0, P, I, I],
        [0, P, X, X, 0, P],
        [0, 0, X, X, 0, 0],
        [0, 0, X, X, 0, 0],
        [0, 0, X, X, 0, 0],
        [0, 0, X, X, 0, 0],
        [P, 0, X, X, P, 0],
        [I, I, P, 0, I, I],
        [I, I, 0, P, I, I],
        [S, S, S, S, S, S],
        [S, S, S, S, S, S]
    ],

    'map3': [
        [I, I, P, 0, I, I, P, 0, I, I],
        [I, I, 0, P, I, I, 0, P, I, I],
        [0, P, X, X, 0, P, X, X, 0, P],
        [0, 0, X, X, 0, 0, X, X, 0, 0],
        [0, 0, X, X, P, 0, X, X, 0, 0],
        [P, 0, X, X, I, I, X, X, P, 0],
        [I, I, X, X, X, X, X, X, I, I],
        [I, I, X, X, X, X, X, X, I, I],
        [S, S, S, S, S, S, S, S, S, S],
        [S, S, S, S, S, S, S, S, S, S]
    ],


}


def get_random_locations(map_, nof_locations=4):
    possible_locs = []
    for i in range(len(map_)):
        for j in range(len(map_[0])):
            if map_[i][j] != X and map_[i][j] != S:
                possible_locs.append((i, j))

    return random.sample(possible_locs, nof_locations)


def get_taxi_parking_locations(map_, nof_locations=4):

    row_size = len(map_)
    col_size = len(map_[0])
    locs = [(row_size-2, col_size-2-i) for i in range(nof_locations)]
    return locs


def generate(nof_problems=1):
    """
    create and save taxis problems with the known 'MAPS'
    :param nof_problems: number of problems (different locations) for each map
    """
    all_problems = []

    for map_ in MAPS:
        for idx in range(nof_problems):
            new_problem = {
                'map': MAPS[map_],
                'p_locs': get_random_locations(MAPS[map_]),
                'p_dests': get_random_locations(MAPS[map_]),
                't_locs': get_taxi_parking_locations(MAPS[map_]),
            }
            all_problems.append(new_problem)

    with open(r"problems/problems_list.pkl", 'wb') as file:
        pickle.dump(all_problems, file)


if __name__ == '__main__':
    generate(nof_problems=10)

