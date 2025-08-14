# -*- coding: utf-8 -*-
from PIL import Image
import random

class Mosaic:
    
    @staticmethod
    def generate(image, image_region_list, margin = 2, linecolor = (255, 255, 255, 0), x_jitter_range = 0, y_jitter_range = 0):
        # Check incoming Image_Regions
        Mosaic.validate_image_region_attributes(image_region_list)
        
        # Get the original image size
        width, height = image.size
        
        # Calculate the size of the Mosaic, taking into margins and offsets
        n_rows, n_cols = Mosaic.get_maximum_grid_values(image_region_list.image_regions)
        total_width, total_height = Mosaic.calculate_new_image_size(width, height, n_rows, n_cols, margin)
        
        # Generate a blank image
        result = Image.new('RGBA', (total_width + x_jitter_range, total_height + y_jitter_range), linecolor)
        
        # Paste the Image_Regions into the Mosaic image
        for image_region in image_region_list.image_regions:
            # Calculate paste coordinates
            x = image_region._grid['x'] + image_region._grid['col'] * margin
            y = image_region._grid['y'] + image_region._grid['row'] * margin
            
            # Adjust for random offset
            x_jitter = random.randint(-x_jitter_range, x_jitter_range)
            y_jitter = random.randint(-y_jitter_range, y_jitter_range)
            
            # Paste Image_Region into final image
            if image_region._image == None:
                extracted_image = image_region.extract_from_image(image)
            else:               
                extracted_image = image_region.extract_from_image(image_region._image)
                
            new_x, new_y = x + x_jitter, y + y_jitter
                
            result.paste(extracted_image, (new_x, new_y))
        
        return result
    
    @staticmethod
    def validate_image_region_attributes(image_region_list):
        """
        To generate a Mosaic, the algorithm needs row and column values
        for the Image_Region. This function checks if these attributes are present
        for each Image_Region.

        Parameters
        ----------
        Image_Regions : list
            a list of Image_Region objects.

        Returns
        -------
        None.

        """
        for image_region in image_region_list.image_regions:
            if not hasattr(image_region, '_grid'):
                raise AttributeError("At least one of the Image_Regions does not have a _grid attribute")
        
    @staticmethod
    def get_maximum_grid_values(Image_Regions):
        max_row = max(Image_Region._grid['row'] for Image_Region in Image_Regions)
        max_col = max(Image_Region._grid['col'] for Image_Region in Image_Regions)
        
        return max_row, max_col

    @staticmethod
    def calculate_new_image_size(original_width, original_height, n_columns, n_rows, margin):
        new_width = original_width + (n_columns + 1) * margin
        new_height = original_height + (n_rows + 1) * margin
        
        return new_width, new_height
        