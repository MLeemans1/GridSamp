# -*- coding: utf-8 -*-

from ..image_region import ImageRegion
from ..image_region_list import ImageRegionList
import copy


class SpacedGrid:
    """
    Generates a grid of equally spaced image regions around 
    a central point, with optional padding for each region.

    Attributes
    ----------
    _image : object
        An image-like object with `.width` and `.height` attributes.
    _x_center : int
        The x-coordinate of the central grid point.
    _y_center : int
        The y-coordinate of the central grid point.
    _x_spacing : int
        Horizontal spacing between the centers of adjacent grid cells.
    _y_spacing : int
        Vertical spacing between the centers of adjacent grid cells.
    _x_padding : int
        Horizontal padding added to each region’s width.
    _y_padding : int
        Vertical padding added to each region’s height.
    _grid_width : int
        Width of the image (derived from `image.width`).
    _grid_height : int
        Height of the image (derived from `image.height`).
    _image_regions : list of ImageRegion
        List of generated image regions in the grid.

    Methods
    -------
    image_regions : ImageRegionList
        Returns an ImageRegionList of the generated grid cells, sorted by row.
    generate_spaced_points(total_size, starting_point, spacing) -> list[int]
        Generates a list of coordinates spaced evenly from a starting point 
        until the edges of the image are reached.
    """
    def __init__(self, image, x_center, y_center, x_spacing, y_spacing, x_padding, y_padding):
        """
        Initializes the SpacedGrid and generates the image regions.

        Parameters
        ----------
        image : object
            An object with `.width` and `.height` attributes (e.g., PIL Image).
        x_center : int
            X-coordinate of the central grid point.
        y_center : int
            Y-coordinate of the central grid point.
        x_spacing : int
            Horizontal distance between centers of adjacent grid cells.
        y_spacing : int
            Vertical distance between centers of adjacent grid cells.
        x_padding : int
            Extra pixels added to each side horizontally.
        y_padding : int
            Extra pixels added to each side vertically.
        """
        self._image = image
        self._x_center = x_center
        self._y_center = y_center
        self._x_spacing = x_spacing
        self._y_spacing = y_spacing
        self._x_padding = x_padding
        self._y_padding = y_padding
        
        self._grid_width  = image.width
        self._grid_height = image.height
        
        self._generate_image_regions()
        
    def _generate_image_regions(self):
        """
        Internal method to generate ImageRegion objects 
        based on the spacing, center, and padding parameters.

        Each region's width and height are determined as:
            width  = 0.5 * x_spacing + (2 * x_padding)
            height = 0.5 * y_spacing + (2 * y_padding)

        The method uses `generate_spaced_points` to determine
        the center positions of all rows and columns, then creates
        ImageRegion objects for each grid cell.

        Notes
        -----
        - This method modifies `self._image_regions` in place.
        - The generated ImageRegion objects are annotated with 
          grid row/column indices and their center coordinates.
        """
        self._image_regions = []
        
        x_centers = SpacedGrid.generate_spaced_points(self._grid_width, self._x_center, self._x_spacing)
        y_centers = SpacedGrid.generate_spaced_points(self._grid_height, self._y_center, self._y_spacing)
        
        for col_index, x in enumerate(x_centers):
            for row_index, y in enumerate(y_centers):
                width  =  int(0.5 * self._x_spacing) + (2 * self._x_padding)
                height =  int(0.5 * self._y_spacing) + (2 * self._y_padding)
                
                print(x, y, width, height)
                
                new_region = ImageRegion(x, y, width, height)
                new_region.set_grid_data(row_index + 1, col_index + 1)
                new_region._grid['x'] = x
                new_region._grid['y'] = y
                self._image_regions.append(new_region)
    
    @property
    def image_regions(self):
        """
        Returns the generated image regions sorted by their row number.

        Returns
        -------
        ImageRegionList
            A list-like container of ImageRegion objects, sorted in 
            top-to-bottom order by row index.
        """
        sorted_list = sorted(self._image_regions, key = lambda image_region : image_region._grid['row'])
        return ImageRegionList(sorted_list)
    
    @staticmethod
    def generate_spaced_points(total_size, starting_point, spacing):
        """
        Generates evenly spaced coordinates along one dimension,
        starting from a given central point and extending toward 
        both edges of the dimension.

        Parameters
        ----------
        total_size : int
            The size of the dimension (e.g., image width or height).
        starting_point : int
            The coordinate of the first central point.
        spacing : int
            The distance between consecutive points.

        Returns
        -------
        list[int]
            A list of coordinates for grid centers, starting from the 
            smallest coordinate (closest to 0) to the largest coordinate 
            (closest to total_size - 1).

        Notes
        -----
        - The first element is `starting_point`.
        - The method fills coordinates in both directions from the 
          starting point until the edges are reached.
        """
        spaced_points = [starting_point]
        
        current_point = starting_point
        while current_point > 0:
            current_point -= spacing
            
            if current_point < 0:
                current_point = 0
                
            spaced_points.insert(0, current_point)
        
        current_point = starting_point
        while current_point < (total_size - 1):
            current_point += spacing
            
            if current_point > (total_size - 1):
                current_point = total_size - 1
                
            spaced_points.append(current_point)
            
        return spaced_points