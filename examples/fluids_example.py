import fluids
import pygame
import numpy as np
import scipy
import random
import sys


interesting_seeds = [
    27,
    54,
    55,
    57,
    64,
]


np.random.seed(interesting_seeds[0])
random.seed(interesting_seeds[0])

simulator = fluids.FluidSim(visualization_level=4,        # How much debug visualization you want to enable. Set to 0 for no vis
                            fps=0,                        # If set to non 0, caps the FPS. Target is 30
                            obs_space=fluids.OBS_GRID,# OBS_BIRDSEYE, OBS_GRID, or OBS_NONE
                            background_control=fluids.BACKGROUND_CSP) # BACKGROUND_CSP or BACKGROUND_NULL

state = fluids.State(
    layout=fluids.STATE_CITY,
    use_traffic_lights=False,
    background_cars=0,           # How many background cars
    background_peds=0,
    controlled_cars=1,            # How many cars to control. Set to 0 for background cars only
)


simulator.set_state(state)

car_keys = simulator.get_control_keys()


step_counter = 0
max_steps_counter = 1500

while True:
    actions = {}

    # Uncomment any of these lines.
    # VelocityAction is vel for car to move along trajectory
    # SteeringAction is steer, acc control
    # KeyboardAction is use keyboard input
    # SteeringVelAction is steer, vel control


    # actions = simulator.get_supervisor_actions(fluids.SteeringAction, keys=car_keys)
    # actions = simulator.get_supervisor_actions(fluids.VelocityAction, keys=car_keys)
    # actions = simulator.get_supervisor_actions(fluids.SteeringAccAction, keys=car_keys)
    actions = simulator.get_supervisor_actions(fluids.SteeringVelAction, keys=car_keys)

    #    actions = {k:fluids.VelocityAction(1) for k in car_keys}
    #    actions = {k:fluids.SteeringAction(0, 1) for k in car_keys}
    # actions = {k:fluids.KeyboardAction() for k in car_keys}
    #    actions = {k:fluids.SteeringVelAction(0, 1) for k in car_keys}

    rew = simulator.step(actions)
    obs = simulator.get_observations(car_keys)
    simulator.render()
    step_counter += 1

    if step_counter > max_steps_counter or simulator.reached_goal:
        break



# collect preformance metrics for agent car
results = simulator.wrap_up(step_counter)
print(results)

