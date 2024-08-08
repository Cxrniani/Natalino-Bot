
import pandas as pd

def export_to_excel(self, dynamo_table, filename='inventory.xlsx'):
    """
    Exporta todos os dados da tabela DynamoDB para um arquivo Excel.

    :param filename: Nome do arquivo Excel a ser salvo
    :return: None
    """
    items = dynamo_table
    if items is None:
        print("Erro ao obter itens da tabela DynamoDB.")
        return

    # Cria um DataFrame do Pandas a partir dos itens
    df = pd.DataFrame(items)

    # Salva o DataFrame como um arquivo Excel
    df.to_excel(filename, index=False)