import copy
import random

class ImageRegionList:
    """
    A class representing a collection of image regions, with options to 
    manipulate the image regions
    """
    
    def __init__(self, image_regions):
        """
        Class constructor

        Parameters
        ----------
        image_regions : list
            A list with ImageRegion objects.

        Returns
        -------
        None.

        """
        self._image_regions = image_regions
        
    def __len__(self):
        """
        Return the number of image regions in the image region list

        """
        return len(self._image_regions)
    
    def __iter__(self):
        """
        Iterator that produces individual ImageRegion objects
        """
        return iter(self._image_regions)
    
    def __getitem__(self, key):
        return self._image_regions[key]
    
    @property
    def image_regions(self):
        """
        Returns the underlying list of ImageRegion objects
        """
        return self._image_regions
        
    def get(self, image_region_index):
        """
        Returns an ImageRegion from the ImageRegionList

        Parameters
        ----------
        image_region_index : int
            Index of the ImageRegion in the ImageRegionList.

        Returns
        -------
        ImageRegion
            A copy of the ImageRegion object.

        """
        return copy.deepcopy(self._image_regions[image_region_index])
        
    def replace(self, original_region_index, new_image_region):
        """
        Returns a copy of the ImageRegionList, in which an image region
        has been replaced with a new image region

        Parameters
        ----------
        original_region_index : int
            Location in the ImageRegionList of the element that will be replaced.
        new_image_region : ImageRegion
            ImageRegion that will be replaced at the provided index.

        Returns
        -------
        ImageRegionList
            A copy of the new ImageRegionList.

        """
        image_region_list = copy.deepcopy(self._image_regions)
        
        if hasattr(image_region_list[original_region_index], '_grid'):
            new_image_region._grid = image_region_list[original_region_index]._grid
        image_region_list[original_region_index] = new_image_region
        
        return ImageRegionList(image_region_list)
        
    def swap(self, region_1_index, region_2_index):
        """
        Returns a copy of the ImageRegionList in which two ImageRegions have
        been swapped

        Parameters
        ----------
        region_1_index : int
            Location of the first image region.
        region_2_index : int
            Location of the second image region.

        Returns
        -------
        ImageRegionList
            A copy of the ImageRegionList in which two regions have been 
            swapped.

        """
        # Create copy for new image region list
        image_regions = copy.deepcopy(self._image_regions)
        
        # Copy the image regions
        region_1_grid = copy.deepcopy(image_regions[region_1_index]._grid)
        region_2_grid = copy.deepcopy(image_regions[region_2_index]._grid)
        
        # Swap the grid properties
        image_regions[region_2_index]._grid = region_1_grid
        image_regions[region_1_index]._grid = region_2_grid
        
        # Return the result
        return ImageRegionList(image_regions)
        
    def shuffle(self, pass_region=None, fix_unit=None):
        regions = copy.deepcopy(self._image_regions)
    
        # Normalize input: convert a single region to a list
        if pass_region is None:
            pass_region = []
            
        elif not isinstance(pass_region, list):
            pass_region = [pass_region]
    
        # Identify indices of regions to exclude
        exclude_indices = []
        for region in pass_region:
            if isinstance(region, int):
                exclude_indices.append(region)
            else:
                for i, r in enumerate(self._image_regions):
                    if r._grid == region._grid:
                        exclude_indices.append(i)
                        break
    
        # Shuffle everything
        print("Ecluding these indices: ",exclude_indices)
        if fix_unit is None:
            all_indices = list(range(len(regions)))
            indices_to_shuffle = [i for i in all_indices if i not in exclude_indices]
            shuffled_indices = indices_to_shuffle.copy()
            random.shuffle(shuffled_indices)
    
            for target_idx, source_idx in zip(indices_to_shuffle, shuffled_indices):
                regions[target_idx]._grid = copy.deepcopy(self._image_regions[source_idx]._grid)
    
        # Shuffle rows
        if fix_unit == 'rows':
            original_row_indices = self._get_grid_row_indices()
            shuffled_row_indices = original_row_indices.copy()
            random.shuffle(shuffled_row_indices)
            grid_row_swaps = {
                orig[0]: new for orig, new in zip(original_row_indices, shuffled_row_indices)
            }
            print("Grid row swaps: ", grid_row_swaps)
    
            for i, image_region in enumerate(regions):
                if i in exclude_indices:
                    continue
                new_grid_location = grid_row_swaps[image_region._grid['row']]
                image_region._grid['row'] = new_grid_location[0]
                image_region._grid['y'] = new_grid_location[1]
                
        # Shuffle columns
        if fix_unit == 'columns':
            original_column_indices = self._get_grid_column_indices()
            shuffled_column_indices = original_column_indices.copy()
            random.shuffle(shuffled_column_indices)
            grid_column_swaps = {
                orig[0]: new for orig, new in zip(original_column_indices, shuffled_column_indices)
            }
            print("Grid row swaps: ", grid_column_swaps)
    
            for i, image_region in enumerate(regions):
                if i in exclude_indices:
                    continue
                new_grid_location = grid_column_swaps[image_region._grid['col']]
                image_region._grid['col'] = new_grid_location[0]
                image_region._grid['x'] = new_grid_location[1]
                
        if fix_unit == "edges":
            all_indices = list(range(len(regions)))
            exclude_indices = self._get_grid_edge_indices()
            indices_to_shuffle = [i for i in all_indices if i not in exclude_indices]
            shuffled_indices = indices_to_shuffle.copy()
            random.shuffle(shuffled_indices)
    
            for target_idx, source_idx in zip(indices_to_shuffle, shuffled_indices):
                regions[target_idx]._grid = copy.deepcopy(self._image_regions[source_idx]._grid)
    
        return ImageRegionList(regions)

    
    def shuffle_within_columns(self):
        return self.shuffle_within_unit('col')

    def shuffle_within_size(self):
        size_groups = {}
        
        # 1. Create groups with equally sized image regions
        for idx, image_region in enumerate(self._image_regions):
            size = (image_region._width, image_region._height)
            
            if not size in size_groups:
                size_groups[size] = [idx]
            else:
                size_groups[size].append(idx)
        
        print(size_groups)
        
        # 2. Shuffle within size groups
        regions = copy.deepcopy(self._image_regions)
        
        for size in size_groups:
            original_indices = size_groups[size]
            shuffled_indices = original_indices.copy()
            random.shuffle(shuffled_indices)
            
            for target_idx, source_idx in zip(original_indices, shuffled_indices):
                regions[target_idx]._grid = copy.deepcopy(self._image_regions[source_idx]._grid)
                
        return ImageRegionList(regions)
        
    
    def shuffle_within_unit(self, unit):
        regions = copy.deepcopy(self._image_regions)
        rows = {}
    
        for idx, region in enumerate(regions):
            row_id = region._grid[unit]
            if row_id not in rows:
                rows[row_id] = []
            rows[row_id].append(idx)
                   
        for row_index in rows:
            row_indices = rows[row_index]
            shuffled_row_indices = copy.deepcopy(row_indices)
            random.shuffle(shuffled_row_indices)
            
            
            for target_idx, source_idx in zip(row_indices, shuffled_row_indices):
                print(target_idx, source_idx)
                regions[target_idx]._grid = copy.deepcopy(self._image_regions[source_idx]._grid)
                       
        return ImageRegionList(regions)
    
    def shuffle_within_rows(self):
        return self.shuffle_within_unit('row')

    
    def _get_grid_row_indices(self):
        """
        Creates a list with all occuring grid row indices ('row') and their
        corresponding position ('y') in the image

        Returns
        -------
        List
            List of tuples: (row_index, y).

        """
        row_indices = []
        for image_region in self._image_regions:
            row_indices.append((image_region._grid['row'], image_region._grid['y']))
        
        return list(set(row_indices))
            
    def _get_grid_column_indices(self):
        """
        Creates a list with all occuring grid column indices ('col') and their
        corresponding position ('x') in the image

        Returns
        -------
        List
            List of tuples: (row_index, y).

        """
        col_indices = []
        for image_region in self._image_regions:
            col_indices.append((image_region._grid['col'], image_region._grid['x']))
            
        return list(set(col_indices))

    
    def _get_grid_edge_indices(self):
        """
        Get the indices of image regions in the list that occur on the edge,
        defined as either the first or last column, or the first or last row

        Returns
        -------
        edge_indices : List
            A list with indices of ImageRegions that fall on the egde of 
            the grid.

        """
        rows = [r._grid['row'] for r in self._image_regions]
        cols = [r._grid['col'] for r in self._image_regions]
    
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)
    
        edge_indices = []
        for idx, region in enumerate(self._image_regions):
            r, c = region._grid['row'], region._grid['col']
            if r in (min_row, max_row) or c in (min_col, max_col):
                edge_indices.append(idx)
                
        return edge_indices