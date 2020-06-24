import functools
import typing
from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QAction, QWidget

from brainframe.api import bf_codecs
from brainframe.client.ui.dialogs import AboutPage, CapsuleConfigDialog, \
    RenderConfiguration, ServerConfigurationDialog
from brainframe.client.ui.main_window.activities import StreamConfiguration
from brainframe.client.ui.main_window.main_window_ui import MainWindowUI
from brainframe.client.ui.resources import stylesheet_watcher


class MainWindow(MainWindowUI):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.activity_action_map = {
            self.toolbar.stream_activity_action: self.stream_activity,
            self.toolbar.identity_activity_action: self.identity_activity,
            self.toolbar.alert_view_activity_action: self.alert_activity
        }
        self.dialog_action_map = {
            self.toolbar.capsule_config_action: CapsuleConfigDialog,
            self.toolbar.client_config_action: RenderConfiguration,
            self.toolbar.server_config_action: ServerConfigurationDialog,
            self.toolbar.about_page_action: AboutPage
        }

        self._init_signals()

        # Explicitly make the stream activity active (helps with styling)
        # Not sure why the delay is necessary
        select_stream_activity = functools.partial(
            self.change_activity, self.toolbar.stream_activity_action)
        QTimer.singleShot(0, select_stream_activity)

    def _init_signals(self) -> None:

        self._init_activity_signals()
        self._init_dialog_signals()
        self._init_sidebar_signals()

    def _init_activity_signals(self) -> None:

        for action in self.activity_action_map.keys():
            action.triggered.connect(self._handle_action_click)

    def _init_dialog_signals(self) -> None:

        for action in self.dialog_action_map.keys():
            action.triggered.connect(self._handle_action_click)

    def _init_sidebar_signals(self) -> None:

        def display_stream_configuration(
                stream_conf: Optional[bf_codecs.StreamConfiguration]):

            stream_configuration = StreamConfiguration(self)
            stream_configuration.load_from_conf(stream_conf)
            self.show_sidebar_widget(stream_configuration)

        def toggle_stream_configuration(
                stream_conf: Optional[bf_codecs.StreamConfiguration]):
            """Toggle the stream configuration if the passed stream_conf is
            the same as the displayed one"""
            sidebar_widget = self.sidebar_dock_widget.widget()
            if isinstance(sidebar_widget, StreamConfiguration) \
                    and sidebar_widget.isVisible() \
                    and sidebar_widget.stream_id == stream_conf.id:
                close_stream_configuration()
            else:
                display_stream_configuration(stream_conf)

        def close_stream_configuration():
            sidebar_widget = self.sidebar_dock_widget.widget()
            if isinstance(sidebar_widget, StreamConfiguration):
                self.close_sidebar_widget()

        def change_stream_configuration(
                stream_conf: Optional[bf_codecs.StreamConfiguration]):
            sidebar_widget = self.sidebar_dock_widget.widget()
            if not isinstance(sidebar_widget, StreamConfiguration):
                return

            sidebar_widget.load_from_conf(stream_conf)

        thumbnail_view = self.stream_activity.video_thumbnail_view
        thumbnail_view.stream_clicked.connect(change_stream_configuration)

        expanded_view = self.stream_activity.video_expanded_view
        expanded_view.toggle_stream_config_signal.connect(
            toggle_stream_configuration)
        expanded_view.stream_delete_signal.connect(
            close_stream_configuration)

        self.stream_activity.new_stream_button.clicked.connect(
            lambda: display_stream_configuration(None))

    def change_activity(self, action: QAction) -> None:
        # Change action button background
        for action_ in self.toolbar.button_actions:
            button = self.toolbar.widgetForAction(action_)

            tag = "selected" if action_ is action else "deselected"
            button.setObjectName(tag)

        # Update stylesheet because we changed object names (must force reload)
        stylesheet_watcher.update_widget(self)

        # Open activity
        widget = self.activity_action_map[action]
        self.stacked_widget.setCurrentWidget(widget)

    def close_sidebar_widget(self):
        # TODO: What happens to previous widget
        self.sidebar_dock_widget.setWidget(None)
        self.sidebar_dock_widget.hide()

    def open_dialog(self, action) -> None:
        dialog = self.dialog_action_map[action]
        dialog.show_dialog(self)

    def show_sidebar_widget(self, widget: QWidget):
        if widget is self.sidebar_dock_widget.widget():
            # Nothing to do
            return

        # Clear the current widget
        if self.sidebar_dock_widget.widget() is not None:
            self.close_sidebar_widget()

        self.sidebar_dock_widget.setWidget(widget)

        self._connect_sidebar_widget_signals()

        self.sidebar_dock_widget.show()

    def _connect_sidebar_widget_signals(self) -> None:

        sidebar_widget = self.sidebar_dock_widget.widget()

        if isinstance(sidebar_widget, StreamConfiguration):
            sidebar_widget.stream_conf_modified.connect(
                self.stream_activity.video_thumbnail_view.add_stream_conf)
            sidebar_widget.stream_conf_modified.connect(
                self._handle_stream_config_modification)

            sidebar_widget.stream_conf_deleted.connect(
                self.close_sidebar_widget)

    def _handle_stream_config_modification(
            self, stream_conf: bf_codecs.StreamConfiguration) \
            -> None:

        sidebar_widget = self.sidebar_dock_widget.widget()

        # Failsafe
        if not isinstance(sidebar_widget, StreamConfiguration):
            return

        self.stream_activity.open_expanded_view(stream_conf)

    def _handle_action_click(self) -> None:
        action = typing.cast(QAction, self.sender())
        if action in self.activity_action_map:
            self.change_activity(action)
        elif action in self.dialog_action_map:
            self.open_dialog(action)
