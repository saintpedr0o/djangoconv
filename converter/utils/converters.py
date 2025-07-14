import os
import subprocess
import tempfile
import io
import pypandoc
from PIL import Image
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from abc import ABC, abstractmethod
from converter.models import FormatConversion


FORMAT_ALIASES = {
    "jpg": "jpeg",
    "jpe": "jpeg",
    "jfif": "jpeg",
    "tif": "tiff",
    "bmpf": "bmp",
    "dib": "bmp",
    "htm": "html",
}


def get_conversion(input_format, output_format):
    input_format = FORMAT_ALIASES.get(input_format, input_format)
    output_format = FORMAT_ALIASES.get(output_format, output_format)
    conversion = FormatConversion.objects.get(
        input_format__name__iexact=input_format,
        output_format__name__iexact=output_format,
    )
    return conversion, output_format


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
        conversion = get_conversion(input_format, output_format)
        engine = conversion.engine

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
        conversion = get_conversion(input_format, output_format)
        codec = conversion.audio_codec

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
        conversion = get_conversion(input_format, output_format)
        codec = conversion.video_codec
        audio_codec = conversion.audio_video_codec

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
