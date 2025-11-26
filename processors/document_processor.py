"""
Módulo para processar documentos (PDF, texto e imagens).
"""
import pdfplumber
from pathlib import Path
from typing import Optional
from backend.processors.ocr_provider import get_ocr_provider


class DocumentProcessor:
    """Processa documentos PDF e texto para extração de conteúdo."""
    
    def __init__(self, ocr_provider: str = "auto"):
        """
        Inicializa o processador de documentos.
        
        Args:
            ocr_provider: Provedor de OCR a usar ("auto", "tesseract", "easyocr", "google", "aws")
        """
        self.ocr_provider_name = ocr_provider
        self._ocr_provider = None
    
    @property
    def ocr_provider(self):
        """Lazy loading do provedor de OCR."""
        if self._ocr_provider is None:
            self._ocr_provider = get_ocr_provider(self.ocr_provider_name)
        return self._ocr_provider
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrai texto de um arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Texto extraído do PDF
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Erro ao processar PDF: {str(e)}")
        
        return text.strip()
    
    def clean_text(self, text: str) -> str:
        """
        Limpa e normaliza o texto extraído.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto limpo e normalizado
        """
        # Remove espaços múltiplos
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extrai texto de uma imagem usando OCR (Optical Character Recognition).
        
        Args:
            image_path: Caminho para o arquivo de imagem (JPEG, PNG, etc.)
            
        Returns:
            Texto extraído da imagem
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
        
        try:
            return self.ocr_provider.extract_text(image_path=image_path)
        except Exception as e:
            raise Exception(f"Erro ao processar imagem com OCR: {str(e)}")
    
    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """
        Extrai texto de uma imagem a partir de bytes (útil para uploads).
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Texto extraído da imagem
        """
        try:
            return self.ocr_provider.extract_text(image_bytes=image_bytes)
        except Exception as e:
            raise Exception(f"Erro ao processar imagem com OCR: {str(e)}")
    
    def process_document(self, file_path: Optional[str] = None, text: Optional[str] = None) -> str:
        """
        Processa um documento (PDF ou texto direto).
        
        Args:
            file_path: Caminho para arquivo PDF (opcional)
            text: Texto direto (opcional)
            
        Returns:
            Texto processado e limpo
        """
        if file_path:
            # Verifica se é imagem ou PDF
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
                raw_text = self.extract_text_from_image(file_path)
            else:
                raw_text = self.extract_text_from_pdf(file_path)
        elif text:
            raw_text = text
        else:
            raise ValueError("Forneça file_path ou text")
        
        return self.clean_text(raw_text)

