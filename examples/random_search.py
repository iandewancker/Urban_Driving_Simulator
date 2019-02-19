import fluids
import numpy as np
import random
import time
import argparse


CSV_ORDER = (
  'max_vel', 'pid_acc_p', 'pid_acc_i', 'pid_acc_d', 'pid_steer_p', 'pid_steer_i', 'pid_steer_d',
  'goal_reached', 'time_steps_taken', 'collision_count', 'activity_metric',
  'comfort_metric', 'angle_metric', 'angle_corrections'
)


def reset_randomness(random_seed=None):
  if not hasattr(reset_randomness, 'random_seed'):
    if random_seed is None:
      raise ValueError('Must be called with initial seed')
    reset_randomness.random_seed = random_seed

  np.random.seed(reset_randomness.random_seed)
  random.seed(reset_randomness.random_seed)


def initialize():
  parser = argparse.ArgumentParser()
  parser.add_argument('--random-seed', type=int, required=False, default=1)
  parser.add_argument('--output-file', type=str, required=False)
  parser.add_argument('--num-tests', type=int, required=True)
  parser.add_argument('--max-steps', type=int, required=True)
  args = parser.parse_args()

  reset_randomness(args.random_seed)

  output_file = args.output_file or f'{time.time()}_{args.max_steps}.csv'
  with open(output_file, 'w') as f:
    f.write(','.join(CSV_ORDER) + '\n')
  return args.max_steps, output_file, args.num_tests


def generate_simulator_with_parameters(parameters):
  simulator = fluids.FluidSim(
    visualization_level=0,  # How much debug visualization you want to enable. Set to 0 for no vis
    fps=0,  # If set to non 0, caps the FPS. Target is 30
    obs_space=fluids.OBS_GRID,  # OBS_BIRDSEYE, OBS_GRID, or OBS_NONE
    background_control=fluids.BACKGROUND_CSP  # BACKGROUND_CSP or BACKGROUND_NULL
  )

  state = fluids.State(
    layout=fluids.STATE_CITY,
    background_cars=0,
    background_peds=0,
    controlled_cars=1,
  )

  simulator.set_state(state)
  return simulator


def run_simulation_to_completion(simulator, max_steps):
  car_keys = simulator.get_control_keys()
  for _ in range(max_steps):
    simulator.step(simulator.get_supervisor_actions(fluids.SteeringVelAction, keys=car_keys))
    if simulator.reached_goal:
      break


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


def report_results(parameters, results, output_file):
  values_as_strings = []
  for key in CSV_ORDER:
    if key in parameters:
      values_as_strings.append(str(float(parameters[key])))
    else:
      values_as_strings.append(str(float(results[key])))

  with open(output_file, 'a') as f:
    f.write(','.join(values_as_strings) + '\n')


def main():
  max_steps, output_file, num_tests = initialize()
  for _ in range(num_tests):
    parameters = create_random_parameters()
    reset_randomness()
    simulator = generate_simulator_with_parameters(parameters)
    run_simulation_to_completion(simulator, max_steps)
    results = simulator.wrap_up()
    report_results(parameters, results, output_file)


if __name__ == '__main__':
  main()
