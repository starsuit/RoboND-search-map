## Project: Search and Sample Return

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook).
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands.
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./misc/notebook_video.gif
[image2]: ./misc/rover.gif
[image3]: ./misc/screenshot2.png

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.
* After running all the notebook code, I started by running the rover simulator to generate my own images.
* I changed the file path to my recorded image directory to select one at random to work with.
* Taking some tester images from my rover, I identified the RGB thresholds for the sample rocks using a color meter program.
* I made a new function, `sample_thresh()` to identify where the sample rocks appeared in the app.

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result.
* I updated the `process_image()` function to call on the various functions in the notebook where appropriate, including my new `sample_thresh()` function.
* I also added "obstacles" pixel values by reversing the `navigable_color_select` values. This works as they are mutually exclusive- where one is positive, the other should be negative etc.
* I made sure that the notebook was looking at my recorded images and CSV file to process the video correctly.
* Running the remainder of the code successfully generated my video.

  ![Section of my generated notebook video][image1]
### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.


#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

Simulator resolution: 1024 x 768  
Simulator graphics: Good  
Windowed: True  
FPS: ~28-33  

* I began by filling in the `perception_step()` code as it was written in the notebook. I added my `sample_thresh()` function further up the `perception.py` script to apply the filter to sample rocks. Next I updated the `Rover.vision_image` to multiply each channel by 255 where the pixels for obstacles, navigable and samples were- this gave me a view of where the thresholds appeared in color, otherwise my thresholded view on the simulator came up black. This made the rover run reasonably ok, but fidelity was not too great and the rover got stuck behind (and on) rocks a lot. It did manage to plot sample rocks with good accuracy so I didn't feel much need to adjust those thresholds for now.  


* I next attempted to modify the `decision_step()` code to only use images where the rover was reasonably level (e.g. pitch and roll were near 0). I found that it helped my understanding of the code to set these near zero conditions as a temporary variable `rover_steady`, which allowed me to phrase my code: `if rover_steady:`. I implemented this both in the "Update Rover worldmap" section of `perception.py` and the rover steering angle selection in `decision.py`.  


* Next I found that the fidelity of my rover decreased significantly if it got stuck- often it would sit behind a low rock, trying to go forward as it could see over the rock, thinking it had navigable terrain in front. I found it difficult for the rover to know it was stuck- the telemetry is updated instantaneously so the rover had no "memory" as such. To get around this I introduced a counter system: each time the `decision_step()` code was run, the counter would increment. I knew from running the simulator that the `decision_step()` was run around 28 times per second, so to count 1 second the `decision_step()` would have to run 1x28 times, 2 seconds 2x28 times etc. I also introduced a `Rover.stuck_yet` mode, which was either `True` or `False`. It would start off as `False`, and if the rover found itself stopped, it would switch this value to `True`, and begin counting. If the rover found this value to still be `True`, it would continue incrementing the count, and this way record how long it had been stuck for. If the rover was stuck for more than 5 seconds, it went into "stuck" mode. This set throttle and steer to zero and initiated "turning" mode.  


* Turning mode was set up in the same way as the time counting above where the rover decided if it was stuck. The mode initialized a -15 degree turn, then recorded how long it was turning for. Once the rover had been turning for around 2 seconds, it stopped and attempted to go forwards. If it could not, the turn would initialize again. I found that this has solved most issues with getting stuck, although the rover can take some time to free itself.  


* I also wanted to try and make the rover a "wall-crawler". After experimenting with min and max angles, I found that the simplest solution was just to add a certain number of degrees to the mean of navigable angles:
`Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi) + 12 , -15, 15)`. There was some trial and error as I varied my angles- too large an angle would steer the rover into the wall a lot, too small and it wouldn't stick to the wall at all. I settled on 12, making the rover offset the mean navigable path by 12 degrees, hugging the left wall.   


* Around this time I also implemented a few debugging features. Adding the rover status into the simulator itself, overlaid on the worldmap helped me understand the rover's immediate "thinking state". I also added the new features like `Rover.stuck_yet` and `Rover.count` to the printout in the command line. I also changed the formatting so that each feature printed on a line. This meant that the values would "stay in the same place" in the command line as they updated.  
  ![Command line printout][image3]


* The final thing I did was to experiment with the rover worldmap in the `perception.py` file. I wanted to increase my fidelity score, as often my rover would mistake shadowy sand for obstacle rocks. I began tweaking how much the worldmapped pixels would increment, adjusting the navigable channel up by 10 each time. I found that this had little effect, so took a different approach. I thought that when pixels were thresholded as navigable, I'd want to increase their "navigableness", and decrease their "obstacleness" and vice-versa. I implemented this like so:  
```python
        # for every pixel that is an obstacle, increment the worldmap obstacle channel by 1, decrease the navigable channel by 1
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 2] -= 1
        # for every pixel that is an obstacle, increment the worldmap navigable channel by 10, decrease the obstacle channel by 1
        # weighted in favour of navigable, to counter effect of shadows on RGB threshold
        Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 10
        Rover.worldmap[navigable_y_world, navigable_x_world, 0] -= 1
```
I left the rock channel as it was, as there seemed to be no issue with fidelity there.    

* All this had the rover running with around 80% + fidelity, which I was pretty happy with. The rover very rarely gets un-fixably stuck, and this mainly seems to be down to bugs in the simulation- sometimes the rover gets stuck "in" a rock, and "sees" clear space in front.


* Potential failures: as I mentioned above, the rover does get stuck on simulation bugs. I would like to develop a more efficient method of getting unstuck, possibly including reversing. Depending on where the rover starts the simulation, it's method of exploration sometimes misses a section of the map. This might be improved by adjusting the "wall crawler" functionality.

* I'd like to pursue the project further; I think once my grasp of python has improved I could do a lot more. I'd like to encourage the rover to visit previously unexplored places and ignore already explored places. I'd also like to work on the sample return, getting the rover to home in on sample rocks and pick them up.

  ![Sped up gif of my rover running autonomously][image2]
