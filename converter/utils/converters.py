import os
import subprocess
import tempfile
import io
import pypandoc
from PIL import Image
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from abc import ABC, abstractmethod


def get_output_choices(input_format):
    input_format = input_format.lower()
    if input_format in FORMATS_MAP:
        outputs = FORMATS_MAP[input_format]["outputs"]
        return [(fmt, fmt.upper()) for fmt in outputs]
    return []


class ConversionError(Exception):
    pass


class BaseConverter(ABC):
    @abstractmethod
    def convert(self, file, input_format, output_format):
        pass

    def _save_file_for_return(self, output_path):
        with open(output_path, "rb") as out_f:
            result = io.BytesIO(out_f.read())
            result.seek(0)
            return result

    def _create_temp_dir(self, file, input_format, output_format):
        tmp_dir_obj = tempfile.TemporaryDirectory()
        tmp_dir = tmp_dir_obj.name
        input_path = os.path.join(tmp_dir, f"input.{input_format}")
        output_path = os.path.join(tmp_dir, f"output.{output_format}")

        with open(input_path, "wb") as f:
            f.write(file)

        return input_path, output_path, tmp_dir_obj


class ImageConverter(BaseConverter):
    def convert(self, file, _input_format, output_format):
        try:
            file_stream = io.BytesIO(file)
            file_stream.seek(0)

            with Image.open(file_stream) as img:
                img = img.convert("RGB")
                result = io.BytesIO()
                img.save(result, format=output_format.upper())
                result.seek(0)
                return result

        except Exception as e:
            raise ConversionError(f"Сonversion failed: {e}")


class DocConverter(BaseConverter):
    def convert(self, file, input_format, output_format):
        engine = DOC_ENGINE[input_format][output_format]

        try:
            input_path, output_path, tmp_dir_obj = self._create_temp_dir(
                file, input_format, output_format
            )

            if engine == "pandoc":
                pypandoc.convert_file(input_path, output_format, outputfile=output_path)
                result = self._save_file_for_return(output_path)
            else:
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    output_format,
                    "--outdir",
                    tmp_dir_obj.name,
                    input_path,
                ]
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                output_files = [
                    f
                    for f in os.listdir(tmp_dir_obj.name)
                    if f.endswith(f".{output_format.lower()}")
                ]
                output_path = os.path.join(tmp_dir_obj.name, output_files[0])
                result = self._save_file_for_return(output_path)

            return result

        except Exception as e:
            raise ConversionError(f"Сonversion failed: {e}")

        finally:
            tmp_dir_obj.cleanup()


class AudioConverter(BaseConverter):
    def convert(self, file, input_format, output_format):
        codec = AUDIO_CODEC.get(output_format)

        try:
            input_path, output_path, tmp_dir_obj = self._create_temp_dir(
                file, input_format, output_format
            )
            audio = AudioFileClip(input_path)
            audio.write_audiofile(output_path, codec=codec, logger=None)
            result = self._save_file_for_return(output_path)
            return result

        except Exception as e:
            raise ConversionError(f"Сonversion failed: {e}")

        finally:
            tmp_dir_obj.cleanup()


class VideoConverter(BaseConverter):
    def _get_audio_ext(self, acodec):
        return {
            "aac": "m4a",
            "libmp3lame": "mp3",
            "libvorbis": "ogg",
            "libopus": "opus",
            "mp2": "mp2",
            "wmav2": "wma",
        }.get(acodec)

    def convert(self, file, input_format, output_format):
        codec = VIDEO_CODEC.get(output_format)
        audio_codec = VIDEO_AUDIO_CODECS.get(output_format)

        try:
            input_path, output_path, tmp_dir_obj = self._create_temp_dir(
                file, input_format, output_format
            )
            clip = VideoFileClip(input_path)
            ext = self._get_audio_ext(audio_codec)

            if ext:
                temp_audio_path = os.path.join(tmp_dir_obj.name, f"temp-audio.{ext}")
                clip.write_videofile(
                    output_path,
                    codec=codec,
                    audio_codec=audio_codec,
                    logger=None,
                    temp_audiofile=temp_audio_path,
                )
            else:
                clip.write_videofile(
                    output_path, codec=codec, audio_codec=audio_codec, logger=None
                )

            result = self._save_file_for_return(output_path)
            return result

        except Exception as e:
            raise ConversionError(f"Сonversion failed: {e}")

        finally:
            tmp_dir_obj.cleanup()


BASE_IMAGE_FORMATS = ["JPEG", "PNG", "BMP", "GIF", "TIFF", "WEBP"]
IMAGE_FORMATS = {
    fmt: [f for f in BASE_IMAGE_FORMATS if f != fmt] for fmt in BASE_IMAGE_FORMATS
}
IMAGE_FORMATS.update(
    {
        "ICO": ["PNG"],
        "PPM": ["PNG", "JPEG"],
        "TGA": ["PNG", "JPEG"],
    }
)

