import signal
import time
from multiprocessing import Queue

from experiments.simulation import (
    generate_simulator_with_parameters,
    reset_randomness,
    run_simulation_to_completion,
)
from prefopt.edward_optimizer import QueueRunner, add_to_queue, timeout_handler, TimeoutError, TensorFlowError


@add_to_queue
def _run_simulation_in_queue_for_real(parameters, max_steps, random_seed):
    reset_randomness(random_seed)
    simulator = generate_simulator_with_parameters(parameters)
    run_simulation_to_completion(simulator, max_steps)
    return simulator.wrap_up()


def _run_simulation_with_queue(parameters, max_steps, random_seed, timeout_factor=0):
    if not hasattr(_run_simulation_with_queue, 'previous_time'):
        _run_simulation_with_queue.previous_time = 0

    start = time.time()
    if timeout_factor and _run_simulation_with_queue.previous_time:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_factor * _run_simulation_with_queue.previous_time + .5))

    q = Queue()
    p = QueueRunner(target=_run_simulation_in_queue_for_real, args=(q, parameters, max_steps, random_seed))
    p.start()
    p.join()
    if p.exception:
        error, traceback = p.exception
        print(traceback)  # There's gotta be a better way to do this
        raise error
    next_point = q.get()

    signal.alarm(0)
    end = time.time()
    _run_simulation_with_queue.previous_time = end - start
    return next_point


def run_simulation_with_queue(parameters, max_steps, random_seed, timeout=True):
    x_next = None
    min_timeout_factor = 2
    max_timeout_factor = 10
    timeout_factor = min_timeout_factor if timeout else 0
    while x_next is None:
        try:
            x_next = _run_simulation_with_queue(parameters, max_steps, random_seed, timeout_factor)
        except TimeoutError:
            print(f'Timeout encountered with parameters {parameters}, max_steps {max_steps}')
            if timeout_factor == min_timeout_factor:
                print('Retrying with higher timeout limit')
                timeout_factor = max_timeout_factor
            else:
                print('Already retried so crashing out')
                raise
        except TensorFlowError as e:
            if 'assertion failed' in e.args[0]:
                print(f'InvalidArgumentError with parameters {parameters}, max_steps {max_steps}, retrying')
            else:
                raise
    return x_next
