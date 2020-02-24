import numpy as np
import time

from experiments.simulation import (
    generate_simulator_with_parameters,
    initialize,
    parse_args,
    report_results,
    reset_randomness,
    run_simulation_to_completion
)


# Should update this to use DOMAIN from simulation
def create_random_parameters():
    np.random.seed(int(1e9 * np.mod(time.time(), 1)))
    return {
        'max_vel': np.random.uniform(1, 30),
        'pid_acc_p': np.random.uniform(0.01, 100),
        'pid_acc_i': np.random.uniform(0.001, 5),
        'pid_acc_d': np.random.uniform(0.001, 5),
        'pid_steer_p': np.random.uniform(0.01, 100),
        'pid_steer_i': np.random.uniform(0.001, 5),
        'pid_steer_d': np.random.uniform(0.001, 5),
    }


def main():
    args = parse_args()
    output_file = initialize(args)
    start = time.time()
    for k in range(args.num_tests):
        parameters = create_random_parameters()
        reset_randomness()

        simulator = generate_simulator_with_parameters(parameters)
        run_simulation_to_completion(simulator, args.max_steps)
        results = simulator.wrap_up()

        report_results(parameters, results, output_file)
        if args.verbosity == 2 or (args.verbosity == 1 and (k + 1) % args.print_lag == 0) or k == 0:
            end = time.time()
            print(f'Iteration {k:4d}, {end - start:6.2f} seconds since last print')
            start = time.time()


if __name__ == '__main__':
    main()

# To run this, execute the following from the top directory
# PYTHONPATH=. python experiments/random_sampling.py --output-file some-results.csv --num-tests 5 --max-steps 1000 --optimizer none
