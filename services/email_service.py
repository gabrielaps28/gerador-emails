from services.jira_service import (
    ajustar_orgao
)
from core.config import NOME_EMPRESA


def gerar_email(dados):

    # Ajusta o nome do órgão para o padrão utilizado
    # nos assuntos dos e-mails
    orgao_formatado = ajustar_orgao(
        dados.get(
            'Nome do órgão',
            ''
        )
    )

    # Monta o assunto utilizando os dados do Jira
    assunto = (
        f"Indicação de Condutor - "
        f"{orgao_formatado} - "
        f"{NOME_EMPRESA} - "
        f"AIT {dados.get('AIT', '')}"
    )

    # Corpo padrão utilizado para envio
    # das indicações de condutor
    corpo = f"""
Assunto: {assunto}

Prezados,

Encaminhamos a indicação de condutor referente ao Auto de Infração nº {dados.get('AIT', '')}.

Dados do Condutor:
• Nome: {dados.get('Nome do Condutor', '')}
• CPF: {dados.get('CPF', '')}
• CNH: {dados.get('CNH', '')}

Atenciosamente,
"""

# Retorna os dados em formato de dicionário
# para a interface preencher os campos

    return {
        "assunto": assunto,
        "corpo": corpo
    }
