"""
Provedores de OCR para extração de texto de imagens.
Suporta múltiplos métodos: Tesseract (local), EasyOCR (sem instalação), e serviços em nuvem.
"""
from typing import Optional
from PIL import Image
import io


class OCRProvider:
    """Interface base para provedores de OCR."""
    
    def extract_text(self, image_path: str = None, image_bytes: bytes = None) -> str:
        """
        Extrai texto de uma imagem.
        
        Args:
            image_path: Caminho para o arquivo de imagem
            image_bytes: Bytes da imagem
            
        Returns:
            Texto extraído
        """
        raise NotImplementedError


class TesseractOCRProvider(OCRProvider):
    """Provedor usando Tesseract OCR (requer instalação local)."""
    
    def __init__(self):
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            raise ImportError("pytesseract não está instalado. Execute: pip install pytesseract")
    
    def extract_text(self, image_path: str = None, image_bytes: bytes = None) -> str:
        """Extrai texto usando Tesseract."""
        if image_path:
            image = Image.open(image_path)
        elif image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
        else:
            raise ValueError("Forneça image_path ou image_bytes")
        
        try:
            text = self.pytesseract.image_to_string(image, lang='por')
        except:
            # Fallback para inglês se português não estiver disponível
            text = self.pytesseract.image_to_string(image, lang='eng')
        
        return text.strip()


class EasyOCRProvider(OCRProvider):
    """
    Provedor usando EasyOCR (não requer instalação do sistema, funciona em qualquer ambiente).
    Mais lento na primeira execução (baixa modelos), mas funciona em produção.
    """
    
    def __init__(self):
        try:
            import easyocr
            # Inicializa o reader (baixa modelos na primeira vez)
            # 'pt' para português, 'en' para inglês
            self.reader = easyocr.Reader(['pt', 'en'], gpu=False)
        except ImportError:
            raise ImportError("easyocr não está instalado. Execute: pip install easyocr")
    
    def extract_text(self, image_path: str = None, image_bytes: bytes = None) -> str:
        """Extrai texto usando EasyOCR."""
        if image_path:
            results = self.reader.readtext(image_path)
        elif image_bytes:
            import numpy as np
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            results = self.reader.readtext(image_array)
        else:
            raise ValueError("Forneça image_path ou image_bytes")
        
        # Combina todos os textos encontrados
        text = '\n'.join([result[1] for result in results])
        return text.strip()


class GoogleVisionOCRProvider(OCRProvider):
    """
    Provedor usando Google Cloud Vision API (requer credenciais, mas muito preciso).
    Ideal para produção em APIs hospedadas.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        try:
            from google.cloud import vision
            import os
            
            # Se não tiver credentials_path, tenta pegar da variável de ambiente
            if not credentials_path:
                credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            if credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            # Configura o cliente (usa credenciais padrão se configuradas)
            self.client = vision.ImageAnnotatorClient()
        except ImportError:
            raise ImportError("google-cloud-vision não está instalado. Execute: pip install google-cloud-vision")
    
    def extract_text(self, image_path: str = None, image_bytes: bytes = None) -> str:
        """Extrai texto usando Google Vision API."""
        from google.cloud import vision
        
        if image_path:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
        elif image_bytes:
            content = image_bytes
        else:
            raise ValueError("Forneça image_path ou image_bytes")
        
        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            return texts[0].description.strip()
        return ""


class AWSTextractOCRProvider(OCRProvider):
    """
    Provedor usando AWS Textract (requer credenciais AWS, muito preciso).
    Ideal para produção em APIs hospedadas na AWS.
    """
    
    def __init__(self, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        try:
            import boto3
            import os
            
            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    'textract',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Tenta usar credenciais padrão do ambiente AWS
                self.client = boto3.client('textract')
        except ImportError:
            raise ImportError("boto3 não está instalado. Execute: pip install boto3")
    
    def extract_text(self, image_path: str = None, image_bytes: bytes = None) -> str:
        """Extrai texto usando AWS Textract."""
        if image_path:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
        
        if not image_bytes:
            raise ValueError("Forneça image_path ou image_bytes")
        
        response = self.client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        text = ""
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text += block['Text'] + '\n'
        
        return text.strip()


def get_ocr_provider(provider: str = "auto") -> OCRProvider:
    """
    Factory function para obter o provedor de OCR apropriado.
    
    Args:
        provider: "tesseract", "easyocr", "google", "aws", ou "auto" (tenta encontrar o melhor disponível)
        
    Returns:
        Instância do OCRProvider
    """
    import os
    
    if provider == "auto":
        # Tenta encontrar o melhor provedor disponível
        # Prioridade: EasyOCR (funciona em qualquer lugar) > Tesseract > Serviços em nuvem
        
        # Tenta EasyOCR primeiro (não precisa instalação do sistema)
        try:
            return EasyOCRProvider()
        except:
            pass
        
        # Tenta Tesseract (pode não estar instalado)
        try:
            return TesseractOCRProvider()
        except:
            pass
        
        # Tenta Google Vision (se tiver credenciais configuradas)
        try:
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                return GoogleVisionOCRProvider()
        except:
            pass
        
        # Tenta AWS Textract (se tiver credenciais configuradas)
        try:
            if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
                return AWSTextractOCRProvider()
        except:
            pass
        
        raise RuntimeError(
            "Nenhum provedor de OCR disponível. "
            "Instale EasyOCR (recomendado): pip install easyocr "
            "ou configure um serviço em nuvem (Google Vision/AWS Textract)"
        )
    
    elif provider == "tesseract":
        return TesseractOCRProvider()
    elif provider == "easyocr":
        return EasyOCRProvider()
    elif provider == "google":
        return GoogleVisionOCRProvider()
    elif provider == "aws":
        return AWSTextractOCRProvider()
    else:
        raise ValueError(f"Provedor desconhecido: {provider}")

