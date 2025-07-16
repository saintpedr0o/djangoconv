from django.core.cache import cache
from converter.models import ConverterMap, FileFormat, FormatConversion
from functools import lru_cache
import importlib


def get_input_choices(category: str):
    cache_key = f"input_choices_{category.lower()}"
    return cache.get_or_set(
        cache_key,
        lambda: [
            (f.name, f.name.upper())
            for f in FileFormat.objects.filter(file_type__iexact=category)
        ],
        timeout=3600,
    )


def get_output_choices(input_format: str):
    cache_key = f"output_choices_{input_format.lower()}"

    def fetch_choices():
        try:
            input_fmt_obj = FileFormat.objects.get(name__iexact=input_format)
        except FileFormat.DoesNotExist:
            return []

        conversions = FormatConversion.objects.select_related("output_format").filter(
            input_format=input_fmt_obj
        )

        return [
            (conv.output_format.name, conv.output_format.name.upper())
            for conv in conversions
        ]

    return cache.get_or_set(cache_key, fetch_choices, timeout=3600)


def get_converter_map(format_type):
    cache_key = f"converter_map_{format_type}"
    converter_map = cache.get(cache_key)
    if not converter_map:
        converter_map = ConverterMap.objects.get(format_type=format_type)
        cache.set(cache_key, converter_map, timeout=3600)
    return converter_map


@lru_cache(maxsize=4)
def get_converter_class(class_path):
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Import error -  '{class_path}': {e}")
