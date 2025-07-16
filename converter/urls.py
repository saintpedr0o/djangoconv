from django.urls import path
from . import views


app_name = "converter"

urlpatterns = [
    path(
        "get-target-formats/",
        views.GetTargetFormatView.as_view(),
        name="get_target_formats",
    ),
    path("", views.SelectFileView.as_view(), name="select_file"),
    path(
        "select-format/for/<slug:category>/",
        views.SelectFormatView.as_view(),
        name="select_format",
    ),
    path(
        "convert/<slug:input_format>/to/<slug:output_format>/",
        views.ConvertView.as_view(),
        name="convert",
    ),
    path(
        "convert-progress-info/<str:token>/",
        views.ProgressbarView.as_view(),
        name="convert_progress_info",
    ),
    path(
        "convert-progress/<str:token>/",
        views.ConvertProgressView.as_view(),
        name="convert_progress",
    ),
    path(
        "download-file/<str:token>/",
        views.DownloadFileView.as_view(),
        name="download_file",
    ),
]
