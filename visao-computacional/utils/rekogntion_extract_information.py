# -+-+-+-+-+ Extração de Características e Cores Dominantes do Rekogntion -+-+-+-+-+ 
def extract_data_from_rekognition_label(response):
    item_info = {
        'item_name' : [],
        'donation_type' : 'miscellaneous',
        'donation_value' : None,
        'conservation_state' : 'good state',
        'Categories' : [],
        'BoundingBox' : []
    }

    # Extraindo tipo do item e confiança
    for label in response['Labels']:

        item_name = label.get('Name')
        categories = extract_categories(label)
        bounding_box = extract_boundbox(label)

        if item_name not in item_info['item_name']: item_info['item_name'].append(item_name)
        if categories not in item_info['Categories']: item_info['Categories'].append(categories)
        if bounding_box not in item_info['BoundingBox']: item_info['BoundingBox'].append(bounding_box)
    
        item_info['type'] = label['Name']
        item_info['confidence'] = label['Confidence']

    # Extraindo cores dominantes do foreground
    foreground_colors = response.get('ImageProperties', {}).get('Foreground', {}).get('DominantColors', [])
    colors = []

    for color in foreground_colors:
        color_info = {
            'color_name': color['CSSColor'],
            'hex_code': color['HexCode'],
            'pixel_percent': color['PixelPercent']
        }
        colors.append(color_info)
    
    item_info['colors'] = colors

    return item_info
   
# -+-+-+-+-+ Extração de Nomes das Categorias -+-+-+-+-+
def extract_categories(label):
    categories_name = None
    
    try:
        categories_name = [categories['Name'] for categories in label['Categories'] if categories.get('Name')]
        return categories_name[0] 
    
    # Em caso de erro, loga a exceção e retorna
    except Exception as e:
        return None
    
# -+-+-+-+-+ Extração de BoundingBox -+-+-+-+-+
def extract_boundbox(label):
    
    try:
        bounding_box = [instance for instance in label['Instances'] if instance.get('BoundingBox')]
        return bounding_box[0] 
    
    # Em caso de erro, loga a exceção e retorna
    except Exception as e:
        return None
    
# -+-+-+-+-+ Extração de Dados de Texto do Rekognition -+-+-+-+-+
def extract_text_data_from_rekognition(response):
    item_info = {
        'donation_type' : 'cash',
    }

    # Extraindo textos detectados que são do tipo 'LINE'
    detected_texts = [text['DetectedText'] for text in response if text['Type'] == 'LINE']

    item_info['rekogntion_texts'] = detected_texts
    item_info['donation_value'] = find_donation_value(item_info['rekogntion_texts'])
    return item_info

import re

# Função para identificar valores monetários em uma lista de mensagens
def find_donation_value(mensagens):
    # Lista para armazenar todos os valores encontrados
    valores_encontrados = []
    
    # Regex para identificar valores monetários no formato XX,XX ou TT.TT
    padrao = r'\b\d{1,3}[.,]\d{2}\b'
    
    # Percorrer a lista de mensagens
    for text in mensagens:
        # Encontrar todos os valores na mensagem atual
        valores = re.findall(padrao, text)
        # Adicionar os valores encontrados à lista
        valores_encontrados.extend(valores)
    
    return valores_encontrados

# Lista de mensagens
# mensagens = [
#             "Comprovante de Pagamento",
#             "Bradesco",
#             "Boleto de Cobrança",
#             "Data: 19/02/2019",
#             "Nome do Banco Destinatário: Banco Itaú S.A.",
#             "Número de Identificação:",
#             "00001.00100 00800.000700 00500.000007 3 60070000001698",
#             "Data de Vencimento:",
#             "22/02/2019",
#             "Valor do Pagamento: 16,98",
#             "Data do Pagamento:",
#             "20/02/2019",
#             "Descrição do Pagamento:",
#             "hospedagem",
#             "Debitado da:",
#             "Conta Fácil",
#             "A cobrança acima foi paga através do(a) BRADESCO CELULAR, dentro das condições",
#             "especificadas.",
#             "o lançamento consta no extrato do(a) cliente Agência 111 - Conta 111111, da data de",
#             "pagamento, sob o número de protocolo 0000000.",
#             "Banco Bradesco S.A.",
#             "http://www.bradesco. .com.br"
#         ]

# dicionario  = {"Labels" : [
#             {
#                 "Name": "Page",
#                 "Confidence": 99.26079559326172,
#                 "Instances": [],
#                 "Parents": [
#                     {
#                         "Name": "Text"
#                     }
#                 ],
#                 "Aliases": [],
#                 "Categories": [
#                     {
#                         "Name": "Text and Documents"
#                     }
#                 ]
#             },
#             {
#                 "Name": "Text",
#                 "Confidence": 99.26079559326172,
#                 "Instances": [],
#                 "Parents": [],
#                 "Aliases": [],
#                 "Categories": [
#                     {
#                         "Name": "Text and Documents"
#                     }
#                 ]
#             },
#             {
#                 "Name": "Paper",
#                 "Confidence": 83.13408660888672,
#                 "Instances": [],
#                 "Parents": [],
#                 "Aliases": [],
#                 "Categories": [
#                     {
#                         "Name": "Materials"
#                     }
#                 ]
#             }
#         ]
# }

# # Encontrar valores monetários na lista de mensagens
# valores = extract_data_from_rekognition_label(dicionario)

# # Exibir os valores encontrados
# print(f"Valores encontrados: {valores}")