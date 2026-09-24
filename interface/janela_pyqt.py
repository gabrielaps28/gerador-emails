import os
import json
import requests  # <-- ADICIONADO PARA TRATAR OS ERROS DE CONEXÃO E CARD NÃO ENCONTRADO
import time

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QLineEdit,
    QTextEdit,
    QFileDialog
)

from services.jira_email_services import gerar_email
from PyQt5.QtCore import Qt, QMimeData, QUrl
from PyQt5.QtGui import QDrag

from services.drive_service import buscar_documentos

# =========================
# LISTA DE ARQUIVOS
# =========================
class ListaArquivos(QListWidget):

    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)

    def startDrag(self, supportedActions):
        items = self.selectedItems()
        if not items:
            return

        urls = []
        for item in items:
            caminho = item.data(Qt.UserRole)
            if caminho and os.path.exists(caminho):
                urls.append(QUrl.fromLocalFile(caminho))

        if not urls:
            return

        mime = QMimeData()
        mime.setUrls(urls)

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.CopyAction)


# =========================
# JANELA PRINCIPAL
# =========================
class JanelaPrincipal(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gerador de E-mail")
        self.resize(1200, 700)

        layout = QVBoxLayout()

        # --- BARRA SUPERIOR (CARD, BUSCAR E CONFIGURAR) ---
        topo = QHBoxLayout()

        self.card = QLineEdit()
        self.card.setPlaceholderText("Digite o card")

        botao_buscar = QPushButton("Buscar")
        botao_buscar.clicked.connect(self.buscar)

        # O botão no canto para configurar a rota a qualquer momento
        self.botao_config = QPushButton("⚙️ Configurar Rota")
        self.botao_config.clicked.connect(self.configurar_rota)

        topo.addWidget(QLabel("Card:"))
        topo.addWidget(self.card)
        topo.addWidget(botao_buscar)
        topo.addWidget(self.botao_config) # Adiciona o botão no canto direito superior

        layout.addLayout(topo)

        # Área principal do sistema
        conteudo = QHBoxLayout()

        # Lista onde serão exibidos os documentos
        self.lista_docs = ListaArquivos()
        self.lista_docs.doubleClicked.connect(self.abrir_arquivo)

        conteudo.addWidget(self.lista_docs, 1)
        layout.addLayout(conteudo)

        # Campo do assunto do e-mail
        self.assunto_label = QLabel("Assunto:")
        self.assunto_field = QLineEdit()
        self.assunto_field.setReadOnly(True)

        self.btn_copy_assunto = QPushButton("📋 Copiar")
        self.btn_copy_assunto.clicked.connect(
            lambda: QApplication.clipboard().setText(self.assunto_field.text())
        )

        layout.addWidget(self.assunto_label)

        linha_assunto = QHBoxLayout()
        linha_assunto.addWidget(self.assunto_field)
        linha_assunto.addWidget(self.btn_copy_assunto)
        layout.addLayout(linha_assunto)

        # Campo do corpo do e-mail
        self.corpo_label = QLabel("Corpo do e-mail:")
        self.corpo_field = QTextEdit()
        self.corpo_field.setReadOnly(True)

        self.btn_copy_corpo = QPushButton("📋 Copiar")
        self.btn_copy_corpo.clicked.connect(
            lambda: QApplication.clipboard().setText(self.corpo_field.toPlainText())
        )

        layout.addWidget(self.corpo_label)

        linha_corpo = QHBoxLayout()
        linha_corpo.addWidget(self.corpo_field)
        linha_corpo.addWidget(self.btn_copy_corpo)
        layout.addLayout(linha_corpo)

        self.setLayout(layout)

    def configurar_rota(self):
        """ Abre o explorador de arquivos para definir ou alterar a rota das indicações """
        config_local = "config_rota_indicacoes.json"

        # Abre a tela para escolher a pasta
        rota_selecionada = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Rota das Indicações e Documentos",
            os.path.expanduser("~")
        )

        if rota_selecionada:
            # Salva o caminho no arquivo JSON local
            with open(config_local, "w", encoding="utf-8") as f:
                json.dump({"rota_sistema": rota_selecionada}, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(self, "Sucesso", f"Rota configurada com sucesso!\n\nCaminho: {rota_selecionada}")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma pasta foi selecionada.")

    # Busca os documentos do card informado
    def buscar(self):
        try:
            card = self.card.text().strip()
            if not card:
                QMessageBox.warning(self, "Aviso", "Por favor, digite o número do card.")
                return

            config_local = "config_rota_indicacoes.json"
            
            # Trava de segurança: Se a pessoa clicar em Buscar e NUNCA tiver configurado a rota antes
            if not os.path.exists(config_local):
                QMessageBox.warning(
                    self, 
                    "Aviso de Rota", 
                    "Você ainda não configurou a rota dos documentos.\n\nPor favor, clique no botão '⚙️ Configurar Rota' no canto superior direito para selecionar a pasta."
                )
                return

            # Executa a busca normal dos documentos e do Jira
            # Executa a busca normal dos documentos e do Jira
            # Executa a busca normal dos documentos e do Jira
            inicio = time.time()

            docs = buscar_documentos(card)

            print(
                f"Tempo busca documentos: {time.time() - inicio:.2f}s"
            )

            self.lista_docs.clear()

            if docs:
                for doc in docs:
                    item = QListWidgetItem(doc["nome"])
                    item.setData(Qt.UserRole, doc["caminho"])
                    self.lista_docs.addItem(item)
            else:
                self.lista_docs.addItem("Nenhum documento encontrado")

            # Busca os dados do Jira e gera o e-mail
            email = gerar_email(card)

            print("EMAIL RETORNADO:")
            print(email)

            self.assunto_field.setText(email["assunto"])
            self.corpo_field.setPlainText(email["corpo"])

        except requests.exceptions.HTTPError as http_err:
            # --- NOVO BLOCO: DETECTA SE O CARD NÃO EXISTE NO JIRA ---
            status = http_err.response.status_code
            if status == 404:
                QMessageBox.warning(
                    self, 
                    "Card Não Encontrado", 
                    f"O card '{card}' não foi encontrado no sistema Jira.\n\nVerifique se digitou o número corretamente."
                )
            elif status == 401:
                QMessageBox.critical(
                    self, 
                    "Erro de Autenticação", 
                    "Não foi possível acessar o Jira. Verifique se o seu Token ou E-mail estão corretos no arquivo .env."
                )
            else:
                QMessageBox.critical(
                    self, 
                    "Erro no Sistema", 
                    f"Ocorreu um erro de rede com o Jira (Status: {status})."
                )

        except Exception as e:
            # Captura qualquer outra falha genérica
            QMessageBox.critical(
                self,
                "Erro Inesperado",
                f"Não foi possível processar a busca.\n\nDetalhes: {str(e)}"
            )

    # Abre o arquivo ao dar duplo clique
    def abrir_arquivo(self):
        item = self.lista_docs.currentItem()
        if not item:
            return

        caminho = item.data(Qt.UserRole)
        if caminho and os.path.exists(caminho):
            os.startfile(caminho)
