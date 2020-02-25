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


def preference1(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    if results_a['time_steps_taken'] < results_b['time_steps_taken']:
        return 1
    return -1


def preference2(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    if abs(results_a['time_steps_taken'] - results_b['time_steps_taken']) < 32:
        return 0
    if results_a['time_steps_taken'] < results_b['time_steps_taken']:
        return 1
    return -1


def preference3(results_a, results_b):
    initial_check = _parse_initial(results_a, results_b)
    if initial_check != TIE_SO_FAR:
        return initial_check

    if abs(results_a['time_steps_taken'] - results_b['time_steps_taken']) < 8:
        return 0
    if results_a['time_steps_taken'] < results_b['time_steps_taken']:
        return 1
    return -1


def recover_preference_query(preference_number):
    if preference_number is None:
        raise ValueError('No preference was stated')
    if preference_number == 1:
        return preference1
    if preference_number == 2:
        return preference2
    if preference_number == 3:
        return preference3
