import os
import fitz  # PyMuPDF is imported as fitz
from io import BytesIO
import logging

# 🔹 Ensure pdfminer.six is installed before importing
try:
    from pdfminer.high_level import extract_text
except ImportError:
    os.system("pip install pdfminer.six")
    from pdfminer.high_level import extract_text

def extract_text_from_pdf(uploaded_file):
    """
    Extract text from PDF using PyMuPDF with fallback to pdfminer.six
    """
    if uploaded_file is None:
        raise ValueError("No file was uploaded")

    text = ""
    pdf_bytes = uploaded_file.getvalue()  # Use getvalue() instead of read()

    # Try PyMuPDF first
    try:
        logging.info("Attempting to extract text using PyMuPDF")
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            logging.info(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
            text += page_text
        doc.close()
    except Exception as e:
        logging.warning(f"PyMuPDF extraction failed: {str(e)}")
        # Fallback to pdfminer.six
        try:
            logging.info("Attempting to extract text using pdfminer.six")
            pdf_stream = BytesIO(pdf_bytes)
            text = extract_text(pdf_stream)
            logging.info(f"pdfminer.six extracted {len(text)} characters")
        except Exception as inner_e:
            logging.error(f"pdfminer.six extraction failed: {str(inner_e)}")
            raise Exception(f"Failed to extract text using both methods: PyMuPDF error: {str(e)}, pdfminer.six error: {str(inner_e)}")

    if not text.strip():
        logging.warning("No text could be extracted from the PDF")
        raise Exception("No text could be extracted from the PDF. The file might be scanned, protected, or corrupted.")

    return text.strip()

