import os
import json
import sys
from tkinter import Tk, filedialog

CONFIG_FILE = os.path.join(
    os.path.expanduser("~"),
    "config_drive.json"
)


def obter_pasta_drive():

    # Evita janela escondida no EXE
    root = Tk()
    root.withdraw()

    if os.path.exists(CONFIG_FILE):

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        pasta = dados.get("pasta_drive")

        if pasta and os.path.exists(pasta):
            return pasta

    pasta = filedialog.askdirectory(
        title="Selecione a pasta raiz do Drive"
    )

    if not pasta:
        return None

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"pasta_drive": pasta},
            f,
            indent=4,
            ensure_ascii=False
        )

    return pasta
