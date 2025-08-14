from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageChops
from ..image_region import ImageRegion
from ..image_region_list import ImageRegionList
from ..grids.fixed_grid import FixedGrid

import matplotlib.pyplot as plt
import numpy as np
from skimage import measure
from scipy import ndimage as ndi
from scipy.ndimage import binary_erosion, distance_transform_edt
from skimage.exposure import match_histograms

class ROI:
    """
    A utility class for generating ROI objects for region-based image manipulation.

    This class is used to initialize a ROI-aware image from a base image and a defined
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
    image : PIL.Image
        The source image to be processed.
    image_regions : list of ImageRegion
        One or more regions of interest defined for the image.
    """

    text_color = (0, 0, 0)
    text_box_width = 20
    text_box_height = 20
    text_box_color = (200, 200, 200, 250)

    def __init__(self, image, image_regions):
        self.image = image.convert("RGB")
        if isinstance(image_regions, (list, ImageRegionList)):
            self.image_regions = list(image_regions)
        else:
            self.image_regions = [image_regions]
        self.mode = None

    def __repr__(self):
        return "ROI Object"

##################
# DRAW FUNCTIONS #
##################
    def draw_region_outline(self, line_color="red", line_width=2, draw_index=False):
        """
        Draw bounding boxes or outlines around image regions following their mask contours.
        Falls back to rectangles when no mask is available.
    
        Parameters
        ----------
        line_color : str
        line_width : int
        draw_index : bool
    
        Returns
        -------
        ROI
        """
        draw = ImageDraw.Draw(self.image)
    
        for idx, region in enumerate(self.image_regions):
            if region._mask is not None:
                self._draw_mask_outline(draw, region, line_color, line_width)
            else:
                self._draw_rectangle(draw, region, line_color, line_width)
    
            if draw_index:
                self._draw_region_index(draw, region, idx)
    
        return self
    
    def _draw_rectangle(self, draw, region, line_color, line_width):
        x0, y0 = region.top_left()
        x1, y1 = region.bottom_right()
        draw.rectangle((x0, y0, x1, y1), outline=line_color, width=line_width)
        
    def _draw_region_index(self, draw, region, idx):
        center = region.get_center()
        font = ImageFont.load_default()
        draw.rectangle(
            ((center[0] - 20, center[1] - 20), (center[0] + 20, center[1] + 20)),
            fill=(200, 200, 200, 125)
        )
        draw.text((center[0] - 10, center[1] - 20), str(idx), fill=(0, 0, 0), font=font)
        
    def _draw_mask_outline(self, draw, region, line_color, line_width):
        x0, y0 = region.top_left()
        mask_array = np.array(region._mask)
        binary_mask = mask_array > 0
    
        padded = np.pad(binary_mask, pad_width=1, mode="constant", constant_values=0)
        contours = measure.find_contours(padded.astype(float), 0.5)
    
        if not contours:
            self._draw_rectangle(draw, region, line_color, line_width)
            return
    
        abs_contours = self._contours_to_image_coords(contours, x0, y0)
        self._draw_contour_lines(draw, abs_contours, line_color, line_width)
        self._connect_contour_endpoints(draw, abs_contours, line_color, line_width)
        
    def _contours_to_image_coords(self, contours, offset_x, offset_y, pad=1):
        abs_contours = []
        for contour in contours:
            pts = [(offset_x + pt[1] - pad, offset_y + pt[0] - pad) for pt in contour]
            abs_contours.append(pts)
        return abs_contours
    
    def _draw_contour_lines(self, draw, contours, color, width):
        for pts in contours:
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i + 1]], fill=color, width=width)
                
    def _connect_contour_endpoints(self, draw, contours, color, width):
        endpoints = []
        for i, pts in enumerate(contours):
            endpoints.append((pts[0], i, 'start'))
            endpoints.append((pts[-1], i, 'end'))
    
        pairs = []
        used = set()
    
        def dist_sq(p1, p2):
            return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2
    
        for i in range(len(endpoints)):
            p1, c1, pos1 = endpoints[i]
            for j in range(i + 1, len(endpoints)):
                p2, c2, pos2 = endpoints[j]
                if c1 != c2 and pos1 != pos2:
                    pairs.append((dist_sq(p1, p2), i, j))
    
        for _, i_idx, j_idx in sorted(pairs):
            if i_idx not in used and j_idx not in used:
                p1 = endpoints[i_idx][0]
                p2 = endpoints[j_idx][0]
                draw.line([p1, p2], fill=color, width=width)
                used.add(i_idx)
                used.add(j_idx)
                
