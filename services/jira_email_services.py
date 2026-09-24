import re
import requests
from requests.auth import HTTPBasicAuth

from core.config import (
    EMAIL,
    TOKEN,
    BASE_URL,
    JIRA_PROJECT_KEY,
    NOME_EMPRESA
)

from core.dados_demo import (
    NUMERO_CARD_DEMO,
    DESCRICAO_CARD_DEMO
)


# ==========================================================
# UTILITÁRIOS
# ==========================================================

def ajustar_orgao(nome_orgao: str) -> str:
    """
    Ajusta o nome do órgão para utilização no assunto do e-mail.

    Alguns nomes podem ser abreviados para deixar o assunto
    mais organizado.
    """
    if not nome_orgao:
        return ""

    nome = nome_orgao.upper()

    if "POLICIA RODOVIARIA FEDERAL" in nome:
        return "PRF"

    if "DNIT" in nome:
        return "DNIT"

    if "PREFEITURA" in nome:
        return nome_orgao.replace("MUNICIPAL DE", "").strip()

    return nome_orgao.strip()


def extrair_texto_adf(node) -> str:
    """
    Converte uma descrição em formato ADF (Atlassian Document Format)
    para texto simples.

    Isso permite que as informações recebidas sejam posteriormente
    processadas pelo gerador.
    """
    if not isinstance(node, dict):
        return ""

    texto = ""

    for filho in node.get("content", []):
        texto += extrair_texto_adf(filho)

    if "text" in node:
        texto = node["text"] + texto

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

    if node.get("type") in block_types:
        return texto + "\n"

    return texto


def parse_dados(descricao: str) -> dict:
    """
    Extrai da descrição os campos necessários para gerar o e-mail.

    Na versão pública, os campos foram generalizados para evitar
    exposição de regras de negócio ou informações internas.
    """
    dados = {}

    re_campos = {
        "Processo": r"(?m)^Processo:\s*(.*)$",
        "Nome do órgão": r"(?m)^Nome do órgão:\s*(.*)$",
        "Código do órgão": r"(?m)^Código do órgão:\s*(.*)$",
        "Data Limite": r"(?m)^Data Limite:\s*(.*)$",

        "Identificador": r"(?m)^Identificador:\s*(.*)$",
        "Documento": r"(?m)^Documento:\s*(.*)$",

        "Nome": r"(?m)^Nome:\s*(.*)$",
        "RG": r"(?m)^RG:\s*(.*)$",
        "CPF": r"(?m)^CPF:\s*(.*)$"
    }

    for campo, regex in re_campos.items():
        match = re.search(regex, descricao, re.IGNORECASE)

        if match:
            dados[campo] = match.group(1).strip()

    return dados


# ==========================================================
# BUSCA DE DADOS
# ==========================================================

def buscar_issue(issue_key: str) -> dict:
    """
    Busca os dados relacionados ao número informado.

    O número reservado para exemplo utiliza dados locais fictícios,
    permitindo executar o projeto público sem acessar serviços externos.
    """

    # Mantém somente os números digitados pelo usuário.
    numeros = "".join(re.findall(r"\d+", str(issue_key)))

    if not numeros:
        raise ValueError("Nenhum número encontrado no card.")

    # O exemplo 0001 utiliza dados locais e fictícios.
    if numeros == NUMERO_CARD_DEMO:
        return {
            "fields": {
                "description": DESCRICAO_CARD_DEMO
            }
        }

    # Monta o identificador utilizado para consulta.
    issue_key = f"{JIRA_PROJECT_KEY}-{numeros}"

    url = f"{BASE_URL}{issue_key}"

    # Realiza a consulta utilizando as credenciais configuradas
    # no ambiente local.
    response = requests.get(
        url,
        auth=HTTPBasicAuth(EMAIL, TOKEN),
        headers={"Accept": "application/json"},
        timeout=15
    )

    # Gera uma exceção caso a consulta não seja bem-sucedida.
    response.raise_for_status()

    return response.json()


# ==========================================================
# GERADOR DE E-MAIL
# ==========================================================

def gerar_email(issue_key: str) -> dict:
    """
    Gera automaticamente o assunto e o corpo do e-mail
    utilizando os dados encontrados para o processo informado.
    """

    # Busca as informações relacionadas ao número informado.
    data = buscar_issue(issue_key)

    # Recupera a descrição.
    desc_raw = data["fields"].get("description", "")

    # Algumas respostas podem utilizar ADF.
    # Nesse caso, convertemos o conteúdo para texto simples.
    if isinstance(desc_raw, dict):
        descricao = extrair_texto_adf(desc_raw)
    else:
        descricao = desc_raw or ""

    # Extrai os campos estruturados da descrição.
    dados = parse_dados(descricao)

    # Ajusta o nome do órgão para utilização no assunto.
    orgao_assunto = ajustar_orgao(
        dados.get("Nome do órgão", "")
    )

    # ======================================================
    # ASSUNTO DO E-MAIL
    # ======================================================

    assunto = (
        f"Envio de Documentação - "
        f"{orgao_assunto} - "
        f"{NOME_EMPRESA} - "
        f"Processo {dados.get('Processo', '')}"
    )

    # ======================================================
    # FORMATAÇÃO DA DATA
    # ======================================================

    data_limite = dados.get("Data Limite", "")

    # Converte AAAA-MM-DD para DD-MM-AAAA quando necessário.
    if "-" in data_limite:
        partes_data = data_limite.split("-")

        if (
            partes_data[0].isdigit()
            and len(partes_data[0]) == 4
        ):
            data_limite = "-".join(
                reversed(partes_data)
            )

    # Mantém o nome completo do órgão no corpo do e-mail.
    nome_orgao_capturado = dados.get(
        "Nome do órgão",
        ""
    )

    # ======================================================
    # CORPO DO E-MAIL
    # ======================================================

    corpo = f"""Prezados,

Encaminhamos a documentação referente ao Processo nº {dados.get('Processo', '')}, conforme solicitado.

Informações do Processo:
* Órgão Responsável: {nome_orgao_capturado}
* Código do Órgão: {dados.get('Código do órgão', '')}
* Data Limite: {data_limite}

Dados da Solicitação:
* Identificador: {dados.get('Identificador', '')}
* Documento: {dados.get('Documento', '')}

Dados do Solicitante:
* Nome: {dados.get('Nome', '')}
* RG: {dados.get('RG', '')}
* CPF: {dados.get('CPF', '')}

Os documentos comprobatórios encontram-se anexados. Para qualquer informação adicional, estamos à disposição.

Atenciosamente,"""

    # Retorna as informações para a interface.
    return {
        "assunto": assunto,
        "corpo": corpo,
        "dados": dados
    }