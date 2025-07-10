from django.db import models


class FormatType(models.TextChoices):
    IMAGE = "image", "Image"
    DOCUMENT = "document", "Document"
    AUDIO = "audio", "Audio"
    VIDEO = "video", "Video"


class FileFormat(models.Model):
    name = models.CharField(max_length=10, unique=True)
    file_type = models.CharField(max_length=10, choices=FormatType.choices)

    def __str__(self):
        return f"{self.name} ({self.file_type})"


class FormatConversion(models.Model):
    input_format = models.ForeignKey(
        FileFormat, related_name="conversions_from", on_delete=models.CASCADE
    )
    output_format = models.ForeignKey(
        FileFormat, related_name="conversions_to", on_delete=models.CASCADE
    )
    video_codec = models.CharField(max_length=50, blank=True, null=True)
    audio_video_codec = models.CharField(max_length=50, blank=True, null=True)
    audio_codec = models.CharField(max_length=50, blank=True, null=True)
    engine = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.input_format.name} → {self.output_format.name}"


class ConverterMap(models.Model):
    format_type = models.CharField(
        max_length=10, choices=FormatType.choices, unique=True
    )
    class_path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.format_type}: {self.class_path}"
