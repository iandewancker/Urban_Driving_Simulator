import numpy as np
import time

from experiments.simulation import (
    DOMAIN,
    generate_simulator_with_parameters,
    initialize,
    PARAMETERS_IN_ORDER,
    parse_args,
    reset_randomness,
    report_results,
    run_simulation_to_completion,
)
from experiments.enqueue_simulation import run_simulation_with_queue
from experiments.state_preference import recover_preference_query
from prefopt.random_optimizer import RandomOptimizer
from prefopt.edward_optimizer import EdwardOptimizer


# def run_simulation(parameters, args):
#     reset_randomness()
#     simulator = generate_simulator_with_parameters(parameters)
#     run_simulation_to_completion(simulator, args.max_steps)
#     return simulator.wrap_up()
#
# There is, apparently, a great amount of unpleasantness between the fluids simulator and Edward.
# I am going to get rid of Edward when I can, but right now I lack the time.
# I think that, maybe, by wrapping this in a multiprocessing queue, we can keep them separated.
# We'll see if this actually works ...
def run_simulation(parameters, args):
    return run_simulation_with_queue(parameters, args.max_steps, args.random_seed)


def break_tie_if_needed(preference, args):
    return np.random.random() > .5 if (args.optimizer == 'edwardT' and preference == 0) else preference



# This loop is a little grosser than I would like because of the fact that the preference query is not dependent
# on the parameters, but rather the metrics.  Rather than try and build a weird wrapper with the optimizer object
# contained inside of a preference_query, I'm forgoing the run_preference_search call and writing a custom loop
# here.  This will allow me to store metrics and not recompute metrics for each preference.
#
# fake_preference_query is only used to get through the random initialization phase, which we immediately replace with
# the actual preferences.
def main():
    args = parse_args()
    output_file = initialize(args, comparison=True)

    def fake_preference_query(x1, x2):
        return 1

    actual_preference_query_with_metrics = recover_preference_query(args.preference_number)

    if args.optimizer == 'random':
        preference_optimizer = RandomOptimizer(fake_preference_query, DOMAIN, debug=args.verbosity == 2)
    else:
        preference_optimizer = EdwardOptimizer(
            fake_preference_query,
            DOMAIN,
            args.beta,
            ei_sample_strategy='lhs',
            num_ei_test_points=args.num_ei_test_points,
            debug=args.verbosity == 2,
        )

    joint_metrics = []
    preference_optimizer.random_initialization(args.init_duration)
    for parameter_values in preference_optimizer.joint_points:
        joint_metrics.append(run_simulation(dict(zip(PARAMETERS_IN_ORDER, parameter_values)), args))

    indexes_printed = set()  # This is fuckin terrible
    for preference_index, (i1, i2) in enumerate(zip(
        preference_optimizer.preference_organizer.first_index_to_joint_index,
        preference_optimizer.preference_organizer.second_index_to_joint_index,
    )):
        results_a = joint_metrics[i1]
        results_b = joint_metrics[i2]
        preference = break_tie_if_needed(actual_preference_query_with_metrics(results_a, results_b), args)
        preference_optimizer.preference_organizer.preferences[preference_index] = preference

        if i1 not in indexes_printed:
            indexes_printed.add(i1)
            parameters = dict(zip(PARAMETERS_IN_ORDER, preference_optimizer.joint_points[i1]))
            comparison = {'comparison_index': i1, 'my_index': i1, 'winner': 0}
            report_results(parameters, results_a, output_file, comparison)

        indexes_printed.add(i2)
        parameters = dict(zip(PARAMETERS_IN_ORDER, preference_optimizer.joint_points[i2]))
        comparison = {'comparison_index': i1, 'my_index': i2, 'winner': preference}
        report_results(parameters, results_b, output_file, comparison)

    print(f'Initialization with {args.init_duration} comparisons completed')

    # Could do this in a variety of different ways, but this seems simple enough
    i1 = np.random.randint(preference_optimizer.num_unique_points)
    best_point = preference_optimizer.joint_points[i1, :]

    start = time.time()
    while preference_optimizer.num_observations < args.num_tests:
        print('Starting work on next point')
        next_point = preference_optimizer.create_next_point()
        print('Completed work on next point', next_point)

        # First add the fake result, then run the comparison, then update the preferences appropriately
        # NOTE(Mike) - This takes advantage of the fact that we know we already have the metrics for best_point
        #              If this were not true we would have to run a check, or just rerun the whole list
        #              Actually, maybe both are better options but I want to try this first, I guess
        preference_optimizer.preference_organizer.add_result(best_point, next_point, 1)
        results_a = joint_metrics[preference_optimizer.preference_organizer.first_index_to_joint_index[-1]]

        i2 = preference_optimizer.preference_organizer.second_index_to_joint_index[-1]
        parameters = dict(zip(PARAMETERS_IN_ORDER, preference_optimizer.joint_points[i2]))
        if i2 < len(joint_metrics):
            results_b = joint_metrics[i2]
        else:
            assert i2 == len(joint_metrics)
            results_b = run_simulation(parameters, args)
            joint_metrics.append(results_b)

        preference = break_tie_if_needed(actual_preference_query_with_metrics(results_a, results_b), args)
        preference_optimizer.preference_organizer.preferences[-1] = preference

        if preference_optimizer.debug:
            print(preference_optimizer.num_observations, results_a, results_b, preference)

        indexes_printed.add(i2)
        comparison = {'comparison_index': i1, 'my_index': i2, 'winner': preference}
        report_results(parameters, results_b, output_file, comparison)

        if preference == -1 or (preference == 0 and np.random.random() < preference_optimizer.ties_swap_probability):
            best_point = next_point
            i1 = i2

        num_obs = preference_optimizer.num_observations
        if args.verbosity == 2 or (args.verbosity == 1 and (num_obs + 1) % args.print_lag == 0):
            end = time.time()
            print(f'Comparison {num_obs:4d} completed, {end - start:6.2f} seconds since last print')
            start = time.time()


if __name__ == '__main__':
    main()

# To run this, I'm assuming you have prefopt in a neighboring directory (or with pypi, maybe)
# For random search
# PYTHONPATH=prefopt_priv/src:Urban_Driving_Simulator python Urban_Driving_Simulator/experiments/run_optimization.py --output-file some-results.csv --num-tests 8 --max-steps 1000 --optimizer random --init-duration 4 --preference-number 1
# For Edward
# I had to add this to my environment to get this to work correctly
#   export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
# PYTHONPATH=prefopt_priv/src:Urban_Driving_Simulator python Urban_Driving_Simulator/experiments/run_optimization.py --output-file some-results.csv --num-tests 8 --max-steps 1000 --optimizer edward --init-duration 4 --beta 1.1 --preference-number 1
