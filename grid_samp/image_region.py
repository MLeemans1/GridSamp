from PIL import Image, ImageFilter, ImageDraw
import random
import numpy as np
import copy



from scipy.fft import fft2, ifft2, fftshift, ifftshift
from skimage.exposure import match_histograms


class ImageRegion:
    def __init__(self, x0, y0, width, height, image = None):
        """
        Parameters
        ----------
        x0 : INT
            top-left x-coordinate.
        y0 : INT
            top-left y-coordinate.
        width : TYPE
            DESCRIPTION.
        height : TYPE
            DESCRIPTION.
        image : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        self._x0 = x0
        self._y0 = y0
        self._width = width
        self._height = height
        self._image = image
        
        self._frequency_filter = None
        self._blur     = False
        self._invert_y = False
        self._invert_x = False
        self._transparency = None
        self._greyscale = False
        self._saturation = 1.0
        self._pixel_scramble = False
        self._mask = None
        self._contrast_match_to = None

        
    def __repr__(self):
        return "ImageRegion Object"
    
    @property
    def mode(self):
        if self._image is not None:
            return self._image.mode
        else:
            return None
        
    def copy(self):
        return copy.deepcopy(self)

    def set_box(self, box):
        self._top_left = (box[0], box[1])
        self._bottom_right = (box[2], box[3])
    
    def get_center(self):
        """
        Returns the center of the ImageRegion. For even dimensions, the center
        is counted as one-half of the way from the origin
        
        Returns
        -------
        A tuple with the center coordinates for the ImageRegion
        
        """
        half_width  = ImageRegion._calculate_center_pixel(self._width)
        half_height = ImageRegion._calculate_center_pixel(self._height)
        
        x_center = self._x0 + half_width
        y_center = self._y0 + half_height
        
        return (x_center, y_center)
    
    def set_image(self, image):
        self._image = image
        
    def get_image(self):
        """
        Returns
        -------
        PIL.Image.Image or None
            The cropped image for this region.
        """
        return self._image
        
    def set_region_dimensions_to_proportions(self, scale_factor):
        """
        Returns a new ImageRegion by scaling the dimensions of the current ImageRegion 
        according to the scale factor, rounded to the nearest integer.
        
        The scaled ImageRegion has the same center as the original ImageRegion.

        Parameters
        ----------
        scale_factor : number or list with two elements
            When a single number is provided, this will scale both dimensions.
            When two numbers are provided, the scaling will be applied to
            the width and height respectively

        Returns
        -------
        ImageRegion.

        """
        if isinstance(scale_factor, int) or isinstance(scale_factor, float):
            scale_factor = [scale_factor, scale_factor]
        
        assert (isinstance(scale_factor, list) or isinstance(scale_factor, tuple)) and len(scale_factor) == 2, "scale factor must be a single number or a list with two numbers"
        
        # Calculate the updated dimensions
        new_width  = int(self._width * scale_factor[0])
        new_height = int(self._height * scale_factor[1])
        
        # Calculate updated origin point centered on current ImageRegion
        new_half_width  = ImageRegion._calculate_center_pixel(new_width)
        new_half_height = ImageRegion._calculate_center_pixel(new_height)
        
        x0 = self.get_center()[0] - new_half_width
        y0 = self.get_center()[1] - new_half_height
        
        # Create and return new ImageRegion
        return ImageRegion(x0, y0, new_width, new_height)
    
    def set_region_dimensions_to_pixels(self, pixel_dims):
        """
        Create a new ImageRegion cropped to a specific pixel width and height,
        centered on the current region.
    
        Parameters
        ----------
        pixel_dims : int, float, or list/tuple of two values
            Desired dimensions of the cropped region in pixels.
            - If a single number, both width and height will use this value.
            - If a list or tuple, should be [width, height].
    
        Returns
        -------
        ImageRegion
            New ImageRegion centered on the original, with given pixel dimensions.
        """
        if isinstance(pixel_dims, (int, float)):
            pixel_dims = [pixel_dims, pixel_dims]
    
        assert isinstance(pixel_dims, (list, tuple)) and len(pixel_dims) == 2, \
            "pixel_dims must be a single number or a list/tuple with two numbers"
    
        new_width = int(pixel_dims[0])
        new_height = int(pixel_dims[1])
    
        # Calculate new top-left corner based on center of current region
        center_x, center_y = self.get_center()
        new_half_width = new_width // 2
        new_half_height = new_height // 2
    
        x0 = center_x - new_half_width
        y0 = center_y - new_half_height
    
        return ImageRegion(x0, y0, new_width, new_height)
    
    def extract_from_image(self, image, clip_to_image_boundaries = True):
        """
        Extract the ImageRegion region from the provided image. ImageRegion coordinates
        are constrained to fall within the image boundaries.

        Parameters
        ----------
        image : PIL image object
            Image from which to extract the ImageRegion region.

        Returns
        -------
        PIL Image
            The ImageRegion extracted from the image.

        """
        if self._frequency_filter:
            image = self._filter_frequency_pass(
                self._frequency_filter["range"],
                self._frequency_filter["cutoff"],
                self._frequency_filter.get("ppd", 30)
                )
        
        # Extract bounding box
        bounding_box = self.get_bounding_box()
        left_bb, top_bb, right_bb, bottom_bb = bounding_box
        width_bb = right_bb - left_bb
        height_bb = bottom_bb - top_bb
    
        # Determine cropped area within image bounds
        crop_left = max(left_bb, 0)
        crop_top = max(top_bb, 0)
        crop_right = min(right_bb, image.width)
        crop_bottom = min(bottom_bb, image.height)
    
        if clip_to_image_boundaries:
            if crop_left != left_bb:
                print(f"WARNING: Left coordinate adjusted from {left_bb} to {crop_left} to stay within image bounds.")
            if crop_top != top_bb:
                print(f"WARNING: Top coordinate adjusted from {top_bb} to {crop_top} to stay within image bounds.")
            if crop_right != right_bb:
                print(f"WARNING: Right coordinate adjusted from {right_bb} to {crop_right} to stay within image bounds.")
            if crop_bottom != bottom_bb:
                print(f"WARNING: Bottom coordinate adjusted from {bottom_bb} to {crop_bottom} to stay within image bounds.")
    
            # Crop and return without transparency padding
            result = image.crop((crop_left, crop_top, crop_right, crop_bottom))
    
        else:
            # Crop the portion within the image bounds
            cropped = image.crop((crop_left, crop_top, crop_right, crop_bottom)).convert("RGBA")
    
            # Create a transparent image the size of the full bounding box
            result = Image.new("RGBA", (width_bb, height_bb), (0, 0, 0, 0))
    
            # Paste the cropped region at the correct offset
            paste_x = crop_left - left_bb
            paste_y = crop_top - top_bb
            result.paste(cropped, (paste_x, paste_y))
        
        # Perform post processing
        if self._blur:
            result = result.filter(ImageFilter.GaussianBlur(radius = self._blur_radius))
        
        if self._invert_x:
            result = result.transpose(Image.FLIP_LEFT_RIGHT)
            
        if self._invert_y:
            result = result.transpose(Image.FLIP_TOP_BOTTOM)
            
        if self._transparency is not None:
            result = self._apply_transparency(result)
            
        if self._greyscale:
            result = result.convert("L")
            
        if self._saturation != 1.0:
            result = self._adjust_saturation_hsv(result, self._saturation)
            
        if self._pixel_scramble:
            result = self._apply_pixel_scramble(result)
            
        if self._mask is not None:
            # Check mask dimensions match cropped region
            mask_width, mask_height = result.size
            if self._mask.size != (mask_width, mask_height):
                print(f"INFO: Regenerating mask to match clipped region of size {result.size}")
                if hasattr(self, '_generate_oval_mask'):
                    self._mask = self._generate_oval_mask(width=mask_width, height=mask_height)
                else:
                    raise ValueError("Mask and region size mismatch, and no method to regenerate mask.")
            result.putalpha(self._mask)

        if self._contrast_match_to is not None:
            result = self._apply_contrast_match(result)
            
        # Return the result
        return result
    
    def top_left(self):
        """
        Returns the top-left coordinate of the ImageRegion.
        
        Returns
        -------
        tuple
            (x0, y0) coordinate of the top-left corner.
        """
        return (self._x0, self._y0)
    
    def top_right(self):
        """
        Returns the top-right coordinate of the ImageRegion.
        
        Returns
        -------
        tuple
            (x1, y0) coordinate of the top-right corner.
        """
        return (self._x0 + self._width, self._y0)
    
    def bottom_left(self):
        """
        Returns the bottom-left coordinate of the ImageRegion.
        
        Returns
        -------
        tuple
            (x0, y1) coordinate of the bottom-left corner.
        """
        return (self._x0, self._y0 + self._height)
    
    def bottom_right(self):
        """
        Returns the bottom-right coordinate of the ImageRegion.
        
        Returns
        -------
        tuple
            (x1, y1) coordinate of the bottom-right corner.
        """
        return (self._x0 + self._width, self._y0 + self._height)
    
    def decompose(self, decomposition):
        """
        Returns the ImageRegion parameters as a tuple.
        
        Returns
        -------
        tuple
            (x0, y0, width, height)
        """
        return decomposition.generate(self)
    
    def get_corners(self):
        """
        Returns all four corner coordinates of the ImageRegion.
        
        Returns
        -------
        dict
            Dictionary containing 'top_left', 'top_right', 'bottom_left', and 'bottom_right' keys.
        """
        return (self.top_left(), self.top_right(), self.bottom_left(), self.bottom_right())
    
    def get_bounding_box(self):
        """
        Compute the bounding box of the ImageRegion.
        
        Returns
        -------
        tuple
            (left, top, right, bottom) coordinates of the ImageRegion bounding box.
        """
        return (self._x0, self._y0, self._x0 + self._width, self._y0 + self._height)
    
    def set_grid_data(self, row, column):
        """
        Sets the ImageRegion attributes based on grid data.
        
        Parameters
        ----------
        x0 : int
            The x-coordinate of the top-left corner.
        y0 : int
            The y-coordinate of the top-left corner.
        width : int
            The width of the ImageRegion.
        height : int
            The height of the ImageRegion.
        """
        self._grid = {
            'row' : row,
            'col' : column}
        
    def set_mask(self, mask_type, **kwargs):
        """
        Adds a mask when the ImageRegion is extracted from the image.
    
        Parameters
        ----------
        mask_type : int / Image / None
            For integers, the following options are available:
                1: Circular mask
                2: Gaussian mask
            
            If an image is provided, it will be set as the mask.
            
        **kwargs : additional parameters
            sigma: can be used to configure the width of the gaussian mask.
    
        Returns
        -------
        self : ImageRegion
            Returns the modified instance for chaining.
        """
        if mask_type == 1:
            self._mask = self._generate_oval_mask()
        elif mask_type == 2:
            sigma = kwargs.get('sigma', (self._width**2 + self._height**2)**0.5)
            self._mask = self._generate_gaussian_mask(sigma)
        elif isinstance(mask_type, Image.Image):
            assert mask_type.width == self._width and mask_type.height == self._height, 'Mask size does not match region size'
            self._mask = mask_type
        elif mask_type is None:
            self._mask = None
    
        return self

    def _generate_oval_mask(self, width=None, height=None):
        width = width or self._width
        height = height or self._height
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), (width, height)], fill=255)
        
        return mask

    def _generate_gaussian_mask(self, sigma, width=None, height=None):
    
        width = width or self._width
        height = height or self._height
    
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        x, y = np.meshgrid(x, y)
        d = np.sqrt(x*x + y*y)
        g = np.exp(-(d**2) / (2 * sigma**2))
        g = (g / g.max() * 255).astype(np.uint8)
        
        return Image.fromarray(g, mode='L')

       
    def blur(self, status=True, radius=5):
        """
        Enable or disable Gaussian blur for the ImageRegion.
        
        Parameters
        ----------
        status : bool, optional
            If True, the ImageRegion will be blurred. Default is True.
        radius : int, optional
            The blur radius. Default is 5.
        """
        self._blur = status
        self._blur_radius = radius
        
    def invert(self, invert_x = True, invert_y = True):
        """
        Invert the ImageRegion along the x and/or y axis.
        
        Parameters
        ----------
        invert_x : bool, optional
            If True, the ImageRegion will be flipped horizontally. Default is True.
        invert_y : bool, optional
            If True, the ImageRegion will be flipped vertically. Default is True.
        """
        self._invert_x = invert_x
        self._invert_y = invert_y
        
    def set_transparency(self, transparency_level=1.0):
        """
        Set the transparency of the extracted region.
        
        Parameters
        ----------
        transparency_level : float
            A value between 0 (fully transparent) and 1 (fully opaque).
        """
        self._transparency = transparency_level
        
    def _apply_transparency(self, image):
        """
        Apply transparency to the image based on the transparency level.
        """
        image = image.convert("RGBA")
        alpha = image.split()[3]  # Get the alpha channel
        
        # Create a new alpha channel with adjusted transparency
        new_alpha = alpha.point(lambda p: p * self._transparency)
        
        # Replace the alpha channel in the image
        image.putalpha(new_alpha)
        
        return image
    
    def grey_scale(self, status=True):
        """
        Set whether the extracted ImageRegion should be converted to grayscale.
    
        Parameters
        ----------
        status : bool, optional
            If True, the ImageRegion will be converted to grayscale upon extraction. 
            Default is True.
        """
        self._greyscale = status
        
    def set_saturation(self, status=1.0):
        """
        Set the saturation factor. 1.0 means no change, 0.0 means grayscale,
        and >1.0 increases saturation.
        
        Parameters
        ----------
        status : float
            Saturation factor to apply to the ImageRegion. Default is 1.0.
        """
        self._saturation = status
        
    def _adjust_saturation_hsv(self, image, factor):
        """
        Adjusts the saturation of an image using the HSV color space.
    
        Parameters
        ----------
        image : PIL.Image
            Input image in RGB mode.
        factor : float
            Saturation adjustment factor (0 = grayscale, 1 = original, >1 = increased saturation).
    
        Returns
        -------
        PIL.Image
            Image with adjusted saturation.
        """
        # Convert image to HSV
        hsv_image = image.convert("HSV")
        
        # Split the image into H, S, V channels
        h, s, v = hsv_image.split()
        
        # Adjust the saturation (S) channel by multiplying with the factor
        s = s.point(lambda p: min(255, max(0, p * factor)))  # Ensure values are within 0-255
        
        # Merge the channels back into the HSV image
        hsv_image = Image.merge("HSV", (h, s, v))
        
        # Convert back to RGB
        rgb_image = hsv_image.convert("RGB")
        
        return rgb_image
    
    def pixel_scramble(self, status=True):
        """
        Enable or disable pixel scrambling.
        
        Parameters
        ----------
        status : bool
            If True, the pixels will be scrambled. Default is True.
        """
        self._pixel_scramble = status
    
    def _apply_pixel_scramble(self, image):
        """
        Randomly shuffles pixels in the image (pixel scrambling).
        
        Parameters
        ----------
        image : PIL.Image
            The input image to be scrambled.
        
        Returns
        -------
        PIL.Image
            Scrambled image with pixels randomly rearranged.
        """
        # Ensure image is in RGBA to preserve alpha channel if needed
        image = image.convert("RGBA")
        array = np.array(image)
        
        # Flatten the image array to a 2D array of shape (num_pixels, 4)
        h, w, c = array.shape
        flat = array.reshape((-1, c))
        
        # Shuffle pixel rows
        np.random.shuffle(flat)
        
        # Reshape back to the original image shape
        scrambled_array = flat.reshape((h, w, c))
        
        # Convert back to a PIL image
        return Image.fromarray(scrambled_array.astype('uint8'), 'RGBA')
    
    def set_frequency_filter(self, frequency_range, cut_off_frequency, pixels_per_degree=30):
        """
        Set frequency filter parameters for this ImageRegion.
        
        Parameters
        ----------
        frequency_range : tuple or list
            Frequency range to apply the filter.
        cut_off_frequency : float
            Cutoff frequency for the filter.
        pixels_per_degree : int, optional
            Pixels per degree parameter, by default 30.
        
        Returns
        -------
        self
            Returns self for method chaining.
        """
        self._frequency_filter = {
            "range": frequency_range,
            "cutoff": cut_off_frequency,
            "ppd": pixels_per_degree
        }

    
    def _filter_frequency_pass(self, frequency_range="low", cut_off_frequency=2.0, pixels_per_degree=30):
        """
        Applies a low-pass or high-pass spatial frequency filter to a PIL image.
        Preserves the input mode (greyscale or RGB).
    
        Parameters
        ----------
        image : PIL.Image
            Input image to filter.
        frequency_range : str
            'low' for low-pass or 'high' for high-pass filtering.
        cut_off_frequency : float
            Cut-off frequency in cycles per degree.
        pixels_per_degree : float
            Number of pixels per visual degree.
    
        Returns
        -------
        PIL.Image
            Filtered image in the same mode as the input.
        """
        assert frequency_range in ("low", "high"), "frequency_range must be 'low' or 'high'"
        
        if self._image.mode == "L":
            # Greyscale image
            img_array = np.array(self._image, dtype=np.float32)
            rows, cols = img_array.shape
            cx, cy = cols // 2, rows // 2
    
            x = np.linspace(-cx, cx, cols)
            y = np.linspace(-cy, cy, rows)
            xv, yv = np.meshgrid(x, y)
            radius = np.sqrt(xv**2 + yv**2)
            freqs = radius / pixels_per_degree
    
            fft_img = fftshift(fft2(img_array))
            mask = freqs <= cut_off_frequency if frequency_range == "low" else freqs >= cut_off_frequency
            fft_img_filtered = fft_img * mask
            img_filtered = np.real(ifft2(ifftshift(fft_img_filtered)))
    
            # Normalize
            img_filtered -= img_filtered.min()
            img_filtered /= img_filtered.max()
            img_filtered = (img_filtered * 255).astype(np.uint8)
            
            return Image.fromarray(img_filtered, mode="L")
    
        elif self._image.mode == "RGB":
            # Color image: process each channel separately
            channels = self._image.split()
            filtered_channels = []
    
            for ch in channels:
                ch_array = np.array(ch, dtype=np.float32)
                rows, cols = ch_array.shape
                cx, cy = cols // 2, rows // 2
    
                x = np.linspace(-cx, cx, cols)
                y = np.linspace(-cy, cy, rows)
                xv, yv = np.meshgrid(x, y)
                radius = np.sqrt(xv**2 + yv**2)
                freqs = radius / pixels_per_degree
    
                fft_ch = fftshift(fft2(ch_array))
                mask = freqs <= cut_off_frequency if frequency_range == "low" else freqs >= cut_off_frequency
                fft_ch_filtered = fft_ch * mask
                ch_filtered = np.real(ifft2(ifftshift(fft_ch_filtered)))
    
                # Normalize
                ch_filtered -= ch_filtered.min()
                ch_filtered /= ch_filtered.max()
                ch_filtered = (ch_filtered * 255).astype(np.uint8)
                filtered_channels.append(Image.fromarray(ch_filtered))
    
            return Image.merge("RGB", filtered_channels)
    
        else:
            raise ValueError(f"Unsupported image mode: {self._image.mode}")
            

    def _apply_contrast_match(self, source_region: Image.Image) -> Image.Image:
        """
        Apply histogram matching to match the contrast of another region.
    
        Parameters
        ----------
        source_region : PIL.Image
            The cropped image region to be modified.
    
        Returns
        -------
        PIL.Image
            The contrast-matched region.
        """
        if self._contrast_match_to is None:
            return source_region
    
        target_region, target_image = self._contrast_match_to
    
        # Get bounding box and crop target region
        bbox = target_region.get_bounding_box()
        target_crop = target_image.crop(bbox)
    
        # Convert both images to numpy arrays
        source_np = np.array(source_region)
        target_np = np.array(target_crop)
    
        # Perform histogram matching
        matched_np = match_histograms(
            source_np, target_np,
            channel_axis=-1 if source_np.ndim == 3 else None
        )
    
        # Convert back to PIL.Image and return
        return Image.fromarray(np.clip(matched_np, 0, 255).astype(np.uint8))

    def set_contrast_match(self, target_region, target_image):
        """
        Sets the target region and image for contrast matching via histogram.
    
        Parameters
        ----------
        target_region : ImageRegion
            The region whose histogram should be matched.
        target_image : PIL.Image
            The image containing the target region.
        """
        self._contrast_match_to = (target_region, target_image)
    
    @staticmethod
    def _calculate_center_pixel(pixels):
        """
        Calculate the location of the center pixel using zero-based positioning,
        and taking the first half way point in case of uneven dimensions

        Parameters
        ----------
        pixels : INT
            Number of pixels

        Returns
        -------
        INT
            Location of the center pixel.

        """
        return pixels // 2 if pixels % 2 == 0 else (pixels - 1) // 2
    
    @staticmethod
    def from_image(image):
        """
        Set up an initial ImageRegion based on the dimensions of the provided image

        Parameters
        ----------
        image : PIL Image
        

        Returns
        -------
        ImageRegion : ImageRegion object
            
        """
        
        image_region = ImageRegion(0, 0, image.width, image.height, image)
        
        return image_region
    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    image_file = r"C:\Users\u0072088\OneDrive - KU Leuven\Documents\03-projects\image-aesthetic-map-toolbox\image-aesethic-map-toolbox\tests\test_image.jpg"
    image = Image.open(image_file)
    
    image_region = ImageRegion.from_image(image)
    scrambled_image = image_region.pixel_scramble(image)
    plt.imshow(scrambled_image)