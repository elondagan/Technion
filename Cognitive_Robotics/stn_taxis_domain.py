from unified_planning.shortcuts import *
from unified_planning.io import PDDLWriter
from unified_planning.engines import PlanGenerationResultStatus
import time

O = 0
X = 1
S = 2
I = 5
P = 6


def initialize_environment(a_map, passengers_locations, passengers_destinations, taxis_locations, nof_taxis=4,
                           num_switches=20):

    map_rows_size, map_cols_size = len(a_map), len(a_map[0])
    nof_passengers = len(passengers_locations)

    blocked_locations = [(i, j) for i in range(map_rows_size) for j in range(map_cols_size) if a_map[i][j] == X]
    station_locations = [(i, j) for i in range(map_rows_size) for j in range(map_cols_size) if a_map[i][j] == S]
    intersection_locations = [(i, j) for i in range(map_rows_size) for j in range(map_cols_size) if a_map[i][j] == I]
    pre_intersection_locations = [(i, j) for i in range(map_rows_size) for j in range(map_cols_size) if
                                  a_map[i][j] == P]

    xy_locations = [(x, y) for x in range(map_rows_size) for y in range(map_cols_size)]

    # ---------- Initialize problem & define types ----------

    problem = Problem('Taxi_Map_Environment')

    Taxi = UserType('Taxi')
    Location = UserType('Location')
    Passenger = UserType('Passenger')
    Light = UserType("Light")
    Counter = UserType("counter")

    # ---------- Create & add object ----------

    locations = [Object(f'loc({x},{y})', Location) for x in range(map_rows_size) for y in range(map_cols_size)]
    problem.add_objects(locations)

    taxis = [Object(f'taxi_{i}', Taxi) for i in range(1, nof_taxis + 1)]
    problem.add_objects(taxis)

    passengers = [Object(f'passenger_{i}', Passenger) for i in range(1, nof_passengers + 1)]
    problem.add_objects(passengers)

    light = Object("light", Light)
    problem.add_object(light)

    counters = [Object(f"counter_{i}", Counter) for i in range(num_switches+1)]
    problem.add_objects(counters)


    # ---------- Define & add fluents ----------

    taxi_busy = Fluent('taxi_busy', BoolType(), t=Taxi)
    taxi_at = Fluent("taxi_at_loc", BoolType(), t=Taxi, l=Location)
    passenger_of_taxi = Fluent("passenger_of_taxi", BoolType(), p=Passenger, t=Taxi)

    passenger_at = Fluent('pass_at_loc', BoolType(), p=Passenger, l=Location)
    passenger_on = Fluent('pass_on_taxi', BoolType(), p=Passenger, t=Taxi)

    is_blocked = Fluent('is_blocked', BoolType(), l=Location)
    is_station = Fluent('is_station', BoolType(), l=Location)
    is_occupied = Fluent('is_occupied', BoolType(), l=Location)
    is_intersection = Fluent("is_intersection", BoolType(), l=Location)
    is_pre_intersection = Fluent("is_pre_intersection", BoolType(), l=Location)

    is_up_lane = Fluent("is_up_lane", BoolType(), l=Location)
    is_down_lane = Fluent("is_down_lane", BoolType(), l=Location)
    is_right_lane = Fluent("is_right_lane", BoolType(), l=Location)
    is_left_lane = Fluent("is_left_lane", BoolType(), l=Location)

    is_adjacent = Fluent("is_adjacent", BoolType(), loc1=Location, loc2=Location)

    is_right = Fluent("is_right", BoolType(), loc1=Location, loc2=Location)
    is_left = Fluent("is_left", BoolType(), loc1=Location, loc2=Location)
    is_up = Fluent("is_up", BoolType(), loc1=Location, loc2=Location)
    is_down = Fluent("is_down", BoolType(), loc1=Location, loc2=Location)

    moving_up = Fluent("moving_up", BoolType(), t=Taxi)
    moving_down = Fluent("moving_down", BoolType(), t=Taxi)
    moving_right = Fluent("moving_right", BoolType(), t=Taxi)
    moving_left = Fluent("moving_left", BoolType(), t=Taxi)

    is_horizontal = Fluent("is_horizontal", BoolType(), l=Light)
    is_vertical = Fluent("is_vertical", BoolType(), l=Light)
    waiting_on_v = Fluent("waiting_on_v", BoolType(), t=Taxi, l=Light)
    waiting_on_h = Fluent("waiting_on_h", BoolType(), t=Taxi, l=Light)
    next = Fluent("next", BoolType(), cc=Counter, cn=Counter)
    times_switched = Fluent("times_switched", BoolType(), l=Light, c=Counter)


    fluents = [taxi_busy, taxi_at, passenger_of_taxi, passenger_at, passenger_on,
               is_blocked, is_station, is_occupied, is_intersection, is_pre_intersection,
               is_up_lane, is_down_lane, is_right_lane, is_left_lane, is_adjacent,
               is_right, is_left, is_up, is_down, moving_up, moving_down, moving_right, moving_left,
               is_horizontal, is_vertical, waiting_on_v, waiting_on_h, times_switched, next]

    for fluent in fluents:
        problem.add_fluent(fluent)


    # ---------- Define actions ----------


    # Drive straight actions

    drive_straight = InstantaneousAction("drive_straight", taxi=Taxi, from_loc=Location, to_loc=Location,
                                         light=Light)
    taxi = drive_straight.parameter("taxi")
    from_loc, to_loc = drive_straight.parameter("from_loc"), drive_straight.parameter("to_loc")
    l = drive_straight.parameter("light")

    up_condition = And(is_up_lane(from_loc), is_up_lane(to_loc), is_up(from_loc, to_loc), moving_up(taxi),
                       Or(~is_intersection(to_loc), is_vertical(l)))
    down_condition = And(is_down_lane(from_loc), is_down_lane(to_loc), is_down(from_loc, to_loc), moving_down(taxi),
                         Or(~is_intersection(to_loc), is_vertical(l)))
    right_condition = And(is_right_lane(from_loc), is_right_lane(to_loc), is_right(from_loc, to_loc), moving_right(taxi),
                          Or(~is_intersection(to_loc), is_horizontal(l)))
    left_condition = And(is_left_lane(from_loc), is_left_lane(to_loc), is_left(from_loc, to_loc), moving_left(taxi),
                         Or(~is_intersection(to_loc), is_horizontal(l)))

    drive_straight.add_precondition(Or(up_condition, down_condition, right_condition, left_condition))
    drive_straight.add_precondition(taxi_at(taxi, from_loc))
    drive_straight.add_precondition(Not(is_blocked(to_loc)))
    drive_straight.add_precondition(Not(is_occupied(to_loc)))
    drive_straight.add_precondition(~(is_station(from_loc) & is_station(to_loc)))

    drive_straight.add_effect(taxi_at(taxi, from_loc), False)
    drive_straight.add_effect(taxi_at(taxi, to_loc), True)
    drive_straight.add_effect(is_occupied(to_loc), True)
    drive_straight.add_effect(is_occupied(from_loc), False)

    problem.add_action(drive_straight)

    # Turn actions

    drive_up2left = InstantaneousAction("drive_up2left", taxi=Taxi, from_loc=Location, to_loc=Location)
    drive_up2right = InstantaneousAction("drive_up2right", taxi=Taxi, from_loc=Location, to_loc=Location)

    drive_down2left = InstantaneousAction("drive_down2left", taxi=Taxi, from_loc=Location, to_loc=Location)
    drive_down2right = InstantaneousAction("drive_down2right", taxi=Taxi, from_loc=Location, to_loc=Location)

    drive_right2up = InstantaneousAction("drive_right2up", taxi=Taxi, from_loc=Location, to_loc=Location)
    drive_right2down = InstantaneousAction("drive_right2down", taxi=Taxi, from_loc=Location, to_loc=Location)

    drive_left2up = InstantaneousAction("drive_left2up", taxi=Taxi, from_loc=Location, to_loc=Location)
    drive_left2down = InstantaneousAction("drive_left2down", taxi=Taxi, from_loc=Location, to_loc=Location)

    turn_actions = [drive_up2left, drive_up2right, drive_down2left, drive_down2right, drive_right2up, drive_right2down,
                    drive_left2up, drive_left2down]

    for action in turn_actions:
        from_lane, to_lane = action.name.split("_")[1].split("2")

        taxi, from_loc, to_loc = action.parameter("taxi"), action.parameter(
            "from_loc"), action.parameter("to_loc")

        if from_lane == 'up':
            action.add_precondition(is_up_lane(from_loc))
            action.add_precondition(moving_up(taxi))
            action.add_effect(moving_up(taxi), False)
            if to_lane == 'right':
                action.add_precondition(is_left(to_loc, from_loc))
                action.add_precondition(is_right_lane(to_loc))
                action.add_effect(moving_right(taxi), True)
            else:  # left
                action.add_precondition(is_right(to_loc, from_loc))
                action.add_precondition(is_left_lane(to_loc))
                action.add_effect(moving_left(taxi), True)

        elif from_lane == 'down':
            action.add_precondition(is_down_lane(from_loc))
            action.add_precondition(moving_down(taxi))
            action.add_effect(moving_down(taxi), False)
            if to_lane == 'right':
                action.add_precondition(is_left(to_loc, from_loc))
                action.add_precondition(is_right_lane(to_loc))
                action.add_effect(moving_right(taxi), True)
            else:  # left
                action.add_precondition(is_right(to_loc, from_loc))
                action.add_precondition(is_left_lane(to_loc))
                action.add_effect(moving_left(taxi), True)

        elif from_lane == 'right':
            action.add_precondition(is_right_lane(from_loc))
            action.add_precondition(moving_right(taxi))
            action.add_effect(moving_right(taxi), False)
            if to_lane == 'up':
                action.add_precondition(is_down(to_loc, from_loc))
                action.add_precondition(is_up_lane(to_loc))
                action.add_effect(moving_up(taxi), True)
            else:  # down
                action.add_precondition(is_up(to_loc, from_loc))
                action.add_precondition(is_down_lane(to_loc))
                action.add_effect(moving_down(taxi), True)

        elif from_lane == 'left':
            action.add_precondition(is_left_lane(from_loc))
            action.add_precondition(moving_left(taxi))
            action.add_effect(moving_left(taxi), False)
            if to_lane == 'up':
                action.add_precondition(is_down(to_loc, from_loc))
                action.add_precondition(is_up_lane(to_loc))
                action.add_effect(moving_up(taxi), True)
            else:  # down
                action.add_precondition(is_up(to_loc, from_loc))
                action.add_precondition(is_down_lane(to_loc))
                action.add_effect(moving_down(taxi), True)

        else:
            raise RuntimeError("should not get here")

        action.add_precondition(taxi_at(taxi, from_loc))
        action.add_precondition(is_intersection(from_loc))
        action.add_precondition(is_adjacent(from_loc, to_loc))
        action.add_precondition(Not(is_blocked(to_loc)))
        action.add_precondition(Not(is_occupied(to_loc)))
        action.add_precondition(Not(is_station(to_loc)))

        action.add_effect(taxi_at(taxi, from_loc), False)
        action.add_effect(taxi_at(taxi, to_loc), True)
        action.add_effect(is_occupied(to_loc), True)
        action.add_effect(is_occupied(from_loc), False)

        problem.add_action(action)


    # Glide
    glide = InstantaneousAction("glide", taxi=Taxi, from_loc=Location, to_loc=Location)
    taxi, from_loc, to_loc = glide.parameter("taxi"), glide.parameter("from_loc"), glide.parameter("to_loc")

    glide.add_precondition(taxi_at(taxi, from_loc))
    glide.add_precondition(is_station(from_loc))
    glide.add_precondition(is_station(to_loc))
    glide.add_precondition(Not(is_occupied(to_loc)))
    glide.add_precondition(is_adjacent(from_loc, to_loc))

    glide.add_effect(taxi_at(taxi, from_loc), False)
    glide.add_effect(taxi_at(taxi, to_loc), True)
    glide.add_effect(is_occupied(to_loc), True)
    glide.add_effect(is_occupied(from_loc), False)

    problem.add_action(glide)

    # Pick up
    pickup = InstantaneousAction("pickup", t=Taxi, p=Passenger, l=Location)
    taxi, passenger, loc = pickup.parameter('t'), pickup.parameter('p'), pickup.parameter('l')

    pickup.add_precondition(passenger_at(passenger, loc))
    pickup.add_precondition(taxi_at(taxi, loc))
    pickup.add_precondition(Not(taxi_busy(taxi)))
    pickup.add_precondition(passenger_of_taxi(passenger, taxi))

    pickup.add_effect(passenger_at(passenger, loc), False)
    pickup.add_effect(passenger_on(passenger, taxi), True)
    pickup.add_effect(taxi_busy(taxi), True)

    problem.add_action(pickup)

    # drop off
    dropoff = InstantaneousAction("dropoff", t=Taxi, p=Passenger, l=Location)
    taxi, passenger, loc = dropoff.parameter('t'), dropoff.parameter('p'), dropoff.parameter('l')

    dropoff.add_precondition(passenger_on(passenger, taxi))
    dropoff.add_precondition(taxi_at(taxi, loc))

    dropoff.add_effect(passenger_at(passenger, loc), True)
    dropoff.add_effect(passenger_on(passenger, taxi), False)
    dropoff.add_effect(taxi_busy(taxi), False)

    problem.add_action(dropoff)


    # wait to horizontal light

    wait_on_h = InstantaneousAction("wait_on_h", t=Taxi, l=Light, loc=Location)
    t, l, loc = wait_on_h.parameter("t"), wait_on_h.parameter("l"), wait_on_h.parameter("loc")

    wait_on_h.add_precondition(~is_horizontal(l))
    wait_on_h.add_precondition(~waiting_on_h(t, l))
    wait_on_h.add_precondition(And(taxi_at(t, loc), is_pre_intersection(loc)))
    wait_on_h.add_precondition(Or(moving_left(t), moving_right(t)))

    wait_on_h.add_effect(waiting_on_h(t, l), True)

    problem.add_action(wait_on_h)

    # wait to vertical light

    wait_on_v = InstantaneousAction("wait_on_v", t=Taxi, l=Light, loc=Location)
    t, l, loc = wait_on_v.parameter("t"), wait_on_v.parameter("l"), wait_on_v.parameter("loc")
    wait_on_v.add_precondition(~is_vertical(l))

    wait_on_v.add_precondition(~waiting_on_v(t, l))
    wait_on_v.add_precondition(And(taxi_at(t, loc), is_pre_intersection(loc)))
    wait_on_v.add_precondition(Or(moving_up(t), moving_down(t)))

    wait_on_v.add_effect(waiting_on_v(t, l),True)

    problem.add_action(wait_on_v)


    # switch light from horizontal to vertical

    h_to_v = InstantaneousAction("h_to_v", l=Light, t1=Taxi, t2=Taxi, t3=Taxi, t4=Taxi, c1=Counter, c2=Counter)
    taxi_params = [h_to_v.parameter("t1"), h_to_v.parameter("t2"), h_to_v.parameter("t3"), h_to_v.parameter("t4")]
    l = h_to_v.parameter("l")
    c1 = h_to_v.parameter("c1")
    c2 = h_to_v.parameter("c2")
    h_to_v.add_precondition(times_switched(l, c1))
    h_to_v.add_precondition(next(c1, c2))
    h_to_v.add_precondition(is_horizontal(l))
    h_to_v.add_precondition(~is_vertical(l))

    h_to_v.add_precondition(~Equals(taxi_params[0], taxi_params[1]))
    h_to_v.add_precondition(~Equals(taxi_params[0], taxi_params[2]))
    h_to_v.add_precondition(~Equals(taxi_params[0], taxi_params[3]))
    h_to_v.add_precondition(~Equals(taxi_params[1], taxi_params[2]))
    h_to_v.add_precondition(~Equals(taxi_params[1], taxi_params[3]))
    h_to_v.add_precondition(~Equals(taxi_params[2], taxi_params[3]))

    h_to_v.add_precondition(Or(waiting_on_v(taxi_params[0], l), waiting_on_v(taxi_params[1], l),
                               waiting_on_v(taxi_params[2], l), waiting_on_v(taxi_params[3], l)))

    for t in taxi_params:
        for loc in intersection_locations:
            loc_obj = locations[xy_locations.index(loc)]
            h_to_v.add_precondition(~taxi_at(taxi, loc_obj))
        h_to_v.add_effect(waiting_on_v(t, l), False)
    h_to_v.add_effect(is_horizontal(l), False)
    h_to_v.add_effect(is_vertical(l), True)
    h_to_v.add_effect(times_switched(l, c1), False)
    h_to_v.add_effect(times_switched(l, c2), True)

    problem.add_action(h_to_v)

    # switch light from vertical to horizontal

    v_to_h = InstantaneousAction("v_to_h", l=Light, t1=Taxi, t2=Taxi, t3=Taxi, t4=Taxi, c1=Counter, c2=Counter)
    taxi_params = [v_to_h.parameter("t1"), v_to_h.parameter("t2"), v_to_h.parameter("t3"), v_to_h.parameter("t4")]
    l = v_to_h.parameter("l")
    c1 = v_to_h.parameter("c1")
    c2 = v_to_h.parameter("c2")
    v_to_h.add_precondition(times_switched(l, c1))
    v_to_h.add_precondition(next(c1, c2))
    v_to_h.add_precondition(~is_horizontal(l))
    v_to_h.add_precondition(is_vertical(l))
    v_to_h.add_precondition(~Equals(taxi_params[0], taxi_params[1]))
    v_to_h.add_precondition(~Equals(taxi_params[0], taxi_params[2]))
    v_to_h.add_precondition(~Equals(taxi_params[0], taxi_params[3]))
    v_to_h.add_precondition(~Equals(taxi_params[1], taxi_params[2]))
    v_to_h.add_precondition(~Equals(taxi_params[1], taxi_params[3]))
    v_to_h.add_precondition(~Equals(taxi_params[2], taxi_params[3]))
    v_to_h.add_precondition(Or(waiting_on_h(taxi_params[0], l), waiting_on_h(taxi_params[1], l),
                               waiting_on_h(taxi_params[2], l), waiting_on_h(taxi_params[3], l)))

    for t in taxi_params:
        for loc in intersection_locations:
            loc_obj = locations[xy_locations.index(loc)]
            v_to_h.add_precondition(~taxi_at(taxi, loc_obj))
        v_to_h.add_effect(waiting_on_h(t, l), False)
    v_to_h.add_effect(is_horizontal(l), True)
    v_to_h.add_effect(is_vertical(l), False)
    v_to_h.add_effect(times_switched(l, c1), False)
    v_to_h.add_effect(times_switched(l, c2), True)

    problem.add_action(v_to_h)

    # ---------- Set goal ----------

    for i, xy_loc in enumerate(passengers_destinations):

        loc_obj = locations[xy_locations.index(xy_loc)]
        problem.add_goal(passenger_at(passengers[i], loc_obj))

    for i, xy_loc in enumerate(taxis_locations):
        loc_obj = locations[xy_locations.index(xy_loc)]
        problem.add_goal(taxi_at(taxis[i], loc_obj))

    light_condition = Or(times_switched(light, counters[-i]) for i in range(0, num_switches))
    problem.add_goal(light_condition)

    # ---------- Set initial values ----------

    # light

    problem.set_initial_value(is_vertical(light), True)
    problem.set_initial_value(is_horizontal(light), False)
    for taxi in taxis:
        problem.set_initial_value(waiting_on_h(taxi, light), False)
        problem.set_initial_value(waiting_on_v(taxi, light), False)

    # lights counter

    for i, c in enumerate(counters):
        if i == 0:
            problem.set_initial_value(times_switched(light, c), True)
        else:
            problem.set_initial_value(times_switched(light, c), False)

    for i, c1 in enumerate(counters):
        for j, c2 in enumerate(counters):
            if j == i+1:
                problem.set_initial_value(next(c1, c2), True)
            else:
                problem.set_initial_value(next(c1, c2), False)

    # locations

    for i, loc in enumerate(locations):
        xy_loc = xy_locations[i]

        # lane direction

        problem.set_initial_value(is_up_lane(loc), False)
        problem.set_initial_value(is_down_lane(loc), False)
        problem.set_initial_value(is_right_lane(loc), False)
        problem.set_initial_value(is_left_lane(loc), False)

        if xy_loc[1] % 2 == 0:
            problem.set_initial_value(is_down_lane(loc), True)
        else:
            problem.set_initial_value(is_up_lane(loc), True)
        if xy_loc[0] % 2 == 0:
            problem.set_initial_value(is_left_lane(loc), True)
        else:
            problem.set_initial_value(is_right_lane(loc), True)

        # location type

        problem.set_initial_value(is_occupied(loc), False)
        problem.set_initial_value(is_blocked(loc), False)
        problem.set_initial_value(is_station(loc), False)
        problem.set_initial_value(is_intersection(loc), False)
        problem.set_initial_value(is_pre_intersection(loc), False)
        if xy_loc in blocked_locations:
            problem.set_initial_value(is_blocked(loc), True)
        elif xy_loc in station_locations:
            problem.set_initial_value(is_station(loc), True)
        elif xy_loc in intersection_locations:
            problem.set_initial_value(is_intersection(loc), True)
        elif xy_loc in pre_intersection_locations:
            problem.set_initial_value(is_pre_intersection(loc), True)
        for taxi in taxis:
            problem.set_initial_value(taxi_at(taxi, loc), False)
        for p in passengers:
            problem.set_initial_value(passenger_at(p, loc), False)

    # adjacent location

    for loc1 in locations:
        for loc2 in locations:
            x1, y1 = xy_locations[locations.index(loc1)]
            x2, y2 = xy_locations[locations.index(loc2)]
            is_adj = (abs(x1 - x2) == 1 and y1 == y2) or (abs(y1 - y2) == 1 and x1 == x2)
            problem.set_initial_value(is_adjacent(loc1, loc2), is_adj)

    # next to locations

    for loc1 in locations:
        for loc2 in locations:
            x1, y1 = xy_locations[locations.index(loc1)]
            x2, y2 = xy_locations[locations.index(loc2)]

            is_r = x1 == x2 and y1 + 1 == y2
            is_l = x1 == x2 and y1 - 1 == y2
            is_u = x1 - 1 == x2 and y1 == y2
            is_d = x1 + 1 == x2 and y1 == y2

            problem.set_initial_value(is_right(loc1, loc2), is_r)
            problem.set_initial_value(is_left(loc1, loc2), is_l)
            problem.set_initial_value(is_up(loc1, loc2), is_u)
            problem.set_initial_value(is_down(loc1, loc2), is_d)

    # taxis
    for i, taxi in enumerate(taxis):
        loc_obj = locations[xy_locations.index(taxis_locations[i])]
        problem.set_initial_value(taxi_at(taxi, loc_obj), True)
        problem.set_initial_value(is_occupied(loc_obj), True)
        problem.set_initial_value(taxi_busy(taxi), False)
        problem.set_initial_value(passenger_of_taxi(passengers[i], taxi), True)

        # taxi initial direction
        problem.set_initial_value(moving_up(taxi), True)
        problem.set_initial_value(moving_down(taxi), False)
        problem.set_initial_value(moving_right(taxi), False)
        problem.set_initial_value(moving_left(taxi), False)

    # passengers
    for i, p in enumerate(passengers_locations):
        loc_obj = locations[xy_locations.index(passengers_locations[i])]
        problem.set_initial_value(passenger_at(passengers[i], loc_obj), True)
        for j, t in enumerate(taxis):
            problem.set_initial_value(passenger_on(passengers[i], t), False)
            if j == i:
                problem.set_initial_value(passenger_of_taxi(passengers[i], t), True)
            else:
                problem.set_initial_value(passenger_of_taxi(passengers[i], t), False)

    # ____________________________________________________________

    return problem


def solve_taxis_problem(problem_dict):

    problem = initialize_environment(a_map=problem_dict['map'],
                                     passengers_locations=problem_dict['p_locs'],
                                     passengers_destinations=problem_dict['p_dest'],
                                     taxis_locations=problem_dict['t_locs'])
    get_env().credits_stream = None
    with OneshotPlanner(name='fast-downward', optimality_guarantee=PlanGenerationResultStatus.SOLVED_OPTIMALLY) \
            as planner:

        start_time = time.time()
        result = planner.solve(problem)
        solving_time = time.time() - start_time

        return result.plan, solving_time
