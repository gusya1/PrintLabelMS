import pytest
import pdf2image.exceptions

from pdf_to_image_converter.converter import ConvertError, Converter


def test_convert_pdf_to_jpeg_without_poppler(tmp_path):
    converter = Converter(poppler_path=tmp_path)
    with pytest.raises(ConvertError):
        converter.convert_pdf_to_jpeg(b"%PDF-1.4 fake", 200)


@pytest.mark.parametrize(
        "exception",
        [
            pdf2image.exceptions.PopplerNotInstalledError,
            pdf2image.exceptions.PDFInfoNotInstalledError,
            pdf2image.exceptions.PDFPageCountError,
            pdf2image.exceptions.PDFSyntaxError,
            pdf2image.exceptions.PDFPopplerTimeoutError,
        ],
)
def test_convert_pdf_to_jpeg_wraps_poppler_errors(monkeypatch, exception):
    def fake_convert(*args, **kwargs):
        raise exception("test error")

    monkeypatch.setattr("pdf_to_image_converter.converter.pdf2image.convert_from_bytes", fake_convert)
    converter = Converter()
    with pytest.raises(ConvertError, match="test error"):
        converter.convert_pdf_to_jpeg(b"%PDF-1.4 fake", 200)
