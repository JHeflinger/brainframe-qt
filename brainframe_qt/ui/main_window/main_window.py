import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTextEdit
from PyQt5.uic import loadUi

from brainframe.client.api import api, api_errors
from brainframe.client.ui.dialogs import (
    AboutPage,
    StandardError,
    StreamConfigurationDialog,
    IdentityConfiguration
)
from brainframe.client.ui.resources.paths import image_paths, qt_ui_paths


class MainWindow(QMainWindow):
    """Main window for entire UI"""

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(qt_ui_paths.main_window_ui, self).show()

        # Add icons to buttons in toolbar
        new_stream_icon = QIcon(str(image_paths.new_stream_icon))
        configure_identities_icon = QIcon(str(image_paths.settings_gear_icon))
        about_page_icon = QIcon(str(image_paths.information_icon))
        self.add_stream_action.setIcon(new_stream_icon)
        self.configure_identity_action.setIcon(configure_identities_icon)
        self.show_about_page_action.setIcon(about_page_icon)

    @pyqtSlot()
    def show_video_expanded_view(self):
        """Called by thumbnail_view when a thumbnail is clicked"""
        self.video_layout.setStretch(0, 2)
        self.video_layout.setStretch(1, 5)

    @pyqtSlot()
    def hide_video_expanded_view(self):
        """Called by expanded_view when expanded video is closed"""
        self.video_layout.setStretch(0, 2)
        self.video_layout.setStretch(1, 0)

    @pyqtSlot()
    def new_stream(self):

        stream_conf = StreamConfigurationDialog.configure_stream()
        if stream_conf is None:
            return
        try:
            stream_conf = api.set_stream_configuration(stream_conf)

            # Currently, we default to setting all new streams as 'active'
            api.start_analyzing(stream_conf.id)

        except api_errors.DuplicateStreamSourceError as err:
            message = "<b>Stream source already open</b>" \
                      "<br><br>" \
                      "You already have the stream source open.<br><br>" \
                      "Error: <b>" + err.kind + "</b>"

            QMessageBox.information(self, "Error Opening Stream", message)
            return
        except api_errors.BaseAPIError as err:
            message = "<b>Error encountered while opening stream</b>" \
                      "<br><br>" \
                      "Is stream already open?<br>" \
                      "Is this a valid stream source?<br><br>" \
                      "Error: <b>" + err.kind + "</b>"
            QMessageBox.information(self, "Error Opening Stream", message)
            return

        self.video_thumbnail_view.new_stream_widget(stream_conf)

    @pyqtSlot()
    def show_identities_dialog(self):
        raise Exception
        IdentityConfiguration.show_dialog()

    @pyqtSlot()
    def show_about_page_dialog(self):
        AboutPage.show_dialog()

    sys.excepthook = StandardError.show_error
