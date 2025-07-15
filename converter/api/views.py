import os
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from ..tasks import convert_task
import secrets
from rest_framework.response import Response
from django.conf import settings
import mimetypes
from ..utils.redis_ext_client import redis_client


class AsyncConvertView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        output_format = request.data.get("output_format")

        if not file:
            return Response({"error": "No uploaded file found"}, status=400)

        file_bin = file.read()
        input_format = file.name.rsplit(".", 1)[-1].lower()
        token = secrets.token_urlsafe(16)

        convert_task.delay(file_bin, input_format, output_format, token)
        redis_client.setex(f"conv:{token}", settings.FILE_TTL, token)

        return Response({"result token": token}, status=202)


class ResultsConvertView(APIView):
    def get(self, request, token):
        try:
            for file in os.listdir(settings.TEMP_DIR):
                if file.startswith(token):
                    path = os.path.join(settings.TEMP_DIR, file)
                    if os.path.isfile(path):
                        mime_type, _ = mimetypes.guess_type(file)
                        return FileResponse(
                            open(path, "rb"),
                            as_attachment=True,
                            filename=file,
                            content_type=mime_type or "application/octet-stream",
                        )

            task_id = redis_client.get(f"conv:{token}")
            if task_id:
                return Response({"result": "Result file not found"}, status=404)

            return Response({"result": "Invalid token or no task found"}, status=404)

        except Exception as e:
            return Response({"result": f"Unexpected error: {str(e)}"}, status=500)
