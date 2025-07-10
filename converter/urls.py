from django.urls import path
from . import views


app_name = "converter"

urlpatterns = [
    path(
        "get-target-formats/", views.get_target_formats_view, name="get_target_formats"
    ),
    path("", views.select_file_view, name="select_file"),
    path(
        "select-format/for/<slug:category>/",
        views.select_format_view,
        name="select_format",
    ),
    path(
        "convert/<slug:input_format>/to/<slug:output_format>/",
        views.convert_view,
        name="convert",
    ),
    path(
        "convert-progress-info/<str:token>/",
        views.convert_progressbar,
        name="convert_progress_info",
    ),
    path(
        "convert-progress/<str:token>/",
        views.convert_progress_view,
        name="convert_progress",
    ),
    path("download-file/<str:token>/", views.download_file_view, name="download_file"),
]
