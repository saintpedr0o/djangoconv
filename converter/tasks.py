import os
import uuid
from celery import shared_task
from .models import FormatConversion
from .utils.cache_func import get_converter_map, get_converter_class
from .utils.converters import get_conversion
from celery_progress.backend import ProgressRecorder
import time
from django.conf import settings
from .utils.redis_ext_client import redis_client


@shared_task(bind=True)
def convert_task(self, file, input_format, output_format, token):
    progress_recorder = ProgressRecorder(self)

    try:
        conversion, output_format = get_conversion(input_format, output_format)
        progress_recorder.set_progress(25, 100)

        format_type = conversion.input_format.file_type
        converter_map = get_converter_map(format_type)
        converter_class = get_converter_class(converter_map.class_path)

        progress_recorder.set_progress(50, 100)
        out_file = converter_class().convert(file, input_format, output_format)

        progress_recorder.set_progress(75, 100)
        filename = f"{token}{uuid.uuid4().hex[:8]}.{output_format}"
        temp_path = os.path.join(settings.TEMP_DIR, filename)

        with open(temp_path, "wb") as f:
            f.write(out_file.read())

        redis_client.setex(f"path:{token}", settings.FILE_TTL, temp_path)
        progress_recorder.set_progress(100, 100)

        return temp_path

    except FormatConversion.DoesNotExist:
        print(f"[convert_task] Unsupported format: {input_format} -> {output_format}")

    except Exception as e:
        print(f"[convert_task] - error to convert file: {e}")
        progress_recorder.set_progress(100, 100)
        raise self.retry(exc=e, countdown=10, max_retries=3)


@shared_task(bind=True)
def cleanup_temp_folder(self):
    now = time.time()
    max_age = settings.FILE_TTL

    try:
        with os.scandir(settings.TEMP_DIR) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                stat = entry.stat()
                age = now - stat.st_mtime
                if age <= max_age:
                    continue
                try:
                    # in future all prints = logs
                    os.remove(entry.path)
                    print(f"[cleanup_temp_folder] - removed file: {entry.path}")
                except PermissionError:
                    print(
                        f"[cleanup_temp_folder] - permission denied: {entry.path}, skipping"
                    )
                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(
                        f"[cleanup_temp_folder] - error to delete file {entry.path}: {e}"
                    )
    except Exception as e:
        print(
            f"[cleanup_temp_folder] - failed to scan directory {settings.TEMP_DIR}: {e}"
        )
        raise self.retry(exc=e, countdown=10, max_retries=3)
