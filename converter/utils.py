import os
import pathlib
import subprocess
import tempfile
import io
import pypandoc
from PIL import Image
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip


def get_output_choices(input_format):
    def to_choices(formats):
        return [(fmt, fmt.upper()) for fmt in formats]

    for formats_dict in [DOC_FORMATS, IMAGE_FORMATS, AUDIO_FORMATS, VIDEO_FORMATS]:
        if input_format in formats_dict:
            return to_choices(formats_dict[input_format])

    return []

class ImageConverter:
    def convert(self, file, output_format):
        output_format = output_format.upper()
        input_format = file.name.rsplit('.')[-1].upper()

        try:
            with Image.open(file) as img:  
                img = img.convert('RGB')
                result = io.BytesIO()
                img.save(result, format=output_format)
                result.seek(0)
            return result  # FileResponse
        except Exception as e:
            raise e


class DocConverter:
    def convert(self, file, output_format):
        input_format = file.name.split('.')[-1].lower()
        output_format = output_format.lower()
        engine = DOC_ENGINE[input_format][output_format]

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + input_format) as temp_input:
                temp_input.write(file.read())
                temp_input.flush()
                input_path = temp_input.name

            if engine == 'pandoc':
                with tempfile.NamedTemporaryFile(delete=False, suffix='.' + output_format) as temp_output:
                    output_path = temp_output.name
                pypandoc.convert_file(input_path, output_format, outputfile=output_path)

                with open(output_path, 'rb') as out_f:
                        result = io.BytesIO(out_f.read())
                        result.seek(0)
            else:
                with tempfile.TemporaryDirectory() as temp_output_dir:
                    cmd = ['libreoffice', '--headless', '--convert-to', output_format, '--outdir', temp_output_dir, input_path]
                    #subprocess.run(cmd, check=True)
                    result_proc = subprocess.run(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )

                    print("LibreOffice STDOUT:\n", result_proc.stdout.decode())
                    print("LibreOffice STDERR:\n", result_proc.stderr.decode())

                    result_proc.check_returncode()
                    #input_name = pathlib.Path(input_path).stem
                    #output_path = pathlib.Path(temp_output_dir) / f"{input_name}.{output_format}"
                    output_files = os.listdir(temp_output_dir)
                    if not output_files:
                        raise RuntimeError("Conversion failed: no output file generated.")

                    output_path = os.path.join(temp_output_dir, output_files[0])
            
                    with open(output_path, 'rb') as out_f:
                        result = io.BytesIO(out_f.read())
                        result.seek(0)

            return result

        except Exception as e:
            raise RuntimeError(f"Conversion aborted: {e}")

        finally:
            for path in [input_path, output_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass   


class AudioConverter:
    def convert(self, file, output_format):
        input_format = file.name.split('.')[-1].lower()
        output_format = output_format.lower()
        codec = AUDIO_CODEC.get(output_format)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + input_format) as temp_input:
                temp_input.write(file.read())
                temp_input.flush()
                input_path = temp_input.name

            audio = AudioFileClip(input_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + output_format) as temp_output:
                output_path = temp_output.name

            audio.write_audiofile(output_path, codec=codec, logger=None)
            
            with open(output_path, 'rb') as out_f:
                        result = io.BytesIO(out_f.read())
                        result.seek(0)

            return result

        except Exception as e:
            raise RuntimeError(f'{e}')




class VideoConverter:
    def convert(self, file, output_format):
        input_format = file.name.split('.')[-1].lower()
        output_format = output_format.lower()
        codec = VIDEO_CODEC.get(output_format)
        audio_codec = VIDEO_AUDIO_CODECS.get(output_format)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + input_format) as temp_input:
                temp_input.write(file.read())
                temp_input.flush()
                input_path = temp_input.name

            clip = VideoFileClip(input_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + output_format) as temp_output:
                output_path = temp_output.name

            clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec, verbose=False, logger=None)
            
            with open(output_path, 'rb') as out_f:
                        result = io.BytesIO(out_f.read())
                        result.seek(0)

            return result

        except Exception as e:
            raise RuntimeError(f'{e}')


VIDEO_AUDIO_CODECS = {
    'mp4':  'aac',
    'avi':  'libmp3lame',
    'mov':  'aac',
    'webm': 'libopus',
    'mkv':  'aac',
    'flv':  'libmp3lame',
    'wmv':  'wmav2',
    'mpeg': 'mp2',       # aac 
    'ogv':  'libvorbis', 
}

VIDEO_CODEC = {
    'mp4': 'libx264',
    'avi': 'mpeg4',
    'mov': 'libx264',
    'webm': 'libvpx',
    'mkv': 'libx264',
    'flv': 'flv',
    'wmv': 'wmv2',
    'mpeg': 'mpeg2video',
    'ogv': 'libtheora',
}

