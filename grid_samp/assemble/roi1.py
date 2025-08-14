from ..image_region import ImageRegion
from .roi_image import ROIImage

class ROI:
    """
    A utility class for generating ROIImage objects for region-based image manipulation.

    This class is used to initialize an ROI-aware image from a base image and a defined
    set of regions of interest (ROIs). These regions can be provided as a single
    `ImageRegion` or an `ImageRegionList`.

    Attributes
    ----------
    text_color : tuple
        Default RGB color used for text annotations (default: black).
    text_box_width : int
        Default width of the background rectangle behind ROI labels.
    text_box_height : int
        Default height of the background rectangle behind ROI labels.
    text_box_color : tuple
        Default RGBA color of the background rectangle for text (semi-opaque light gray).

    Methods
    -------
    generate(image, image_regions)
        Factory method to create an ROIImage from a given image and one or more regions of interest.
    """

    text_color = (0, 0, 0)
    text_box_width = 20
    text_box_height = 20
    text_box_color = (200, 200, 200, 250)

    @staticmethod
    def generate(image, image_regions):
        """
        Create an ROIImage from a PIL image and one or more image regions.

        Parameters
        ----------
        image : PIL.Image
            The input image on which the regions of interest are defined.
        image_regions : ImageRegion or ImageRegionList
            The region(s) of interest. Can be a single `ImageRegion` or an `ImageRegionList`
            (a list-like container of multiple `ImageRegion` objects).

        Returns
        -------
        ROIImage
            An ROIImage object that can be used to apply manipulations to specific image regions.
        """
        if isinstance(image_regions, ImageRegion):
            image_regions = [image_regions]

        return ROIImage(image, image_regions)
