from django.contrib import admin
from .models import FileFormat, FormatConversion, ConverterMap


@admin.register(FileFormat)
class FileFormatAdmin(admin.ModelAdmin):
    list_display = ("name", "file_type")
    list_filter = ("file_type",)
    search_fields = ("name",)


@admin.register(FormatConversion)
class FormatConversionAdmin(admin.ModelAdmin):
    list_display = (
        "input_format",
        "output_format",
        "engine",
        "video_codec",
        "audio_video_codec",
        "audio_codec",
    )
    list_filter = ("engine", "input_format__file_type")
    search_fields = (
        "input_format__name",
        "output_format__name",
        "video_codec",
        "audio_codec",
        "engine",
    )
    autocomplete_fields = ("input_format", "output_format")


@admin.register(ConverterMap)
class ConverterMapAdmin(admin.ModelAdmin):
    list_display = ("format_type", "class_path")
    list_filter = ("format_type",)
    search_fields = ("class_path",)