VIDEO_FORMATS = {
    'MP4':   ['AVI', 'MOV', 'WEBM', 'MKV', 'FLV', 'WMV', 'MPEG', 'OGV'],
    'AVI':   ['MP4', 'MOV', 'MKV', 'FLV', 'OGV'],
    'MOV':   ['MP4', 'AVI', 'WEBM', 'MKV', 'FLV', 'WMV', 'MPEG', 'OGV'],
    'WEBM':  ['MP4', 'AVI', 'MOV', 'MKV', 'FLV', 'WMV', 'MPEG', 'OGV'],
    'MKV':   ['MP4', 'AVI', 'MOV', 'WEBM', 'FLV', 'WMV', 'MPEG', 'OGV'],
    'FLV':   ['MP4', 'AVI', 'MOV', 'WEBM', 'MKV', 'WMV', 'MPEG', 'OGV'],
    'WMV':   ['MP4', 'AVI', 'MOV', 'WEBM', 'MKV', 'FLV', 'MPEG', 'OGV'],
    'MPEG':  ['MP4', 'AVI', 'MOV', 'WEBM', 'MKV', 'FLV', 'WMV', 'OGV'],
    'OGV':   ['MP4', 'AVI', 'MOV', 'WEBM', 'MKV', 'FLV', 'WMV', 'MPEG'],
}

AUDIO_CODEC = {
    'mp3': 'libmp3lame',
    'wav': None,
    'ogg': 'libvorbis',
    'flac': 'flac',
    'aac': 'aac',
    'm4a': 'aac',
    'wma': 'wmav2',
    'opus': 'libopus',
}

AUDIO_FORMATS = {
    'MP3':    ['WAV', 'OGG', 'FLAC', 'AAC', 'M4A', 'WMA', 'OPUS'],
    'WAV':    ['MP3', 'OGG', 'FLAC', 'AAC', 'M4A', 'WMA', 'OPUS'],
    'OGG':    ['MP3', 'WAV', 'FLAC', 'AAC', 'M4A', 'WMA', 'OPUS'],
    'FLAC':   ['MP3', 'WAV', 'OGG', 'AAC', 'M4A', 'WMA', 'OPUS'],
    'AAC':    ['MP3', 'WAV', 'OGG', 'FLAC', 'M4A', 'WMA', 'OPUS'],
    'M4A':    ['MP3', 'WAV', 'OGG', 'FLAC', 'AAC', 'WMA', 'OPUS'],
    'WMA':    ['MP3', 'WAV', 'OGG', 'FLAC', 'AAC', 'M4A', 'OPUS'],
    'OPUS':   ['MP3', 'WAV', 'OGG', 'FLAC', 'AAC', 'M4A', 'WMA'],
}

IMAGE_FORMATS = {
        'JPEG': ['PNG', 'BMP', 'GIF', 'TIFF', 'WEBP'],
        'PNG': ['JPEG', 'BMP', 'GIF', 'TIFF', 'WEBP'],
        'BMP': ['JPEG', 'PNG', 'GIF', 'TIFF', 'WEBP'],
        'GIF': ['PNG', 'JPEG', 'TIFF', 'WEBP'],
        'TIFF': ['PNG', 'JPEG', 'BMP', 'WEBP'],
        'WEBP': ['PNG', 'JPEG', 'GIF', 'TIFF'],
        'ICO': ['PNG'],
        'PPM': ['PNG', 'JPEG'],
        'TGA': ['PNG', 'JPEG'],}

DOC_ENGINE = {
    'markdown': {
        'html': 'pandoc',
        'latex': 'pandoc',
        'odt': 'pandoc',
        'docx': 'pandoc',
        'pdf': 'pandoc',
        'epub': 'pandoc',
        'rtf': 'pandoc',
    },
    'html': {
        'markdown': 'pandoc',
        'latex': 'pandoc',
        'odt': 'libreoffice',
        'docx': 'libreoffice',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
        'rtf': 'libreoffice',
    },
    'latex': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'odt': 'pandoc',
        'docx': 'pandoc',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
        'rtf': 'pandoc',
    },
    'odt': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'latex': 'pandoc',
        'doc': 'libreoffice',
        'docx': 'libreoffice',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
        'rtf': 'libreoffice',
    },
    'doc': {
        'pdf': 'libreoffice', #?
        'docx': 'libreoffice',
        'odt': 'libreoffice',
        'rtf': 'libreoffice',
        'html': 'libreoffice',
    },
    'docx': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'latex': 'pandoc',
        'odt': 'libreoffice',
        'doc': 'libreoffice',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
        'rtf': 'libreoffice',
    },
    'pdf': {
        'html': 'libreoffice',
    },
    'epub': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'latex': 'pandoc',
        'odt': 'pandoc',
        'docx': 'pandoc',
        'rtf': 'pandoc', #bad result
    },
    'rtf': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'latex': 'pandoc',
        'odt': 'libreoffice',
        'doc': 'libreoffice',
        'docx': 'libreoffice',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
    },
}



DOC_FORMATS = {
    'markdown': ['html', 'latex', 'odt', 'doc', 'docx', 'pdf', 'epub', 'rtf',],
    'html': ['markdown', 'latex', 'odt', 'doc', 'docx', 'pdf', 'epub', 'rtf',],
    'latex': ['markdown', 'html', 'odt', 'doc', 'docx', 'pdf', 'epub', 'rtf',],
    'odt': ['markdown', 'html', 'latex', 'doc', 'docx', 'pdf', 'epub', 'rtf',],
    'doc': ['html', 'odt', 'docx', 'pdf', 'rtf',],
    'docx': ['markdown', 'html', 'latex', 'odt', 'doc', 'pdf', 'epub', 'rtf',],
    'pdf': ['html',],
    'epub': ['markdown', 'html', 'latex', 'odt', 'docx', 'rtf',],
    'rtf': ['markdown', 'html', 'latex', 'odt', 'doc', 'docx', 'pdf', 'epub',],

}

