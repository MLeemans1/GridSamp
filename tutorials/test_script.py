# -*- coding: utf-8 -*-

# LOAD IAM
from PIL import Image, ImageChops
import matplotlib.pyplot as plt
import os
import numpy as np

# Change directory to that of IAM to load it
os.chdir(r'C:\Users\u0072088\OneDrive - KU Leuven\Documents\03-projects\image-aesthetic-map-toolbox\image-aesethic-map-toolbox')

# Open IAM toolbox
from grid_samp import ImageRegion
from grid_samp.grids import FixedGrid, RecursiveGrid, ImageRegionBasedGrid, SpacedGrid
from grid_samp.assemble import ROI, ImageRegionIntersectionHeatmap, Mosaic, Contextualize

# Set environment to current environment
os.chdir("Tutorials")

#------------#
# Load Image #
#------------#
image = 'example img.jpg'
image_2 = 'example_img_2.jpg'

image = Image.open(image).convert("RGB")
image_2 = Image.open(image_2)

image_region = ImageRegion.from_image(image)


#%% 42. Test shuffling with equal sizes:
image_region = ImageRegion(133, 133, 150, 150)

grid = ImageRegionBasedGrid(image_region, image)

image_regions = grid.image_region_list
image_regions = image_regions.shuffle_within_size()
mosaic = Mosaic.generate(image, image_regions)

plt.imshow(mosaic)
#%% 41. Implement shuffle within rows
#
fixed_grid =  FixedGrid(Image.open('example img.jpg'), 8, 8)

image_regions = fixed_grid.image_regions
image_regions_shuffle_rows = image_regions.shuffle_within_rows()
image_regions_shuffled_cols = image_regions.shuffle_within_columns()


roi_image_fixed_1     = Mosaic.generate(image, image_regions_shuffle_rows)
roi_image_fixed_2     = Mosaic.generate(image, image_regions_shuffled_cols)


plt.subplot(1,2,1)
plt.imshow(roi_image_fixed_1)
plt.subplot(1,2,2)
plt.imshow(roi_image_fixed_2)

#%% 36 Create SpacedGrid
#
original_image = Image.open("example img.jpg").convert("RGB")
spaced_grid = SpacedGrid(image, 100, 100, 200, 200, 40, 40)

image_regions = spaced_grid.image_regions


image_mosaic = Mosaic.generate(original_image, image_regions, margin = 0)
image_roi    = ROI.generate(original_image, spaced_grid.image_regions)

plt.subplot(1, 2, 1)
plt.imshow(image_mosaic)
plt.subplot(1, 2, 2)
plt.imshow(image_roi)

#%% #37 Leave one region untouched
#
original_image = Image.open("example img.jpg").convert("RGB")
blurred_image_region = ImageRegion.from_image(original_image)
blurred_image_region.blur(radius = 20)

blurred_image = blurred_image_region.extract_from_image(original_image)


fixed_grid = FixedGrid(image, n_rows = 5, n_cols = 5)
image_regions = fixed_grid.image_regions
image_regions[5].set_image(original_image)


image_mosaic = Mosaic.generate(blurred_image, image_regions, margin = 0)

plt.subplot(1, 2, 1)
plt.imshow(blurred_image)
plt.axis('off')
plt.subplot(1, 2, 2)
plt.imshow(image_mosaic)
plt.axis('off')

#%% 
# Issue #38: recursive grid indexing
recursive_grid = RecursiveGrid(image_region, 3)
fixed_grid =  FixedGrid(Image.open('example img.jpg'), 8, 8)


roi_image_recursive = ROI.generate(image, recursive_grid.get_recursion_level_images(3), draw_index = True)
roi_image_fixed     = ROI.generate(image, fixed_grid.image_regions, draw_index = True)

plt.subplot(1,2,1)
plt.imshow(roi_image_recursive)
plt.subplot(1,2,2)
plt.imshow(roi_image_fixed)
#%% Test Fixed Grid
fixed_grid = FixedGrid(image)
fixed_grid_image_regions = fixed_grid.image_regions

roi_image = ROI.generate(image, fixed_grid_image_regions)

plt.imshow(roi_image)

#%% Test shuffle
fixed_grid = FixedGrid(image, 8, 8)
fixed_grid_image_regions = fixed_grid.image_regions.shuffle(pass_region = [1])

mosaic_image = Mosaic.generate(image, fixed_grid_image_regions, margin = 0).convert("RGB")

diff_image = np.array(mosaic_image.convert("L")) - np.array(image.convert("L"))
diff_image[diff_image[:] > 0] = 200
plt.subplot(2, 2, 1)
plt.imshow(image)
plt.axis('off')
plt.subplot(2, 2, 3)
plt.imshow(mosaic_image)
plt.axis('off')
plt.subplot(1, 2, 2)
plt.imshow(diff_image)
plt.axis('off')


#%% Test image region manipulation functions
fixed_grid = FixedGrid(image, n_rows = 10, n_cols = 10)

image_region_list = fixed_grid.image_regions
image_region = image_region_list.get(5)

