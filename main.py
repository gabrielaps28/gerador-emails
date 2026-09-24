import sys
import traceback
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from interface.janela_pyqt import JanelaPrincipal


app = QApplication(sys.argv)

janela = JanelaPrincipal()

janela.show()

sys.exit(app.exec_())
