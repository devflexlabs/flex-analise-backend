from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image(output_path):
    # Create a white image
    width, height = 800, 1000
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Define text content
    text = """
    CEDULA DE CREDITO BANCARIO - FINANCIAMENTO DE VEICULO
    
    CREDOR: BANCO SANTANDER (BRASIL) S.A.
    CNPJ: 07.707.650/0001-10
    
    EMITENTE: JOAO DA SILVA
    CPF: 123.456.789-00
    
    DADOS DO CONTRATO:
    Numero do Contrato: 987654321
    Valor Total do Credito: R$ 50.000,00
    Quantidade de Parcelas: 48
    Valor da Parcela: R$ 1.850,50
    Data do Primeiro Vencimento: 10/05/2024
    Taxa de Juros Mensal: 2.85%
    Taxa de Juros Anual: 39.80%
    CET Mensal: 3.10%
    CET Anual: 44.50%
    
    DADOS DO BEM:
    Marca: TOYOTA
    Modelo: COROLLA XEI 2.0
    Ano/Modelo: 2022/2022
    Placa: ABC1D23
    RENAVAM: 12345678901
    
    CLAUSULAS E CONDICOES:
    1. O atraso no pagamento de qualquer parcela implicara em multa de 2% 
    e juros moratorios de 1% ao mes.
    2. O veiculo fica alienado fiduciariamente ao Credor.
    """
    
    # Try to use a default font
    try:
        # On Windows, Arial is usually available
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    draw.multiline_text((50, 50), text, fill='black', font=font, spacing=10)
    
    # Save image
    image.save(output_path)
    print(f"Test image created at: {output_path}")

if __name__ == "__main__":
    output_dir = "tests"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    create_test_image(os.path.join(output_dir, "test_contract.png"))
