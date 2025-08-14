from ..image_region import ImageRegion
from ..image_region_list import ImageRegionList

class RecursiveGrid:
    
    def __init__(self, image, recursion_depth):
        self._recursion_depth = recursion_depth
        self._tree = {}

        # If input is a PIL.Image object, wrap it into an ImageRegion
        if isinstance(image, ImageRegion):
            self._source_image = image
        else:
            # Assuming the image object has .width and .height
            self._source_image = ImageRegion(0, 0, image.width, image.height)
            self._source_image._grid = {'x': 0, 'y': 0, 'row': 0, 'col': 0, 'depth': 0}
            self._source_image._quadrant = 0

        self._tree['level_1'] = RecursiveGrid.generate(self._source_image)
        for recursion_index in range(2, recursion_depth + 1):
            self._tree[f'level_{recursion_index}'] = []

            for current_level_element in self._tree[f'level_{recursion_index - 1}']:
                self._tree[f'level_{recursion_index}'].extend(RecursiveGrid.generate(current_level_element))

    def get_recursion_level_images(self, recursion_level):
        image_region_list = ImageRegionList(self._tree[f'level_{recursion_level}'])
        sorted_list = sorted(image_region_list, key=lambda image_region: image_region._grid['row'])
        return sorted_list

    @staticmethod
    def generate(image_region):
        width, start_x  = RecursiveGrid.split_length(image_region._width)
        height, start_y = RecursiveGrid.split_length(image_region._height)

        quadrant_1 = ImageRegion(image_region._x0, image_region._y0, width, height)
        quadrant_2 = ImageRegion(image_region._x0 + start_x, image_region._y0, width, height)
        quadrant_3 = ImageRegion(image_region._x0, image_region._y0 + start_y, width, height)
        quadrant_4 = ImageRegion(image_region._x0 + start_x, image_region._y0 + start_y, width, height)

        quadrant_1._quadrant = 1
        quadrant_2._quadrant = 2
        quadrant_3._quadrant = 3
        quadrant_4._quadrant = 4

        src_row = -1
        src_col = -1
        src_depth = 1
        if hasattr(image_region, '_grid'):
            src_row = image_region._grid['row']
            src_col = image_region._grid['col']
            src_depth = image_region._grid['depth']

        quadrant_1._grid = {
            'x': quadrant_1._x0,
            'y': quadrant_1._y0,
            'row': 2 * max(0, src_row) + 0,
            'col': 2 * max(0, src_col) + 0,
            'depth': src_depth + 1
        }

        quadrant_2._grid = {
            'x': quadrant_2._x0,
            'y': quadrant_2._y0,
            'row': 2 * max(0, src_row) + 0,
            'col': 2 * max(0, src_col) + 1,
            'depth': src_depth + 1
        }

        quadrant_3._grid = {
            'x': quadrant_3._x0,
            'y': quadrant_3._y0,
            'row': 2 * max(0, src_row) + 1,
            'col': 2 * max(0, src_col) + 0,
            'depth': src_depth + 1
        }

        quadrant_4._grid = {
            'x': quadrant_4._x0,
            'y': quadrant_4._y0,
            'row': 2 * max(0, src_row) + 1,
            'col': 2 * max(0, src_col) + 1,
            'depth': src_depth + 1
        }

        return [quadrant_1, quadrant_2, quadrant_3, quadrant_4]

    @staticmethod
    def split_length(length):
        """
        For a dimension of 'length' pixels, calculates the width and the starting point
        of the second part when the dimension is split in two.
                
        In the case of even dimensions this works out in two equal sized
        non-overlapping parts
                
        In the case of uneven dimensions, the midlle pixel overlaps in each part.

        Parameters
        ----------
        length : INT
            Number of pixels 

        Returns
        -------
        width : TYPE
            DESCRIPTION.
        start : TYPE
            DESCRIPTION.
        """
        if length % 2 == 0:
            width = length // 2
            start_2 = width
        else:
            width = (length + 1) // 2
            start_2 = width - 1
        return width, start_2
