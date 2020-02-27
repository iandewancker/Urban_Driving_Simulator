# This file exists to set up a consistent running framework for experimentation for the IROS paper
# Note that the fluids import occurs later, within specific functions, to limit the exposure
# This is because Edward seems to conflict with fluids ... as if I don't have enough shit to deal with

import numpy as np
import random
import time
import argparse


DOMAIN = [
    [1, 30],     # max_vel
    [.01, 100],  # pid_acc_p
    [.001, 5],   # pid_acc_i
    [.001, 5],   # pid_acc_d
    [.01, 100],  # pid_steer_p
    [.001, 5],   # pid_steer_i
    [.001, 5],   # pid_steer_d
]
PARAMETERS_IN_ORDER = (
  'max_vel', 'pid_acc_p', 'pid_acc_i', 'pid_acc_d', 'pid_steer_p', 'pid_steer_i', 'pid_steer_d',
)
METRICS_IN_ORDER = (
  'goal_reached', 'time_steps_taken', 'collision_count', 'activity_metric',
  'comfort_metric', 'angle_metric', 'angle_corrections', 'large_corrections'
)
COMPARISON_TERMS = ('comparison_index', 'my_index', 'winner')
CSV_ORDER_BASE = PARAMETERS_IN_ORDER + METRICS_IN_ORDER
CSV_ORDER_WITH_COMPARISON = CSV_ORDER_BASE + COMPARISON_TERMS


def reset_randomness(random_seed=None):
    if not hasattr(reset_randomness, 'random_seed'):
        if random_seed is None:
            raise ValueError('Must be called with initial seed')
        reset_randomness.random_seed = random_seed

    np.random.seed(reset_randomness.random_seed)
    random.seed(reset_randomness.random_seed)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--random-seed', type=int, required=False, default=27)
    parser.add_argument('--output-file', type=str, required=False)
    parser.add_argument('--num-tests', type=int, required=True)
    parser.add_argument('--max-steps', type=int, required=True)
    parser.add_argument('--verbosity', type=int, required=False, default=2)
    parser.add_argument('--init-duration', type=int, required=False, default=5)
    parser.add_argument('--preference-number', type=int, required=False)
    parser.add_argument('--beta', type=float, required=False)
    parser.add_argument('--optimizer', type=str, required=True, choices=('random', 'edward', 'none'))
    parser.add_argument('--print-lag', type=int, required=False, default=10)
    parser.add_argument('--num-ei-test-points', type=int, required=False, default=10000)
    parser.add_argument('--ties-swap-probability', type=float, required=False, default=0)
    args = parser.parse_args()

    assert args.num_tests >= args.init_duration
    assert args.optimizer != 'prefopt' or args.beta

    return args


def initialize(args, comparison=False):
    reset_randomness(args.random_seed)
    csv_order = CSV_ORDER_WITH_COMPARISON if comparison else CSV_ORDER_BASE

    output_file = args.output_file or f'{time.time()}_{args.max_steps}.csv'
    with open(output_file, 'w') as f:
        f.write(','.join(csv_order) + '\n')
    return output_file


def generate_simulator_with_parameters(parameters):
    import fluids

    simulator = fluids.FluidSim(
        visualization_level=0,  # How much debug visualization you want to enable. Set to 0 for no vis
        fps=0,  # If set to non 0, caps the FPS. Target is 30
        obs_space=fluids.OBS_GRID,  # OBS_BIRDSEYE, OBS_GRID, or OBS_NONE
        background_control=fluids.BACKGROUND_CSP  # BACKGROUND_CSP or BACKGROUND_NULL
    )

    state = fluids.State(
        layout=fluids.STATE_CITY,
        use_traffic_lights=False,
        background_cars=0,
        background_peds=0,
        controlled_cars=1,
        vis_level=0,
        tunable_parameters=parameters,
    )

    simulator.set_state(state)
    return simulator


def run_simulation_to_completion(simulator, max_steps):
    import fluids

    car_keys = simulator.get_control_keys()
    for _ in range(max_steps):
        simulator.step(simulator.get_supervisor_actions(fluids.SteeringVelAction, keys=car_keys))
        if simulator.reached_goal:
            break


def report_results(parameters, results, output_file, comparison=None):
    values_as_strings = []
    for key in CSV_ORDER_BASE:
        if key in parameters:
            values_as_strings.append(str(float(parameters[key])))
        else:
            values_as_strings.append(str(float(results[key])))

    if comparison is not None:
        for key in COMPARISON_TERMS:
            values_as_strings.append(str(int(comparison[key])))

    with open(output_file, 'a') as f:
        f.write(','.join(values_as_strings) + '\n')