DOC_FORMATS = {
    "markdown": [
        "html",
        "latex",
        "odt",
        "doc",
        "docx",
        "pdf",
        "epub",
        "rtf",
    ],
    "html": [
        "markdown",
        "latex",
        "odt",
        "docx",
        "pdf",
        "epub",
        "rtf",
    ],
    "latex": [
        "markdown",
        "html",
        "odt",
        "doc",
        "docx",
        "pdf",
        "epub",
        "rtf",
    ],
    "odt": [
        "markdown",
        "html",
        "latex",
        "doc",
        "docx",
        "pdf",
        "epub",
        "rtf",
    ],
    "doc": [
        "html",
        "odt",
        "docx",
        "pdf",
        "epub",
        "rtf",
    ],
    "docx": [
        "markdown",
        "html",
        "latex",
        "odt",
        "doc",
        "pdf",
        "epub",
        "rtf",
    ],
    "pdf": [
        "html",
    ],
    "epub": [
        "markdown",
        "html",
        "latex",
        "odt",
        "docx",
        "rtf",
    ],
    "rtf": [
        "odt",
        "doc",
        "docx",
        "pdf",
        "epub",
    ],
}

VIDEO = ["mp4", "avi", "mov", "webm", "mkv", "flv", "wmv", "mpeg", "ogv"]
VIDEO_FORMATS = {fmt: [f for f in VIDEO if f != fmt] for fmt in VIDEO}

VIDEO_AUDIO_CODECS = {
    "mp4": "aac",
    "avi": "libmp3lame",
    "mov": "aac",
    "webm": "libvorbis",
    "mkv": "aac",
    "flv": "libmp3lame",
    "wmv": "wmav2",
    "mpeg": "mp2",
    "ogv": "libvorbis",
}

VIDEO_CODEC = {
    "mp4": "libx264",
    "avi": "mpeg4",
    "mov": "libx264",
    "webm": "libvpx",
    "mkv": "libx264",
    "flv": "flv",
    "wmv": "wmv2",
    "mpeg": "mpeg2video",
    "ogv": "libtheora",
}


AUDIO = ["mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "opus"]
AUDIO_FORMATS = {fmt: [f for f in AUDIO if f != fmt] for fmt in AUDIO}

AUDIO_CODEC = {
    "mp3": "libmp3lame",
    "wav": None,
    "ogg": "libvorbis",
    "flac": "flac",
    "aac": "aac",
    "m4a": "aac",
    "wma": "wmav2",
    "opus": "libopus",
}

DOC_ENGINE = {
    "markdown": {
        "html": "pandoc",
        "latex": "pandoc",
        "odt": "pandoc",
        "doc": "libreoffice",
        "docx": "pandoc",
        "pdf": "libreoffice",
        "epub": "pandoc",
        "rtf": "pandoc",
    },
    "html": {
        "markdown": "pandoc",
        "latex": "pandoc",
        "odt": "libreoffice",
        "docx": "pandoc",
        "pdf": "libreoffice",
        "epub": "pandoc",
        "rtf": "pandoc",
    },
    "latex": {
        "markdown": "pandoc",
        "html": "pandoc",
        "odt": "pandoc",
        "doc": "libreoffice",
        "docx": "pandoc",
        "pdf": "libreoffice",
        "epub": "pandoc",
        "rtf": "pandoc",
    },
    "odt": {
        "markdown": "pandoc",
        "html": "pandoc",
        "latex": "pandoc",
        "doc": "libreoffice",
        "docx": "libreoffice",
        "pdf": "libreoffice",
        "epub": "pandoc",
        "rtf": "libreoffice",
    },
    "doc": {
        "html": "libreoffice",
        "odt": "libreoffice",
        "pdf": "libreoffice",
        "docx": "libreoffice",
        "epub": "libreoffice",
        "rtf": "libreoffice",
    },
    "docx": {
        "markdown": "pandoc",
        "html": "pandoc",
        "latex": "pandoc",
        "odt": "libreoffice",
        "doc": "libreoffice",
        "pdf": "libreoffice",
        "epub": "pandoc",
        "rtf": "libreoffice",
    },
    "pdf": {
        "html": "libreoffice",
    },
    "epub": {
        "markdown": "pandoc",
        "html": "pandoc",
        "latex": "pandoc",
        "odt": "pandoc",
        "docx": "pandoc",
        "rtf": "pandoc",
    },
    "rtf": {
        "odt": "libreoffice",
        "doc": "libreoffice",
        "docx": "libreoffice",
        "pdf": "libreoffice",
        "epub": "libreoffice",
    },
}

FORMAT_SOURCES = [
    (DOC_FORMATS, DocConverter),
    (IMAGE_FORMATS, ImageConverter),
    (AUDIO_FORMATS, AudioConverter),
    (VIDEO_FORMATS, VideoConverter),
]

FORMATS_MAP = {}

for format_dict, converter_class in FORMAT_SOURCES:
    for input_format, output_formats in format_dict.items():
        FORMATS_MAP[input_format.lower()] = {
            "converter": converter_class,
            "outputs": [f for f in output_formats],
        }
