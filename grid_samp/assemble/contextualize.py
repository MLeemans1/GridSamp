# -*- coding: utf-8 -*-
from PIL import Image
from .roi import ROI

class Contextualize:
    @staticmethod
    def generate(image, image_region, Image_Region_position = "center", context_position = "right", draw_roi = True):
        """
        Generates a contextualizd image representation of the Image_Region using 
        the provided image

        Parameters
        ----------
        image : PIL Image object
            The full image from which the Image_Region will be extracted.
        Image_Region : Image_Region
            Image_Region object.
        Image_Region_position : STR, optional
            Location where the Image_Region will be drawn, which can be at the center
            or at the original Image_Region location. The default is "center".
        context_position : STR, optional
            Where the original image will be drawn relative to the Image_Region.
            The default is "right".
        draw_roi : BOOL, optional
            Draw a bounding box around the Image_Region in the original image.
            The default is True.

        Returns
        -------
        result : TYPE
            DESCRIPTION.

        """
        # Get the original image dimension
        width, height = image.size

        Image_Region_image = image_region.extract_from_image(image)
        
        if draw_roi:
            image = ROI(image, image_region).draw_region_outline(line_width=5).image
            
        # Ensure both images are in RGBA mode for compatibility
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        if Image_Region_image.mode != 'RGBA':
            Image_Region_image = Image_Region_image.convert('RGBA')

            
        # Create new image
        if context_position in ["left", "right"]:
            final_height = height
            final_width = 2 * width
        elif context_position in ["top", "bottom"]:
            final_width = width
            final_height = 2 * height
        
        result = Image.new('RGBA', (final_width, final_height))
        
        # generate Image_Region location
        paste_x0 = image_region._x0
        paste_y0 = image_region._y0
        if Image_Region_position == "center":
            center_x = width // 2
            center_y = height // 2
            
            paste_x0 = int(center_x - image_region._width / 2)
            paste_y0 = int(center_y - image_region._height/ 2)
        
        if context_position == "left":
            paste_x0 += width
        if context_position == "top":
            paste_y0 += height
            
        # Paste in original image
        if context_position == "left" or context_position == "top":
            result.paste(image, (0, 0))
        elif context_position == "right":
            result.paste(image, (width, 0))
        elif context_position == "bottom":
            result.paste(image, (0, height))
            
            
        # Paste Image_Region
        result.paste(Image_Region_image, (paste_x0, paste_y0))
        
        return result
        
        
        