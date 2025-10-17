from pdf2image import pdf2image
import pdf2image.exceptions

import io

class ConvertError(Exception):
    pass

class Converter:
    def __init__(self, poppler_path=None):
        self.poppler_path = poppler_path
    
    def convert_pdf_to_jpeg(self, pdf_data, resolution):
        try:
            pages = pdf2image.convert_from_bytes(pdf_data, resolution, poppler_path=self.poppler_path)
            img_bytes = io.BytesIO()
            pages[0].save(img_bytes, format='JPEG')
            return img_bytes.getvalue()
        except pdf2image.exceptions.PDFInfoNotInstalledError as e:
            raise ConvertError(str(e))