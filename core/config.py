import os
from dotenv import load_dotenv

# Dados necessários para conexão com o Jira
# Configure suas credenciais no arquivo .env (veja .env.example)
load_dotenv()

EMAIL = os.getenv("JIRA_EMAIL", "")

# Token gerado na conta Atlassian
TOKEN = os.getenv("JIRA_TOKEN", "")

# Domínio utilizado pela empresa
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN", "")

# Prefixo do projeto/board no Jira (ex.: PROJ vira issues PROJ-123)
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "PROJ")

# Nome utilizado no assunto e corpo do e-mail
NOME_EMPRESA = os.getenv("NOME_EMPRESA", "Sua Empresa")

# Endpoint base para busca das informações dos cards
BASE_URL = (
    JIRA_DOMAIN.rstrip("/")
    + "/rest/api/3/issue/"
)
