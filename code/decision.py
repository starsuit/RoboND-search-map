import numpy as np
import time
import pdb


# This is where you can build a decision tree for determining throttle, brake and steer
# commands based on the output of the perception_step() function
def decision_step(Rover):
    Rover.count += 1
    # Implement conditionals to decide what to do given perception data
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward':
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:
                # If mode is forward, navigable terrain looks good
                #pdb.set_trace()
                rover_nearstopped = Rover.vel > -0.1 and Rover.vel < 0.1
                if rover_nearstopped:
                    if Rover.stuck_yet == False and Rover.count > 1*28:
                        Rover.count = 0
                        Rover.stuck_yet = True
                    elif Rover.count > (5 * 28):
                    # But the rover doesn't go anywhere for ~5 seconds
                        Rover.throttle = 0
                        # Stop and go into stuck mode
                        Rover.mode = 'stuck'

                    elif Rover.vel < Rover.max_vel:
                        # Set throttle value to throttle setting
                        Rover.throttle = Rover.throttle_set
                    else: # Else coast
                        Rover.throttle = 0
                    # Reset the time counter
                # and velocity is below max, then throttle
                elif Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # If the rover is steady, set steering to average angle clipped to the range +/- 15
                rover_steady = (Rover.pitch < 2 or Rover.pitch > 358) and (Rover.roll < 2 or Rover.roll > 358)
                #pdb.set_trace()
                if rover_steady:
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi) +12, -15, 15)
                # otherwise just go straight
                else:
                    Rover.steer = 0

            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                # Set mode to "stop" and hit the brakes!
                Rover.throttle = 0
                # Set brake to stored brake value
                Rover.brake = Rover.brake_set
                Rover.steer = 0
                Rover.mode = 'stop'

        # If in stuck mode, stop everything
        elif Rover.mode == 'stuck':
            Rover.throttle = 0
            Rover.brake = 0
            Rover.steer = 0
            # Then begin to turn
            Rover.mode = 'turning'

        # If in turning mode, turn for ~2 seconds
        elif Rover.mode == 'turning':
            Rover.turn_count +=1
            if Rover.turning == False:
                # if Rover's recorded mode isn't turning yet, change it to turning
                Rover.turning = True
                # set a recorded timer
                Rover.turn_count = 0
                #Rover.steer = 0
            # Begin turning
            Rover.steer = -15
            if Rover.turn_count > (2 * 28):
                # once ~2 seconds has passed, stop and start going forward again
            # If we see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
                    # reset the recorded mode
                    Rover.turning = False
                    Rover.timeRev = 0
                else:
                    Rover.mode = 'stop'
                    Rover.stuck_yet = False
                    Rover.turning = False

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if np.absolute(Rover.vel) > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
                    Rover.stuck_yet = False
                    Rover.turning = False
    # Just to make the rover do something
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0

    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
        #If near a sample, stop!
    elif Rover.near_sample and Rover.vel > 0:
        # Set mode to "stop" and hit the brakes!
        Rover.throttle = 0
        # Set brake to stored brake value
        Rover.brake = Rover.brake_set
        Rover.steer = 0
        Rover.mode = 'stop'


    return Rover
