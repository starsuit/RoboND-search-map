import numpy as np
import cv2
import pdb

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an empty array the same size in x and y as the image
    # but just a single channel
    color_select = np.zeros_like(img[:,:,0])
    # Apply the thresholds for RGB and assign 1's
    # where threshold was exceeded
    within_thresh = ((img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2]))

    color_select[within_thresh] = 1
    # Return the single-channel binary image
    return color_select

def sample_thresh(img, rgb_thresh = (110, 110, 50)):
    color_select = np.zeros_like(img[:,:,0])

    sample_threshed = ((img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2]))

    color_select[sample_threshed] = 1

    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the
    # center bottom of the image.
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle)
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))

    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale):
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    mask = cv2.warpPerspective(np.ones_like(img[:,:,0]), M, (img.shape[1], img.shape[0]))
    return warped, mask


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO:
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    image = Rover.img
    dst_size = 5
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])
    # 2) Apply perspective transform
    warped, mask = perspect_transform(image, src = source, dst = destination)
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    navigable_color_select = mask * color_thresh(warped, rgb_thresh = (160, 160, 160))
    sample_color_select = mask * sample_thresh(warped, rgb_thresh = (120, 105, 50))
    obstacle_color_select = mask * np.absolute(np.float32(navigable_color_select) - 1)
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    Rover.vision_image[:,:,0] = 255 * obstacle_color_select
    Rover.vision_image[:,:,1] = 255 * sample_color_select
    Rover.vision_image[:,:,2] = 255 * navigable_color_select

    # 5) Convert map image pixel values to rover-centric coords
    xpix_navigable, ypix_navigable = rover_coords(navigable_color_select)
    xpix_sample, ypix_sample = rover_coords(sample_color_select)
    xpix_obstacle, ypix_obstacle = rover_coords(obstacle_color_select)
    # 6) Convert rover-centric pixel values to world coordinates
    #worldmap = Rover.worldmap
    #scale = 10
    # Get navigable pixel positions in world coords
    navigable_x_world, navigable_y_world = pix_to_world(xpix_navigable, ypix_navigable, Rover.pos[0], Rover.pos[1], Rover.yaw, Rover.worldmap.shape[0], scale =10)
    sample_x_world, sample_y_world = pix_to_world(xpix_sample, ypix_sample, Rover.pos[0], Rover.pos[1], Rover.yaw, Rover.worldmap.shape[0], scale =10)
    obstacle_x_world, obstacle_y_world = pix_to_world(xpix_obstacle, ypix_obstacle, Rover.pos[0], Rover.pos[1], Rover.yaw, Rover.worldmap.shape[0], scale =10)
    # 7) Update Rover worldmap (to be displayed on right side of screen)

    rover_steady = (Rover.pitch < 2 or Rover.pitch > 358) and (Rover.roll < 2 or Rover.roll > 358)
    # if rover is steady, increment worldmap pixels
    #pdb.set_trace()
    if rover_steady:
        # for every pixel that is an obstacle, increment the worldmap obstacle channel by 1, decrease the navigable channel by 1
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 2] -= 1
        Rover.worldmap[sample_y_world, sample_x_world, 1] += 1
        # for every pixel that is an obstacle, increment the worldmap navigable channel by 10, decrease the obstacle channel by 1
        # weighted in favour of navigable, to counter effect of shadows on RGB threshold
        Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 10
        Rover.worldmap[navigable_y_world, navigable_x_world, 0] -= 1
    # if not steady, don't adjust worldmap
    else:
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 0
        Rover.worldmap[sample_y_world, sample_x_world, 1] += 0
        Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 0




    # 8) Convert rover-centric pixel positions to polar coordinates
    dist_navigable, angles_navigable = to_polar_coords(xpix_navigable, ypix_navigable)
    dist_sample, angles_sample = to_polar_coords(xpix_sample, ypix_sample)
    dist_obstacle, angles_obstacle = to_polar_coords(xpix_obstacle, ypix_obstacle)


    #mean_dir = np.mean(angles_navigable)
    # Update Rover pixel distances and angles

    Rover.nav_dists = dist_navigable
    Rover.nav_angles = angles_navigable

    return Rover
