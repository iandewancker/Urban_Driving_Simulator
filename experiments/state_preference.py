# This file defines the different types of experiments we are interested in running
#
# The metrics in the results dict are
#   'goal_reached', 'time_steps_taken', 'collision_count', 'activity_metric',
#   'comfort_metric', 'angle_metric', 'angle_corrections', 'large_corrections'
#
# The values returned are
#     1 - results_a wins
#     0 - tie
#    -1 - results_b wins

TERRIBLE = 'terrible'
A_WINS = 'a_wins'
B_WINS = 'b_wins'
TIE_SO_FAR = 'tie_so_far'


def _check_completed_safely(results_a, results_b):
    if results_a['collision_count'] and results_b['collision_count']:
        return TERRIBLE
    if not (results_a['goal_reached'] or results_b['goal_reached']):
        return TERRIBLE

    if not results_a['collision_count'] and results_b['collision_count']:
        return A_WINS
    if results_a['collision_count'] and not results_b['collision_count']:
        return B_WINS

    if results_a['goal_reached'] and not results_b['goal_reached']:
        return A_WINS
    if not results_a['goal_reached'] and results_b['goal_reached']:
        return B_WINS

    return TIE_SO_FAR


def _parse_initial(results_a, results_b):
    completed_safely = _check_completed_safely(results_a, results_b)
    if completed_safely == TERRIBLE:
        return 0
    if completed_safely == A_WINS:
        return 1
    if completed_safely == B_WINS:
        return -1
    return TIE_SO_FAR


def _check_metric(results_a, results_b, metric_name, tolerance=None, threshold=None, to_be_minimized=True):
    a = results_a[metric_name]
    b = results_b[metric_name]

    if threshold is not None and (
        (to_be_minimized and a < threshold and b < threshold) or
        (not to_be_minimized and a > threshold and b > threshold)
    ):
        return 0

    if tolerance is not None and abs(a - b) < tolerance:
        return 0
    if (to_be_minimized and a < b) or (not to_be_minimized and a > b):
        return 1
    return -1


def preference1(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    return _check_metric(results_a, results_b, 'time_steps_taken')


def preference2(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    return _check_metric(results_a, results_b, 'time_steps_taken', tolerance=32)


def preference3(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    return _check_metric(results_a, results_b, 'time_steps_taken', tolerance=4)


def preference4(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    time_check = _check_metric(results_a, results_b, 'time_steps_taken', tolerance=10)
    comfort_check = _check_metric(results_a, results_b, 'comfort_metric', threshold=.5, tolerance=.1)
    return comfort_check or time_check


def preference5(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    time_check = _check_metric(results_a, results_b, 'time_steps_taken', tolerance=3)
    comfort_check = _check_metric(results_a, results_b, 'comfort_metric', threshold=.3, tolerance=.03)
    return comfort_check or time_check


def preference6(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    time_check = _check_metric(results_a, results_b, 'time_steps_taken', threshold=300, tolerance=12)
    comfort_check = _check_metric(results_a, results_b, 'comfort_metric', tolerance=.1)
    return time_check or comfort_check


def preference7(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    time_check = _check_metric(results_a, results_b, 'time_steps_taken', threshold=160, tolerance=12)
    comfort_check = _check_metric(results_a, results_b, 'comfort_metric')
    return time_check or comfort_check


def recover_preference_query(preference_number):
    if preference_number is None:
        raise ValueError('No preference was stated')
    if preference_number == 1:
        return preference1
    if preference_number == 2:
        return preference2
    if preference_number == 3:
        return preference3
    if preference_number == 4:
        return preference4
    if preference_number == 5:
        return preference5
    if preference_number == 6:
        return preference6
    if preference_number == 7:
        return preference7
    raise ValueError('WTF test are you running')