image_region._pixel_scramble = True
#image_region.set_mask(2, sigma = 0.4) 
image_region_list = image_region_list.replace(5, image_region)
image_region_image = image_region.extract_from_image(image)

mosaic_image = Mosaic.generate(image, image_region_list, margin = 0)


plt.imshow(mosaic_image)
#%% Test image region manipulation function in image region list
fixed_grid = FixedGrid(image, n_rows = 10, n_cols = 10)
image_regions = fixed_grid.image_regions

for image_region in image_regions:
    image_region.set_mask(2, sigma = 0.25)

image_mosaic = Mosaic.generate(image, image_regions, margin = 0)


plt.imshow(image_mosaic)
plt.axis('off')




#%% Test
# Create initial image region and grid
image_region = ImageRegion.from_image(image)
recursive_grid = RecursiveGrid(image_region, recursion_depth=4)

# Get recursion level 2 regions
level_2_regions = recursive_grid.get_recursion_level_images(recursion_level = 2)

original_image = Mosaic.generate(image, level_2_regions, margin = 0)

original_region = level_2_regions.get(1)
original_region.blur()
original_region.set_transparency(0.5)

level_2_regions = level_2_regions.replace(1, original_region)
after_replace_1 = Mosaic.generate(image, level_2_regions, margin = 0)


plt.subplot(1, 3, 1)
plt.imshow(original_image)
plt.subplot(1, 3, 2)
plt.imshow(after_replace_1)

#%%
#-------------------------#
# Image Region based Grid #
#-------------------------#
# Define anchor image region location
x, y, width, height = (750, 750, 240, 240)

# Extract anchor patch
anchor = ImageRegion(x, y, width, height)

# generate grid based on anchor and image
image_region_based_grid = ImageRegionBasedGrid(anchor, image)
image_region_based_grid_region = image_region_based_grid.get_image_region(20)
image_region_based_grid_region.extract_from_image(image)


#%%
#----------------#
# Recursive Grid #
#----------------#

# Initialize a RecursiveGrid with three recursion levels
recursive_grid = RecursiveGrid(image_region, recursion_depth = 4)

# Get a list of image regions at the third recursion level
level_1_regions = recursive_grid.get_recursion_level_images(recursion_level = 1)



#-------------------#
# Inserting a patch #
#-------------------#
width  = level_1_regions.image_regions[0]._width
height = level_1_regions.image_regions[0]._height

new_image_region = ImageRegion(500, 500, width, height, image_2)

inserted_regions = level_1_regions.replace(0, new_image_region)

before_insert = Mosaic.generate(image, level_1_regions, margin = 2)
after_insert = Mosaic.generate(image, inserted_regions, margin = 2)

plt.subplot(1, 2, 1)
plt.imshow(before_insert)
plt.subplot(1, 2, 2)
plt.imshow(after_insert)

for idx, image_region in enumerate(level_1_regions.image_regions):
    if hasattr(image_region, '_grid'):
        print(image_region._grid)
    else:
        print("No image region for %d"%idx)
    if hasattr(image_region, '_image'):
        print(image_region._image)
        
#%%
#-----------#
# Replacing #
#-----------#
# Define new image region from image
x, y, width, height = (150, 300, 120, 120)

# Extract new patch
new_image_region = ImageRegion(x, y, width, height)
   
# Replace the old image region by the new image region and save as a new list
replaced_regions = level_1_regions.swap(0, 1)

before_swap = Mosaic.generate(image, level_1_regions, margin = 2)
after_swap = Mosaic.generate(image, replaced_regions, margin = 2)

difference_image = ImageChops.difference(before_swap, after_swap)
plt.subplot(1, 3, 1)
plt.imshow(before_swap)
plt.subplot(1, 3, 2)
plt.imshow(after_swap)
plt.subplot(1, 3, 3)
plt.imshow(difference_image)

#%% shuffling and swapping in a image grid based grid image regions grid based regions

image_region_grid_region_list = image_region_based_grid.image_region_list

#----------#
# Swapping #
#----------#

# Perform swap - ensure that the image regions are equal in size.
swapped_regions = image_region_grid_region_list.swap(region_1_index = 3, region_2_index = 44)

after_swap = Mosaic.generate(image, image_region_grid_region_list, margin = 2)

#-----------#
# Shuffling #
#-----------#

# Perform shuffle - ensure that either the x_axis, y_axis, or interal arguments are set to True.
shuffled_regions_1 = image_region_grid_region_list.shuffle()
shuffled_regions_2 = image_region_grid_region_list.shuffle(fix_unit = 'rows')

after_shuffle_1 = Mosaic.generate(image, shuffled_regions_1, margin = 2)
after_shuffle_2 = Mosaic.generate(image, shuffled_regions_2, margin = 2)

plt.subplot(1, 3, 1)
plt.imshow(after_swap)
plt.subplot(1, 3, 2)
plt.imshow(after_shuffle_1)
plt.subplot(1, 3, 3)
plt.imshow(after_shuffle_2)
