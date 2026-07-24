from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget


class BasePopupModule(QDialog):
    """
    Base para todo módulo aberto em pop-up (conforme especificação: "sempre
    que um módulo for fechado, o sistema descarrega todos os dados e evita
    ficar lento com diversas informações carregadas").

    Também resolve o problema de telas com muitos campos ficarem maiores
    que a altura da tela do usuário: todo o conteúdo é automaticamente
    colocado dentro de uma QScrollArea, então nada fica cortado/inacessível
    — o usuário rola a tela (ou usa a roda do mouse) para ver o restante.

    Cada tela filha deve sobrescrever `descarregar_dados()` para limpar
    listas/caches específicos dela (ex.: resultados de busca, mídias
    carregadas em memória, etc). O QDialog em si já libera seus widgets
    Qt ao ser fechado com `deleteOnClose`; este hook cobre estruturas
    Python (listas, DataFrames, bytes de imagem) que não seriam
    liberadas automaticamente.
    """

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(parent)
        self.usuario_logado = usuario_logado
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        # Estrutura de rolagem: outer_layout (fixo no QDialog) > QScrollArea
        # > _content_widget (cresce livremente) > content_layout (o que as
        # subclasses usam para montar a tela).
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer_layout.addWidget(scroll)

        self._content_widget = QWidget()
        scroll.setWidget(self._content_widget)

        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(20, 20, 20, 20)

    def content_layout(self) -> QVBoxLayout:
        """
        Layout onde a tela filha deve montar seu conteúdo, em vez de
        `QVBoxLayout(self)`. Fica dentro de uma área rolável, então
        formulários longos nunca ficam cortados pela altura da tela.
        """
        return self._content_layout

    def descarregar_dados(self):
        """Sobrescrever nas subclasses para liberar dados carregados em memória."""
        pass

    def closeEvent(self, event):
        self.descarregar_dados()
        super().closeEvent(event)
