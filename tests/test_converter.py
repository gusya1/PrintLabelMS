import pytest

from pdf_to_image_converter.converter import ConvertError, Converter


def test_convert_pdf_to_jpeg_without_poppler(tmp_path):
    converter = Converter(poppler_path=tmp_path)
    with pytest.raises(ConvertError):
        converter.convert_pdf_to_jpeg(b"%PDF-1.4 fake", 200)
