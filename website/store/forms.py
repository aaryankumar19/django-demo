from django import forms
from .models import Product, Category, Banner
from PIL import Image
import io

ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_FILE_SIZE_MB = 10
DRIVE_MAX_SIZE_MB = 1

FORMAT_CHOICES = [
    ("original", "Keep Original Format"),
    ("jpg", "JPG"),
    ("jpeg", "JPEG"), 
    ("png", "PNG"),
    ("webp", "WEBP"),
]

COMPRESSION_CHOICES = [
    ("high", "High Quality (Minimal Compression) - Recommended"),
    ("auto", "Auto Compress (Smart Balance)"),
    ("medium", "Medium Quality (Balanced)"),
    ("low", "Low Quality (Maximum Compression)"),
    ("none", "No Compression (Original Quality)"),
]

class ImageProcessingMixin:
    def process_image(self, image_file, output_format="original", compression_level="high", max_size=(1200, 1200)):
        img = Image.open(image_file)
        original_format = image_file.content_type.split('/')[-1].lower()
        
        # Preserve original format if requested
        if output_format == "original":
            output_format = original_format
            if output_format not in ['jpg', 'jpeg', 'png', 'webp']:
                output_format = 'jpg'
        
        # Convert based on format requirements
        if output_format.lower() in ['jpg', 'jpeg']:
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert('RGB')
        elif output_format.lower() == 'png':
            img = img.convert('RGBA')
        elif output_format.lower() == 'webp':
            pass

        # Resize while keeping aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Set compression parameters with better quality focus
        if compression_level == "none":
            quality_params = self._get_no_compression_params(output_format)
        elif compression_level == "high":
            quality_params = self._get_high_quality_params(output_format)
        elif compression_level == "auto":
            quality_params = self._get_auto_compression_params(output_format)
        elif compression_level == "medium":
            quality_params = self._get_medium_quality_params(output_format)
        else:  # low
            quality_params = self._get_low_quality_params(output_format)

        buffer = io.BytesIO()
        img.save(buffer, format=output_format.upper(), **quality_params)
        buffer.seek(0)

        # Only compress further if absolutely necessary and not "none"
        if buffer.getbuffer().nbytes > DRIVE_MAX_SIZE_MB * 1024 * 1024:
            if compression_level == "none":
                raise forms.ValidationError(
                    f"Image is too large ({buffer.getbuffer().nbytes / (1024*1024):.1f}MB) for 'No Compression' option. "
                    f"Please choose a compression level or use a smaller image. Maximum size: {DRIVE_MAX_SIZE_MB}MB"
                )
            
            buffer = self._gentle_compress_to_fit(img, output_format, DRIVE_MAX_SIZE_MB * 1024 * 1024)

        return buffer, output_format

    def _get_no_compression_params(self, format):
        """Absolute highest quality possible"""
        if format.lower() in ['jpg', 'jpeg']:
            return {'quality': 100, 'optimize': False, 'progressive': False}
        elif format.lower() == 'png':
            return {'compress_level': 0, 'optimize': False}
        elif format.lower() == 'webp':
            return {'quality': 100, 'method': 6, 'lossless': True}
        return {'optimize': False}

    def _get_high_quality_params(self, format):
        """Very high quality with minimal compression"""
        if format.lower() in ['jpg', 'jpeg']:
            return {'quality': 98, 'optimize': True, 'progressive': True}
        elif format.lower() == 'png':
            return {'compress_level': 1, 'optimize': True}
        elif format.lower() == 'webp':
            return {'quality': 95, 'method': 6}
        return {'optimize': True}

    def _get_auto_compression_params(self, format):
        """Smart compression - still prioritizes quality"""
        if format.lower() in ['jpg', 'jpeg']:
            return {'quality': 92, 'optimize': True, 'progressive': True}
        elif format.lower() == 'png':
            return {'compress_level': 2, 'optimize': True}
        elif format.lower() == 'webp':
            return {'quality': 90, 'method': 5}
        return {'optimize': True}

    def _get_medium_quality_params(self, format):
        """Balanced quality and size"""
        if format.lower() in ['jpg', 'jpeg']:
            return {'quality': 88, 'optimize': True, 'progressive': True}
        elif format.lower() == 'png':
            return {'compress_level': 3, 'optimize': True}
        elif format.lower() == 'webp':
            return {'quality': 85, 'method': 4}
        return {'optimize': True}

    def _get_low_quality_params(self, format):
        """Higher compression but still reasonable quality"""
        if format.lower() in ['jpg', 'jpeg']:
            return {'quality': 80, 'optimize': True, 'progressive': True}
        elif format.lower() == 'png':
            return {'compress_level': 5, 'optimize': True}
        elif format.lower() == 'webp':
            return {'quality': 75, 'method': 4}
        return {'optimize': True}

    def _gentle_compress_to_fit(self, img, format, max_bytes):
        """Gentler compression approach that prioritizes quality"""
        if format.lower() in ['jpg', 'jpeg', 'webp']:
            # Start from higher quality and reduce more gradually
            quality_steps = [95, 92, 88, 85, 82, 78, 75, 72, 68, 65, 60, 55, 50]
            
            for quality in quality_steps:
                buffer = io.BytesIO()
                params = {'quality': quality, 'optimize': True, 'progressive': True}
                if format.lower() == 'webp':
                    params = {'quality': quality, 'method': 4}
                    del params['progressive']  # WebP doesn't use progressive
                
                img.save(buffer, format=format.upper(), **params)
                if buffer.getbuffer().nbytes <= max_bytes:
                    buffer.seek(0)
                    return buffer
        else:
            # For PNG, try gentle compression levels
            for compress_level in range(2, 7):
                buffer = io.BytesIO()
                img.save(buffer, format=format.upper(), 
                        compress_level=compress_level, optimize=True)
                if buffer.getbuffer().nbytes <= max_bytes:
                    buffer.seek(0)
                    return buffer
        
        # Only reduce dimensions if compression isn't enough
        original_size = img.size
        scale_steps = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7]
        
        for scale in scale_steps:
            new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
            resized_img = img.copy()
            resized_img.thumbnail(new_size, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            if format.lower() in ['jpg', 'jpeg']:
                resized_img.save(buffer, format=format.upper(), quality=85, optimize=True, progressive=True)
            elif format.lower() == 'webp':
                resized_img.save(buffer, format=format.upper(), quality=85, method=4)
            else:
                resized_img.save(buffer, format=format.upper(), compress_level=3, optimize=True)
            
            if buffer.getbuffer().nbytes <= max_bytes:
                buffer.seek(0)
                return buffer
        
        # Last resort - but still maintain reasonable quality
        buffer = io.BytesIO()
        if format.lower() in ['jpg', 'jpeg']:
            img.save(buffer, format=format.upper(), quality=65, optimize=True, progressive=True)
        elif format.lower() == 'webp':
            img.save(buffer, format=format.upper(), quality=65, method=4)
        else:
            img.save(buffer, format=format.upper(), compress_level=6, optimize=True)
        
        buffer.seek(0)
        return buffer

# Rest of your form classes remain the same
class ProductAdminForm(forms.ModelForm, ImageProcessingMixin):
    image_file = forms.ImageField(
        required=False,
        help_text="Upload an image (JPG, JPEG, PNG, WEBP). Max 10MB. Use the Image Editor to crop/adjust before processing.",
        widget=forms.FileInput(attrs={
            'accept': '.jpg,.jpeg,.png,.webp',
            'class': 'image-upload-input'
        })
    )
    output_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="original",
        required=True,
        help_text="Choose output format. 'Keep Original' maintains the uploaded format.",
        widget=forms.Select(attrs={'class': 'format-select'})
    )
    compression_level = forms.ChoiceField(
        choices=COMPRESSION_CHOICES,
        initial="high",
        required=True,
        help_text="Choose quality level. 'High Quality' is recommended for best results.",
        widget=forms.Select(attrs={'class': 'compression-select'})
    )

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['output_format'].widget.attrs.update({
            'style': 'margin-top: 10px; padding: 5px;'
        })
        self.fields['compression_level'].widget.attrs.update({
            'style': 'margin-top: 10px; padding: 5px;'
        })

    def clean(self):
        cleaned_data = super().clean()
        image_file = cleaned_data.get("image_file")
        compression_level = cleaned_data.get("compression_level")
        
        if image_file and compression_level == "none":
            img = Image.open(image_file)
            img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            format_type = image_file.content_type.split('/')[-1].lower()
            if format_type in ['jpg', 'jpeg']:
                img.save(buffer, format='JPEG', quality=100, optimize=False)
            elif format_type == 'png':
                img.save(buffer, format='PNG', compress_level=0, optimize=False)
            elif format_type == 'webp':
                img.save(buffer, format='WEBP', quality=100, method=6)
            
            if buffer.getbuffer().nbytes > DRIVE_MAX_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(
                    f"Image is too large ({buffer.getbuffer().nbytes / (1024*1024):.1f}MB) for 'No Compression'. "
                    f"Maximum size: {DRIVE_MAX_SIZE_MB}MB. Please choose a compression level or use a smaller image."
                )
            
            image_file.seek(0)
        
        return cleaned_data

    def clean_image_file(self):
        image = self.cleaned_data.get("image_file")
        if image:
            if image.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(f"Image cannot exceed {MAX_FILE_SIZE_MB}MB")

            if not any(image.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                raise forms.ValidationError("Allowed formats: JPG, JPEG, PNG, WEBP")
                
            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)
            except Exception:
                raise forms.ValidationError("Invalid image file")
                
        return image

