# -*- coding: utf-8 -*-


from ..image_region import ImageRegion
from ..image_region_list import ImageRegionList
import copy


class FixedGrid:
    
    N_ROWS = 2
    N_COLS = 2
    STRICT_DIMENSIONS = True
    
    def __init__(self, image, n_rows = 2, n_cols = 2, strict_dimensions = False):
        """
        Initialize a new FixedGrid object

        Parameters
        ----------
        image : PIL Image
            DESCRIPTION.
        n_cols : int, optional
            DESCRIPTION. The default is 2.
        n_rows : int, optional
            DESCRIPTION. The default is 2.
        strict_dimensions : bool, optional
            DESCRIPTION. The default is True.

        Returns
        -------
        None.

        """
        FixedGrid.validate_dimensions(image, n_rows, n_cols, strict_dimensions)
        
        self._image = image
        self._n_rows = n_rows
        self._n_cols = n_cols
        
        self._image_regions = FixedGrid.calculate_image_region_coordinates(image, n_rows, n_cols)
        
    
    @property
    def image_regions(self):
        sorted_list = sorted(self._image_regions, key = lambda image_region : image_region._grid['row'])
        return ImageRegionList(sorted_list)
    
    def get_image_region(self, region_index):
        assert region_index < len(self._image_regions), "Region index out of bounds"
        
        return self._image_regions[region_index]
    

    @staticmethod
    def generate(image, n_cols = None, n_rows = None):
        """
        Provides an Image_Region object by decomposing the image in Image_Region
        using the idea of subdivision (the image is divided in HORIZONTAL_PARTS
        along the horizontal dimension and VERTICAL_PARTS along the vertical
        dimension)

        Parameters
        ----------
        image : PIL Image
            PIL Image Object
        n_cols : int
            The number of columns in the image grid
        n_rows : int
            The number of rows in the image grid. Defaults to

        Returns
        -------
        Image_Region collection.

        """
        
        FixedGrid.validate_dimensions(image, n_rows, n_cols)
        
        image_regions = FixedGrid.calculate_image_region_coordinates(image, n_rows, n_cols)
        
        return ImageRegionList(image_regions)

        
    @staticmethod
    def validate_dimensions(image, target_rows, target_columns, strict_dimensions = True):
        """
        Checks if the dimensions of the image are consistent with the 
        HORIZONTAL_PARTS and VERTICAL_PARTS of the Fixed_Grid class

        Parameters
        ----------
        image : PIL Image
            The image for which to check the dimensions.

        Returns
        -------
        None.

        """
        if strict_dimensions:
            assert image.width % target_rows == 0, "Image width needs to be a multiple of %d (currently %d)"%(target_rows, image.width)
            assert image.height % target_columns == 0, "Image height needs to be a multiple of %d (currently %d)"%(target_columns, image.height)
            
        
    @staticmethod
    def calculate_image_region_coordinates(image, n_rows, n_cols):
        """
        Calculates the top left locations and the dimensions for each Image_Region
        when it is split in the configured number of HORIZONTAL_PARTS and 
        VERTICAL_PARTS

        Parameters
        ----------
        image : PIL Image
            A PIL Image object.

        Returns
        -------
        A list with dictionaries with Image_Region data (x, y, width and height)

        """
        # Calculate the Image_Region width and height based on the required number of subdivions
        target_width = image.width//n_cols
        target_height = image.height//n_rows
        
        image_regions = []
        for x in range(n_cols):
            for y in range(n_rows):
                # Calculate the top left corner position of the Image_Region
                x_0 = x * target_width
                y_0 = y * target_height
                
                # Calculate the actual Image_Region width and height, constrained by the actual image size
                region_width = image.width - x_0 if x_0 + target_width > image.width else target_width
                region_height = image.height - y_0 if y_0 + target_height > image.height else target_height
                
                # Create new Image_Region
                image_region = ImageRegion(x_0, y_0, region_width, region_height)
                
                image_region._grid = {
                    "row": y,
                    "col": x,
                    "x": x_0,
                    "y": y_0
                }

                image_regions.append(image_region)
                
                
        return image_regions