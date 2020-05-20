from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.uic import loadUi

from brainframe.client.api import api
from brainframe.client.api.codecs import Plugin
from brainframe.client.ui.resources import QTAsyncWorker
from brainframe.client.ui.resources.paths import qt_ui_paths

from .capsule_list_item.capsule_list_item import CapsuleListItem


class CapsuleList(QListWidget):
    plugin_selection_changed = pyqtSignal(str)
    """This is activated when the user changes the selected plugin in the
    list.

    Connected to:
    - CapsuleConfigDialog -- QtDesigner
      [peer].on_plugin_change
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        loadUi(qt_ui_paths.capsule_list_ui, self)
        self.current_plugin = None

        # noinspection PyUnresolvedReferences
        self.currentItemChanged.connect(self.plugin_changed)

        self._init_plugins()

    def _init_plugins(self):
        """Populate plugin_container layout with those plugins"""

        def get_plugins():
            return api.get_plugins()

        def add_plugins(plugins: List[Plugin]):

            for plugin in plugins:
                plugin_item = QListWidgetItem(parent=self)
                self.addItem(plugin_item)

                item_widget = CapsuleListItem(name=plugin.name, parent=self)

                # Fix sizing
                plugin_item.setSizeHint(item_widget.sizeHint())
                self.setItemWidget(plugin_item, item_widget)

            # Always have an item selected
            if plugins:
                self.setCurrentRow(0)

        QTAsyncWorker(self, get_plugins, on_success=add_plugins).start()

    def plugin_changed(self, current: QListWidgetItem,
                       _previous: QListWidgetItem):
        """When an item on the QListWidget is selected, emit a signal with
        the plugin name as the argument

        Connected to:
        - CapsuleList -- Dynamic
          self.currentItemChanged
        """
        capsule_list_item = self.itemWidget(current)
        self.current_plugin = capsule_list_item.plugin_name
        # noinspection PyUnresolvedReferences
        self.plugin_selection_changed.emit(self.current_plugin)
