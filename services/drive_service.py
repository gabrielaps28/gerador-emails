import os
import re
import json


# ==========================================================
# UTILITÁRIOS
# ==========================================================

def extrair_numero_card(texto):
    """
    Extrai a parte numérica do card.

    Exemplos:
    CARD-0001 -> 0001
    0001      -> 0001
    """

    match = re.search(r'\d+', str(texto))

    if match:
        return match.group(0)

    return ""


# ==========================================================
# ROTA CONFIGURADA PELO USUÁRIO
# ==========================================================

def obter_pasta_configurada():
    """
    Obtém a pasta escolhida no botão 'Configurar Rota'.
    """

    config_local = "config_rota_indicacoes.json"

    if not os.path.exists(config_local):
        print("Arquivo de configuração não encontrado.")
        return None

    try:
        with open(config_local, "r", encoding="utf-8") as f:
            config = json.load(f)

        pasta = config.get("rota_sistema")

        if not pasta:
            print("Nenhuma rota configurada.")
            return None

        if not os.path.isdir(pasta):
            print("A rota configurada não existe:")
            print(pasta)
            return None

        return pasta

    except Exception as e:
        print("Erro ao ler configuração:", e)
        return None


# ==========================================================
# LOCALIZAÇÃO DA PASTA DO CARD
# ==========================================================

def localizar_pasta_processo(card):
    """
    Procura a pasta correspondente ao card dentro da pasta
    escolhida pelo usuário.
    """

    numero_card = extrair_numero_card(card)

    if not numero_card:
        print("Card inválido.")
        return None

    pasta_base = obter_pasta_configurada()

    if not pasta_base:
        print("Nenhuma pasta válida foi configurada.")
        return None

    print("\n==============================")
    print("CARD PROCURADO:", numero_card)
    print("ROTA SELECIONADA:", pasta_base)
    print("==============================")

    # ------------------------------------------------------
    # CASO A PRÓPRIA PASTA SELECIONADA SEJA A DO CARD
    # ------------------------------------------------------

    numero_pasta_base = extrair_numero_card(
        os.path.basename(pasta_base)
    )

    if numero_pasta_base == numero_card:
        print("A própria pasta selecionada corresponde ao card.")
        print("PASTA ENCONTRADA:", pasta_base)

        return pasta_base

    # ------------------------------------------------------
    # PROCURA O CARD NAS PASTAS E SUBPASTAS
    # ------------------------------------------------------

    try:
        for raiz, pastas, _ in os.walk(pasta_base):

            for nome_pasta in pastas:

                numero_pasta = extrair_numero_card(
                    nome_pasta
                )

                if numero_pasta == numero_card:

                    caminho = os.path.join(
                        raiz,
                        nome_pasta
                    )

                    print("PASTA ENCONTRADA:")
                    print(caminho)

                    return caminho

        print("Nenhuma pasta encontrada para o card:", numero_card)

        return None

    except Exception as e:
        print("Erro ao procurar pasta:", e)
        return None


# ==========================================================
# BUSCA DOS DOCUMENTOS
# ==========================================================

def buscar_documentos(card):
    """
    Busca todos os arquivos existentes dentro da pasta
    correspondente ao card.
    """

    pasta = localizar_pasta_processo(card)

    if not pasta:
        return []

    documentos = []

    try:
        for raiz, _, arquivos in os.walk(pasta):

            for nome_arquivo in arquivos:

                caminho = os.path.join(
                    raiz,
                    nome_arquivo
                )

                documentos.append({
                    "nome": nome_arquivo,
                    "caminho": caminho
                })

        print(
            "TOTAL DE DOCUMENTOS ENCONTRADOS:",
            len(documentos)
        )

        return documentos

    except Exception as e:
        print("Erro ao buscar documentos:", e)
        return []