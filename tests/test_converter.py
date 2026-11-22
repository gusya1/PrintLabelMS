import io

from PIL import Image
import pytest

from pdf_to_image_converter.converter import ConvertError, Converter


def build_minimal_pdf() -> bytes:
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 72 72] >>\nendobj\n",
    ]
    header = b"%PDF-1.4\n"
    body = b""
    offsets = []
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        pos += len(obj)
        body += obj
    xref_pos = pos
    xref = b"xref\n0 4\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = (
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF\n"
    )
    return header + body + xref + trailer


def test_convert_pdf_to_jpeg_returns_jpeg():
    converter = Converter()
    jpeg_bytes = converter.convert_pdf_to_jpeg(build_minimal_pdf(), 144)
    assert jpeg_bytes[:2] == b"\xff\xd8"


def test_convert_pdf_to_jpeg_resolution_scale():
    converter = Converter()
    jpeg_bytes = converter.convert_pdf_to_jpeg(build_minimal_pdf(), 144)
    img = Image.open(io.BytesIO(jpeg_bytes))
    assert img.size == (144, 144)


def test_convert_pdf_to_jpeg_corrupted_raises():
    converter = Converter()
    with pytest.raises(ConvertError):
        converter.convert_pdf_to_jpeg(b"%PDF-1.4 corrupted garbage", 144)
