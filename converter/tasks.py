import os
import uuid
from celery import shared_task
from django.http import Http404
from .utils import FORMATS_MAP
from celery_progress.backend import ProgressRecorder
import time
from django.conf import settings


@shared_task(bind=True)
def convert_task(self, file, input_format, output_format):
    progress_recorder = ProgressRecorder(self)
    entry = FORMATS_MAP.get(input_format)
    if not entry or output_format not in entry["outputs"]:
        raise Http404(f"Unsupported conversion: {input_format} -> {output_format}")

    progress_recorder.set_progress(25, 100)
    converter = entry["converter"]
    progress_recorder.set_progress(50, 100)
    out_file = converter.convert(file, input_format, output_format)
    progress_recorder.set_progress(75, 100)
    filename = f"converted_{uuid.uuid4().hex[:10]}.{output_format}"
    temp_path = os.path.join(settings.TEMP_DIR, filename)

    with open(temp_path, "wb") as f:
        f.write(out_file.read())

    progress_recorder.set_progress(100, 100)

    return temp_path


@shared_task
def cleanup_temp_folder():
    now = time.time()
    max_age = 5 * 60  # 5 min

    if not os.path.exists(settings.TEMP_DIR):
        print(f"celery - dir not found: {settings.TEMP_DIR}")
        return

    for filename in os.listdir(settings.TEMP_DIR):
        file_path = os.path.join(settings.TEMP_DIR, filename)

        if not os.path.isfile(file_path):
            continue

        age = now - os.path.getmtime(file_path)

        if age <= max_age:
            continue
        # in future all prints = logs
        try:
            os.remove(file_path)
            print(f"celery - removed file: {file_path}")
        except PermissionError:
            print(f"celery - permission denied: {file_path}, skipping")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"celery - error to delete file {file_path}: {e}")
