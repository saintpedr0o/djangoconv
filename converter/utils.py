import os
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

        try:
            with Image.open(file) as img:  
                img = img.convert('RGB')
                result = io.BytesIO()
                img.save(result, format=output_format)
                result.seek(0)
            return result
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
                    subprocess.run(cmd, check=True)
                    output_files = os.listdir(temp_output_dir)
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
            with tempfile.TemporaryDirectory() as tmp_dir:
                input_path = os.path.join(tmp_dir, f"input.{input_format}")
                output_path = os.path.join(tmp_dir, f"output.{output_format}")

                with open(input_path, 'wb') as f:
                    f.write(file.read())

                audio = AudioFileClip(input_path)
                audio.write_audiofile(output_path, codec=codec, logger=None)

                with open(output_path, 'rb') as f:
                    result = io.BytesIO(f.read())
                    result.seek(0)

                return result
            
        except Exception as e:
            raise RuntimeError(f'{e}')
        
        finally:
            try:
                if 'audio' in locals():
                    audio.close()
            except Exception:
                pass


class VideoConverter:
    def convert(self, file, output_format):
        input_format = file.name.split('.')[-1].lower()
        output_format = output_format.lower()
        codec = VIDEO_CODEC.get(output_format)
        audio_codec = VIDEO_AUDIO_CODECS.get(output_format)

        def get_audio_ext(acodec):
            return {
                'aac': 'm4a',
                'libmp3lame': 'mp3',
                'libvorbis': 'ogg',
                'libopus': 'opus',
                'mp2': 'mp2',
                'wmav2': 'wma',
            }.get(acodec)
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                input_path = os.path.join(tmp_dir, f"input.{input_format}")
                output_path = os.path.join(tmp_dir, f"output.{output_format}")
                temp_audio_path = None

                with open(input_path, 'wb') as temp_input:
                    temp_input.write(file.read())

                clip = VideoFileClip(input_path)

                ext = get_audio_ext(audio_codec)

                if ext:
                    temp_audio_path = os.path.join(tmp_dir, f"temp-audio.{ext}")
                    clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec, logger=None, temp_audiofile=temp_audio_path)
                else:
                    clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec, logger=None)
                
                with open(output_path, 'rb') as out_f:
                    result = io.BytesIO(out_f.read())
                    result.seek(0)

                return result

        except Exception as e:
            raise RuntimeError(f'{e}')
        
        finally:
            try:
                if 'clip' in locals():
                    clip.close()
            except Exception:
                pass


BASE_IMAGE_FORMATS = ['JPEG', 'PNG', 'BMP', 'GIF', 'TIFF', 'WEBP']
IMAGE_FORMATS = {fmt: [f for f in BASE_IMAGE_FORMATS if f != fmt] for fmt in BASE_IMAGE_FORMATS}
IMAGE_FORMATS.update({
    'ICO': ['PNG'],
    'PPM': ['PNG', 'JPEG'],
    'TGA': ['PNG', 'JPEG'],
})

DOC_FORMATS = {
    'markdown': ['html', 'latex', 'odt', 'doc','docx', 'pdf', 'epub', 'rtf',],
    'html': ['markdown', 'latex', 'odt', 'docx', 'pdf', 'epub', 'rtf',],
    'latex': ['markdown', 'html', 'odt', 'doc', 'docx', 'pdf', 'epub', 'rtf',],
    'odt': ['markdown', 'html', 'latex', 'doc', 'docx', 'pdf', 'epub', 'rtf',],
    'doc': ['html', 'odt', 'docx', 'pdf', 'epub', 'rtf',],
    'docx': ['markdown', 'html', 'latex', 'odt', 'doc', 'pdf', 'epub', 'rtf',],
    'pdf': ['markdown', 'html',],
    'epub': ['markdown', 'html', 'latex', 'odt', 'docx', 'rtf',],
    'rtf': ['odt', 'doc', 'docx', 'pdf', 'epub',],

}

VIDEO = ['MP4', 'AVI', 'MOV', 'WEBM', 'MKV', 'FLV', 'WMV', 'MPEG', 'OGV']
VIDEO_FORMATS = {fmt: [f for f in VIDEO if f != fmt] for fmt in VIDEO}

VIDEO_AUDIO_CODECS = {
    'mp4':  'aac',
    'avi':  'libmp3lame',
    'mov':  'aac',
    'webm': 'libvorbis', #'libopus',
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


AUDIO = ['MP3', 'WAV', 'OGG', 'FLAC', 'AAC', 'M4A', 'WMA', 'OPUS']
AUDIO_FORMATS = {fmt: [f for f in AUDIO if f != fmt] for fmt in AUDIO}

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

DOC_ENGINE = {
    'markdown': {
        'html': 'pandoc',
        'latex': 'pandoc',
        'odt': 'pandoc',
        'doc': 'libreoffice',
        'docx': 'pandoc',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
        'rtf': 'pandoc',
    },
    'html': {
        'markdown': 'pandoc',
        'latex': 'pandoc',
        'odt': 'libreoffice',
        'docx': 'pandoc',
        'pdf': 'libreoffice',
        'epub': 'pandoc',
        'rtf': 'pandoc',
    },
    'latex': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'odt': 'pandoc',
        'doc': 'libreoffice',
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
        'html': 'libreoffice',
        'odt': 'libreoffice',
        'pdf': 'libreoffice',
        'docx': 'libreoffice',
        'epub': 'libreoffice',
        'rtf': 'libreoffice',
        
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
        'markdown': 'libreoffice',
        'html': 'libreoffice',
    },
    'epub': {
        'markdown': 'pandoc',
        'html': 'pandoc',
        'latex': 'pandoc',
        'odt': 'pandoc',
        'docx': 'pandoc',
        'rtf': 'pandoc',
    },
    'rtf': {
        'odt': 'libreoffice',
        'doc': 'libreoffice',
        'docx': 'libreoffice',
        'pdf': 'libreoffice',
        'epub': 'libreoffice',
    },
}

format_converter_pairs = [
    (DOC_FORMATS, DocConverter),
    (IMAGE_FORMATS, ImageConverter),
    (AUDIO_FORMATS, AudioConverter),
    (VIDEO_FORMATS, VideoConverter),
]

CONVERTER_MAP = {}
for formats, converter in format_converter_pairs:
    for fmt in formats:
        CONVERTER_MAP[fmt] = converter
