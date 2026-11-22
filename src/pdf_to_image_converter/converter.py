import io

import pypdfium2 as pdfium


class ConvertError(Exception):
    pass


class Converter:
    def convert_pdf_to_jpeg(self, pdf_data, resolution):
        try:
            with pdfium.PdfDocument(pdf_data) as document:
                bitmap = document[0].render(scale=resolution / 72)
                image = bitmap.to_pil()
            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="JPEG")
            return buffer.getvalue()
        except pdfium.PdfiumError as e:
            raise ConvertError(str(e)) from e