class CategoryAdminForm(forms.ModelForm, ImageProcessingMixin):
    image_file = forms.ImageField(
        required=False,
        help_text="Upload an image (JPG, JPEG, PNG, WEBP). Max 5MB. Use the Image Editor to crop/adjust before processing.",
        widget=forms.FileInput(attrs={
            'accept': '.jpg,.jpeg,.png,.webp',
            'class': 'image-upload-input'
        })
    )
    output_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="original",
        required=True,
        help_text="Choose output format",
        widget=forms.Select(attrs={'class': 'format-select'})
    )
    compression_level = forms.ChoiceField(
        choices=COMPRESSION_CHOICES,
        initial="high",
        required=True,
        help_text="Choose quality level. 'High Quality' is recommended for best results.",
        widget=forms.Select(attrs={'class': 'compression-select'})
    )

    class Meta:
        model = Category
        fields = "__all__"

    def clean_image_file(self):
        image = self.cleaned_data.get("image_file")
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image size cannot exceed 5MB")
            if not any(image.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                raise forms.ValidationError("Allowed formats: JPG, JPEG, PNG, WEBP")
                
            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)
            except Exception:
                raise forms.ValidationError("Invalid image file")
                
        return image

class BannerAdminForm(forms.ModelForm, ImageProcessingMixin):
    image_file = forms.ImageField(
        required=False,
        help_text="Upload an image (JPG, JPEG, PNG, WEBP). Max 5MB. Use the Image Editor to crop/adjust before processing.",
        widget=forms.FileInput(attrs={
            'accept': '.jpg,.jpeg,.png,.webp',
            'class': 'image-upload-input'
        })
    )
    output_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="original",
        required=True,
        widget=forms.Select(attrs={'class': 'format-select'})
    )
    compression_level = forms.ChoiceField(
        choices=COMPRESSION_CHOICES,
        initial="high",
        required=True,
        widget=forms.Select(attrs={'class': 'compression-select'})
    )

    class Meta:
        model = Banner
        fields = "__all__"

    def clean_image_file(self):
        image = self.cleaned_data.get("image_file")
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image size cannot exceed 5MB")
            if not any(image.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                raise forms.ValidationError("Allowed formats: JPG, JPEG, PNG, WEBP")

            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)
            except Exception:
                raise forms.ValidationError("Invalid image file")
        return image
