# GridSamp (beta)
The official PIL Implementation of GridSamp: A common environment for grid-based image sampling using intuitive python code.

## Overview
The GridSamp Python toolbox was created by Leemans, Bossens, and Wagemans (manuscript in preparation) as a tool for grid-based image sampling. It was created in Python 3.8 and is dependent on the following Python libraries: Pillow, numpy, scipy, and skimage. We thank the developers of each of these libraries and the Python programming language.

## Install
```
pip install https://github.com/MLeemans1/GridSamp.git
```
or 
```
# clone the repo
git clone https://github.com/MLeemans1/GridSamp.git
cd grid_samp

# install locally
pip install -e .
```

## Usage 
A simple example:
```
# Open grid_samp toolbox
from grid_samp import ImageRegion, ImageRegionList
from grid_samp.grids import FixedGrid, RecursiveGrid, ImageRegionBasedGrid
from grid_samp.assemble import ROI, ImageRegionIntersectionHeatmap, Mosaic, Contextualize

# Load example image
image = Image.open('example img.jpg')

# Initialize grid
fixed_grid = FixedGrid(image = image_1, n_rows = 4, n_cols = 5)

# Access and manipulate image regions
region_list = fixed_grid.image_regions
swapped_regions = region_list.swap(region_1_index = 10, region_2_index = 14)

# Extract result
swapped_regions_mosaic_1 = Mosaic.generate(image_1, swapped_regions)
```

## Development Status
This is a beta release; expect API changes.
Contributions and feedback are welcome!

## Cite GridSamp
Leemans, M., Bossens, C., & Wagemans, J. (in preparation). GridSamp: An open source python toolbox for grid-based image sampling.


## Contact
maarten.leemans@kuleuven.be - Maarten Leemans, Maintainer
