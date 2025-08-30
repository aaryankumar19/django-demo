from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Product, Category, Banner
from .forms import ProductAdminForm, CategoryAdminForm, BannerAdminForm
from .utils.google_drive import upload_file_to_drive


def get_full_image_url(google_file_id: str) -> str:
    """Return full-size image link."""
    return f"https://drive.google.com/uc?id={google_file_id}" if google_file_id else ""


def get_thumbnail_url(google_file_id: str, size=200) -> str:
    """Return thumbnail preview link."""
    return f"https://drive.google.com/thumbnail?id={google_file_id}&sz=w{size}" if google_file_id else ""


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "image_link", "image_preview", "file_size_info")
    readonly_fields = ("image_link", "image_preview", "file_size_info")

    class Media:
        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js",
            "admin/js/admin_image_cropper.js",
        )

    def save_model(self, request, obj, form, change):
        image_file = form.cleaned_data.get("image_file")
        output_format = form.cleaned_data.get("output_format")
        compression_level = form.cleaned_data.get("compression_level")

        if image_file:
            try:
                processed_file, ext = form.process_image(
                    image_file,
                    output_format=output_format,
                    compression_level=compression_level,
                    max_size=(800, 800)
                )

                # Get file size info
                file_size_mb = processed_file.getbuffer().nbytes / (1024 * 1024)

                google_id, uuid_val = upload_file_to_drive(processed_file, ext=ext)
                obj.google_file_id = google_id
                obj.image_uuid = uuid_val

                # Show success message with compression info
                compression_info = f"Image processed with {compression_level} compression ({file_size_mb:.2f}MB)"
                messages.success(request, compression_info)

            except Exception as e:
                messages.error(request, f"Error processing image: {str(e)}")
                return

        super().save_model(request, obj, form, change)

    def image_link(self, obj):
        if obj.google_file_id:
            return format_html(
                '<a href="{0}" target="_blank" rel="noopener">View Full Size</a>',
                get_full_image_url(obj.google_file_id),
            )
        return "No Image"
    image_link.short_description = "Image Link"

    def image_preview(self, obj):
        if obj.google_file_id:
            return format_html(
                '<img src="{0}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" alt="Category image">',
                get_thumbnail_url(obj.google_file_id, 100),
            )
        return "No Image"
    image_preview.short_description = "Preview"

    def file_size_info(self, obj):
        if obj.google_file_id:
            return "< 1MB (Optimized)"
        return "No Image"
    file_size_info.short_description = "File Size"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "category", "stock", "is_active", "image_link", "image_preview")
    readonly_fields = ("image_link", "image_preview")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")

    class Media:
        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js",
            "admin/js/admin_image_cropper.js",
        )

    def save_model(self, request, obj, form, change):
        image_file = form.cleaned_data.get("image_file")
        output_format = form.cleaned_data.get("output_format")
        compression_level = form.cleaned_data.get("compression_level")

        if image_file:
            try:
                processed_file, ext = form.process_image(
                    image_file,
                    output_format=output_format,
                    compression_level=compression_level,
                    max_size=(1200, 1200)
                )

                file_size_mb = processed_file.getbuffer().nbytes / (1024 * 1024)

                google_id, uuid_val = upload_file_to_drive(processed_file, ext=ext)
                obj.google_file_id = google_id
                obj.image_uuid = uuid_val

                # Show success message with processing info
                processing_info = f"Image processed with {compression_level} compression ({file_size_mb:.2f}MB)"
                messages.success(request, processing_info)

            except Exception as e:
                messages.error(request, f"Error processing image: {str(e)}")
                return

        super().save_model(request, obj, form, change)

    def image_link(self, obj):
        if obj.google_file_id:
            return format_html(
                '<a href="{0}" target="_blank" rel="noopener">View Full Size</a>',
                get_full_image_url(obj.google_file_id),
            )
        return "No Image"
    image_link.short_description = "Image Link"

    def image_preview(self, obj):
        if obj.google_file_id:
            return format_html(
                '<img src="{0}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 4px;" alt="Product image">',
                get_thumbnail_url(obj.google_file_id, 100),
            )
        return "No Image"
    image_preview.short_description = "Preview"

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    form = BannerAdminForm
    list_display = ("id", "title", "text", "banner_type", "is_active", "image_link", "image_preview")
    list_filter = ("is_active", "banner_type")  # Added banner_type filter
    search_fields = ("title", "text", "search_query")  # Added search_query
    ordering = ("-id",)
    readonly_fields = ("image_link", "image_preview")

    class Media:
        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js",
            "admin/js/admin_image_cropper.js",
        )

    def save_model(self, request, obj, form, change):
        image_file = form.cleaned_data.get("image_file")
        output_format = form.cleaned_data.get("output_format")
        compression_level = form.cleaned_data.get("compression_level")

        if image_file:
            try:
                processed_file, ext = form.process_image(
                    image_file,
                    output_format=output_format,
                    compression_level=compression_level,
                    max_size=(1600, 600)
                )
                file_size_mb = processed_file.getbuffer().nbytes / (1024 * 1024)

                google_id, uuid_val = upload_file_to_drive(processed_file, ext=ext)
                obj.google_file_id = google_id
                obj.image_uuid = uuid_val

                messages.success(
                    request,
                    f"Banner image processed ({compression_level}, {file_size_mb:.2f}MB)"
                )
            except Exception as e:
                messages.error(request, f"Error uploading banner image: {str(e)}")
                return

        super().save_model(request, obj, form, change)

    def image_link(self, obj):
        if getattr(obj, "google_file_id", None):
            return format_html(
                '<a href="{}" target="_blank">View Full Size</a>',
                get_full_image_url(obj.google_file_id),
            )
        return "No Image"
    image_link.short_description = "Image Link"

    def image_preview(self, obj):
        if getattr(obj, "google_file_id", None):
            return format_html(
                '<img src="{}" style="max-width:200px; max-height:100px; object-fit:cover; border-radius:4px;">',
                get_thumbnail_url(obj.google_file_id, 300),
            )
        return "No Image"
    image_preview.short_description = "Preview"
