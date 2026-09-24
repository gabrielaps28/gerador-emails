import requests
import re

from requests.auth import HTTPBasicAuth

from core.config import (
    EMAIL,
    TOKEN,
    BASE_URL,
    JIRA_PROJECT_KEY
)
from core.dados_demo import (
    NUMERO_CARD_DEMO,
    DESCRICAO_CARD_DEMO
)


# ==================================================
# Ajusta alguns nomes de órgãos para um formato menor
# Exemplo:
# POLICIA RODOVIARIA FEDERAL -> PRF
# ==================================================
def ajustar_orgao(nome_orgao):

    if 'POLICIA RODOVIARIA FEDERAL' in nome_orgao.upper():
        return 'PRF'

    if 'DNIT' in nome_orgao.upper():
        return 'DNIT'

    if 'PREFEITURA' in nome_orgao.upper():
        return nome_orgao.replace(
            'MUNICIPAL DE ',
            ''
        ).strip()

    return nome_orgao.strip()


# ==================================================
# Função usada para converter a descrição do Jira
# (ADF) em texto normal para conseguir fazer a leitura
# dos campos posteriormente.
# ==================================================
def extrair_texto_adf(node):

    if not isinstance(node, dict):
        return ""

    node_type = node.get("type", "")

    partes = []

    # percorre todos os nós filhos
    for filho in node.get("content", []):

        partes.append(
            extrair_texto_adf(filho)
        )

    texto_filhos = "".join(partes)

    # adiciona o texto encontrado
    if "text" in node:

        texto_filhos = (
            node["text"]
            + texto_filhos
        )

    # tipos de bloco que devem quebrar linha
    block_types = {
        "paragraph",
        "heading",
        "listItem",
        "bulletList",
        "orderedList",
        "blockquote",
        "rule",
        "mediaGroup"
    }

    if node_type in block_types:

        return texto_filhos + "\n"

    return texto_filhos


# ==================================================
# Busca os dados do card diretamente no Jira
# e retorna as informações encontradas na descrição.
#
# Exceção: o card reservado "0001" é o exemplo público de
# demonstração e sempre retorna dados fictícios locais, sem
# nenhuma chamada ao Jira.
# ==================================================
def buscar_dados_card(issue_key):

    print("VALOR RECEBIDO:", repr(issue_key))

    numeros = ''.join(re.findall(r'\d+', str(issue_key)))

    print("NUMEROS EXTRAIDOS:", numeros)

    if not numeros:
        raise ValueError("Nenhum número encontrado no card.")

    if numeros == NUMERO_CARD_DEMO:
        descricao = DESCRICAO_CARD_DEMO

    else:
        issue_key = f"{JIRA_PROJECT_KEY}-{numeros}"

        print("ISSUE FINAL:", issue_key)

        url = f"{BASE_URL}{issue_key}"

        response = requests.get(
            url,
            auth=HTTPBasicAuth(
                EMAIL,
                TOKEN
            ),
            headers={
                "Accept": "application/json"
            }
        )

        print("STATUS:", response.status_code)

        response.raise_for_status()

        desc_raw = response.json()['fields']['description']

        # algumas descrições vêm em formato ADF
        if isinstance(desc_raw, dict):

            descricao = extrair_texto_adf(
                desc_raw
            )

        else:

            descricao = desc_raw or ""

    dados = dict(re.findall(
        r'(?im)^\*?\s*(AIT|Nome do órgão|Código do órgão|Data Limite de indicação|Placa|Chassi|Renavam|Doc do Proprietário|Nome|RG|CPF|CNH|Data expiração CNH|UF CNH):\s*(.+)',
        descricao
    ))

    return dados