########################
# MANIPULATE FUNCTIONS #
########################
    def manipulate(self, mode, alpha_blend_sigma=5):
        """
        Set manipulation mode and falloff for blending manipulated image.
    
        Parameters
        ----------
        mode : str
            "inside" or "outside"
        sigma : float
            Gaussian blur sigma for soft falloff (default: 5)
    
        Returns
        -------
        ROI
        """
        assert mode in ["inside", "outside"], "Mode must be 'inside' or 'outside'"
        self.mode = mode
        self.alpha_blend_sigma = alpha_blend_sigma
        return self


    def _apply_to_mask(self, manipulation_fn, falloff_sigma=0):
        assert self.mode in ["inside", "outside"], "Call .manipulate('inside' | 'outside') before applying."
    
        original = self.image.convert("RGBA")
        manipulated = manipulation_fn(self.image).convert("RGBA")
        mask = Image.new("L", self.image.size, 0)
    
        for region in self.image_regions:
            if hasattr(region, "_mask") and region._mask is not None:
                local_mask = region._mask.convert("L")
                box = (*region.top_left(), *region.bottom_right())
                mask.paste(local_mask, box)
            else:
                x0, y0 = region.top_left()
                x1, y1 = region.bottom_right()
                region_mask = Image.new("L", self.image.size, 0)
                draw = ImageDraw.Draw(region_mask)
                draw.rectangle([x0, y0, x1, y1], fill=255)
                mask = ImageChops.lighter(mask, region_mask)
      
        # Blur mask to get smooth transition
        if self.mode == "outside" and not hasattr(self, "_direction"):
            mask = ImageOps.invert(mask)
            
        blurred_mask = mask.filter(ImageFilter.GaussianBlur(radius=falloff_sigma))
            
        # Blend images using blurred mask
        blended = Image.composite(manipulated, original, blurred_mask)
        blended = blended.convert("RGBA")
        
        if self.mode == "outside":
            if hasattr(self, "_direction"):
                if self._direction == "horizontal":
                    blended = ImageOps.mirror(blended)
                else:
                    blended = ImageOps.flip(blended)
    
        return ROI(blended, self.image_regions)
    
    def _apply_flipping_mask(self, manipulation_fn, falloff_sigma=0):
        assert self.mode in ["inside", "outside"], "Call .manipulate('inside' | 'outside') before applying."
    
        original = self.image.convert("RGBA")
        manipulated = manipulation_fn(self.image).convert("RGBA")
        mask = Image.new("L", self.image.size, 0)
    
        for region in self.image_regions:
            if hasattr(region, "_mask") and region._mask is not None:
                local_mask = region._mask.convert("L")
                box = (*region.top_left(), *region.bottom_right())
                mask.paste(local_mask, box)
            else:
                x0, y0 = region.top_left()
                x1, y1 = region.bottom_right()
                region_mask = Image.new("L", self.image.size, 0)
                draw = ImageDraw.Draw(region_mask)
                draw.rectangle([x0, y0, x1, y1], fill=255)
                mask = ImageChops.lighter(mask, region_mask)
            
        blurred_mask = mask.filter(ImageFilter.GaussianBlur(radius=falloff_sigma))
            
        # Blend images using blurred mask
        blended = Image.composite(manipulated, original, blurred_mask)
        blended = blended.convert("RGBA")
        
        if self.mode == "outside":
            if hasattr(self, "_direction"):
                if self._direction == "horizontal":
                    blended = ImageOps.mirror(blended)
                else:
                    blended = ImageOps.flip(blended)
    
        return ROI(blended, self.image_regions)
    
    def _apply_transparency_mask(self, alpha_fn, alpha: float, falloff_sigma=0):
        assert self.mode in ["inside", "outside"], "Call .manipulate('inside' | 'outside') before applying."
        
        if alpha == 1.0:
            return self

        # Convert to RGBA
        original = self.image.convert("RGBA")
        manipulated = alpha_fn(original.copy())
    
        # Build a combined mask over all regions
        mask = Image.new("L", self.image.size, 0)
        for region in self.image_regions:
            if hasattr(region, "_mask") and region._mask is not None:
                local_mask = region._mask.convert("L")
                box = (*region.top_left(), *region.bottom_right())
                mask.paste(local_mask, box)
            else:
                x0, y0 = region.top_left()
                x1, y1 = region.bottom_right()
                draw = ImageDraw.Draw(mask)
                draw.rectangle([x0, y0, x1, y1], fill=int(alpha * 255))
            print("hello")
            plt.imshow(mask)
    
        if self.mode == "outside":
            mask = ImageOps.invert(mask)
    
        if falloff_sigma > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(radius=falloff_sigma))
    
        # Composite with a fully transparent image
        transparent_base = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
        if alpha < 1.0:
            # Transparent region over visible image
            blended = Image.composite(transparent_base, manipulated, mask)
        else:
            # Opaque region over original image
            blended = Image.composite(manipulated, self.image.convert("RGBA"), mask)
    
        return ROI(blended, self.image_regions)

    def blur(self, radius=5):
        """
        Apply Gaussian blur to the image inside or outside the region(s),
        depending on the mode set by `.manipulate()`.
    
        Parameters
        ----------
        radius : int or float
            Radius of the Gaussian blur.
    
        Returns
        -------
        ROI
        """
        def blur_fn(img):
            return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
        return self._apply_to_mask(blur_fn, falloff_sigma=self.alpha_blend_sigma)
        
    def saturation(self, factor=1.0):
        """
        Adjust color saturation inside or outside the region(s), based on `.manipulate()` mode.
    
        Parameters
        ----------
        factor : float
            Saturation adjustment factor.
            - 1.0 = no change
            - <1.0 = desaturate
            - >1.0 = more saturation
    
        Returns
        -------
        ROIImage
        """
        
        def apply_saturation_fn(img):
            return ImageEnhance.Color(img).enhance(factor)
    
        return self._apply_to_mask(apply_saturation_fn, falloff_sigma=self.alpha_blend_sigma)

    def frequency_filter(self, mode="low", cutoff=40):
        """
        Apply frequency filtering (low-pass or high-pass) to the image in the selected region(s).
    
        Parameters
        ----------
        mode : str
            Type of filter to apply: "low" (low-pass) or "high" (high-pass).
        cutoff : int
            Radius in frequency space to preserve or remove.
        Returns
        -------
        ROIImage
            The modified ROIImage object (self) with frequency filtering applied.
        """
        def apply_freq_filter_to_channel(channel_array):
            f = np.fft.fft2(channel_array)
            fshift = np.fft.fftshift(f)
    
            rows, cols = channel_array.shape
            crow, ccol = rows // 2, cols // 2
    
            y, x = np.ogrid[:rows, :cols]
            mask_area = (x - ccol) ** 2 + (y - crow) ** 2 <= cutoff ** 2
    
            mask = np.zeros_like(channel_array, dtype=np.uint8)
            if mode == "low":
                mask[mask_area] = 1
            elif mode == "high":
                mask[~mask_area] = 1
            else:
                raise ValueError("mode must be 'low' or 'high'")
    
            f_filtered = fshift * mask
            f_ishift = np.fft.ifftshift(f_filtered)
            img_back = np.fft.ifft2(f_ishift)
            return np.abs(img_back).clip(0, 255).astype(np.uint8)
    
        def filter_freq(img):
            if img.mode == "L":
                # Grayscale case
                arr = np.array(img)
                filtered = apply_freq_filter_to_channel(arr)
                return Image.fromarray(filtered).convert("RGB")
            elif img.mode == "RGB":
                arr = np.array(img)
                channels = [apply_freq_filter_to_channel(arr[:, :, i]) for i in range(3)]
                merged = np.stack(channels, axis=2)
                return Image.fromarray(merged.astype(np.uint8))
            else:
                raise ValueError("Unsupported image mode for frequency filtering.")
    
        return self._apply_to_mask(filter_freq, falloff_sigma=self.alpha_blend_sigma)
    
    def flip(self, direction):
        """
        Flip pixels inside or outside the region(s), depending on mode.
        """
        assert direction in ["horizontal", "vertical"], "Direction must be 'horizontal' or 'vertical'"
        assert self.mode in ["inside", "outside"], "Call .manipulate('inside' | 'outside') before flipping."
    
        self._direction = direction
        
        def flip_fn(img):
            return self._region_flip(img, direction, falloff_sigma=self.alpha_blend_sigma)
        
        result = self._apply_flipping_mask(flip_fn, falloff_sigma=self.alpha_blend_sigma)
        
        return result
        
    def _image_flip(self, direction):
        """
        Flip the entire image in the given direction.
        """
        if direction == "horizontal":
            return self.image.transpose(Image.FLIP_LEFT_RIGHT)
        elif direction == "vertical":
            return self.image.transpose(Image.FLIP_TOP_BOTTOM)
    
    def _region_flip(self, img, direction, falloff_sigma=0):
        """
        Flip content inside the ROI, optionally expanding the crop region by falloff_sigma.
        """
        flipped = img.copy()
        w, h = img.size
    
        for region in self.image_regions:
            x0, y0 = region.top_left()
            x1, y1 = region.bottom_right()
    
            # Expand crop box with falloff_sigma, ensuring bounds are within image
            pad = falloff_sigma
            ex0 = max(0, x0 - pad)
            ey0 = max(0, y0 - pad)
            ex1 = min(w, x1 + pad)
            ey1 = min(h, y1 + pad)
    
            region_crop = img.crop((ex0, ey0, ex1, ey1))
    
            if direction == "horizontal":
                region_flipped = region_crop.transpose(Image.FLIP_LEFT_RIGHT)
            elif direction == "vertical":
                region_flipped = region_crop.transpose(Image.FLIP_TOP_BOTTOM)
    
            flipped.paste(region_flipped, (ex0, ey0, ex1, ey1))
    
        return flipped
    
    def set_contrast_reference(self, target_region, target_image):
        """
        Set the reference region and image for histogram contrast matching.

        Parameters
        ----------
        target_region : ImageRegion
            Region in the target image to match contrast to.
        target_image : PIL.Image
            The full target image that contains the target_region.

        Returns
        -------
        None
        """
        self._contrast_match_to = (target_region, target_image)
        return self

    def contrast_match(self):
        """
        Apply histogram matching to adjust the contrast of the region(s)
        inside or outside the mask to match a reference region.
    
        Returns
        -------
        ROIImage
        """
        assert hasattr(self, "_contrast_match_to") and self._contrast_match_to is not None, \
            "Call .set_contrast_reference(target_region, target_image) before contrast_match()"
    
        def apply_contrast_fn(source_image):
            target_region, target_image = self._contrast_match_to
            bbox = target_region.get_bounding_box()
            target_crop = target_image.crop(bbox)
        
            source_crop = source_image.crop(bbox)
        
            source_np = np.array(source_crop)
            target_np = np.array(target_crop)
        
            if np.array_equal(source_np, target_np):
                # Skip matching if they're already equal
                return source_image

            matched_np = match_histograms(
                source_np, target_np,
                channel_axis=-1 if source_np.ndim == 3 else None
            )
            matched_crop = Image.fromarray(np.clip(matched_np, 0, 255).astype(np.uint8))
        
            # Paste matched crop back into original
            result = source_image.copy()
            result.paste(matched_crop, bbox)
            return result
    
        return self._apply_to_mask(apply_contrast_fn, falloff_sigma=self.alpha_blend_sigma)

    def transparency(self, alpha: float = 0.5) -> "ROI":
        def apply_transparency_fn(image: Image.Image) -> Image.Image:
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            r, g, b, _ = image.split()
            new_alpha = Image.new("L", image.size, int(alpha * 255))
            return Image.merge("RGBA", (r, g, b, new_alpha))
    
        return self._apply_transparency_mask(apply_transparency_fn, alpha=alpha, falloff_sigma=self.alpha_blend_sigma)

    def pixel_scramble(self):
        """
        Randomly scramble pixels inside or outside the selected region(s),
        with optional falloff via soft blending.
    
        Returns
        -------
        ROIImage
            A new ROIImage with scrambled pixels blended as per mode and sigma.
        """
    
        def scramble_fn(img):
            arr = np.array(img)
            h, w, c = arr.shape
            flat = arr.reshape(-1, c)
            np.random.shuffle(flat)
            scrambled = flat.reshape(h, w, c)
            return Image.fromarray(scrambled.astype('uint8'))
    
        return self._apply_to_mask(scramble_fn, falloff_sigma=self.alpha_blend_sigma)

    def grey(self):
        """
        Convert the image to greyscale (RGB) in the selected mode.

        Returns
        -------
        ROIImage
            The modified ROIImage object (self) with greyscale applied.
        """
        return self._apply_to_mask(lambda img: ImageOps.grayscale(img).convert("RGB"))
    
    def extract(self):
        """
        Extract ROI image as a PIL Image object.
    
        Returns
        -------
        PIL.Image.Image of the ROI object
        """
        return self.image