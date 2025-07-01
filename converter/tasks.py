import os
import uuid
from celery import shared_task
from django.http import Http404
from .utils.converters import FORMATS_MAP
from celery_progress.backend import ProgressRecorder
import time
from django.conf import settings
from .utils.redis_ext_client import redis_client


@shared_task(bind=True)
def convert_task(self, file, input_format, output_format, token):
    progress_recorder = ProgressRecorder(self)
    entry = FORMATS_MAP.get(input_format)
    if not entry or output_format not in entry["outputs"]:
        raise Http404(f"Unsupported conversion: {input_format} -> {output_format}")

    progress_recorder.set_progress(25, 100)
    converter = entry["converter"]
    progress_recorder.set_progress(50, 100)
    out_file = converter().convert(file, input_format, output_format)
    progress_recorder.set_progress(75, 100)
    filename = f"{token}{uuid.uuid4().hex[:8]}.{output_format}"
    temp_path = os.path.join(settings.TEMP_DIR, filename)

    with open(temp_path, "wb") as f:
        f.write(out_file.read())

    redis_client.setex(f"path:{token}", settings.FILE_TTL, temp_path)
    progress_recorder.set_progress(100, 100)
    return temp_path


@shared_task
def cleanup_temp_folder():
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
                    print(f"celery - removed file: {entry.path}")
                except PermissionError:
                    print(f"celery - permission denied: {entry.path}, skipping")
                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(f"celery - error to delete file {entry.path}: {e}")
    except Exception as e:
        print(f"celery - failed to scan directory {settings.TEMP_DIR}: {e}")
