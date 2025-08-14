# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 13:24:41 2023

@author: u0072088
"""

from ..image_region import ImageRegion
from ..image_region_list import ImageRegionList

class ImageRegionBasedGrid:
    def __init__(self, anchor_region, image):
        self._image_regions = ImageRegionBasedGrid.generate(anchor_region, image)
        
    def get_image_region(self, index):
        return self._image_regions[index]
    
    @property
    def image_region_list(self):
        return ImageRegionList(self._image_regions)
    
    @staticmethod
    def generate(source_Image_Region, image):
        width, height = image.size
        
        width_division = ImageRegionBasedGrid.subdivide(width, source_Image_Region._width, source_Image_Region._x0)
        height_division = ImageRegionBasedGrid.subdivide(height, source_Image_Region._height, source_Image_Region._y0)
        
        image_regions = []
        for row_index, y in enumerate(height_division):
            for col_index, x in enumerate(width_division):
                new_region = ImageRegion(x[0], y[0], x[1], y[1])
                new_region.set_grid_data(row_index + 1, col_index + 1)
                new_region._grid['x'] = x[0]
                new_region._grid['y'] = y[0]
                image_regions.append(new_region)
                
        return image_regions
        
    @staticmethod
    def subdivide(full_size, Image_Region_size, starting_point):
        """
        Generates a list of tuples, containing the starting points and widths
        of each subdivision
        """
        # Get the offset
        offset = starting_point % Image_Region_size
        starting_points = [ [x + offset, Image_Region_size] for x in range(0, full_size, Image_Region_size)]
    
        # Adjust the size of the last element
        if starting_points[-1][0] > full_size:
            starting_points.pop()
            
        if starting_points[-1][0] + starting_points[-1][1] > full_size:
            starting_points[-1][1] = full_size - starting_points[-1][0]
            
        
        # Insert a starting element
        if starting_points[0][0] != 0:
            new_point = [0, starting_points[0][0]]
            starting_points.insert(0, new_point)
                
        return starting_points
        