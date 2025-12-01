"""
Módulos de processamento de documentos (PDF, imagens, OCR).
"""
from .document_processor import DocumentProcessor
from .ocr_provider import get_ocr_provider, OCRProvider

__all__ = ["DocumentProcessor", "get_ocr_provider", "OCRProvider"]



