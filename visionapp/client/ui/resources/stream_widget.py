# noinspection PyUnresolvedReferences
# pyqtProperty is erroneously detected as unresolved
from PyQt5.QtCore import pyqtProperty, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

from visionapp.client.ui.resources.paths import image_paths


# TODO
# from [] import Stream


class StreamWidget(QGraphicsView):
    """Base widget that uses Stream object to get frames

    Makes use of a QTimer to get frames"""

    def __init__(self, stream_conf=None, frame_rate=30, parent=None):
        """Init StreamWidget object

        :param frame_rate: Frame rate of video in fps
        """
        super().__init__(parent)

        # Remove ugly white background and border from QGraphicsView
        self.setStyleSheet("background-color: transparent; border: 0px")

        self.stream_conf = None
        self.stream_id = None

        self.scene_ = QGraphicsScene()
        self.setScene(self.scene_)

        self.current_frame = None
        self.change_stream(stream_conf)

        self.video_stream = None  # TODO: StreamReader()

        self._frame_rate = frame_rate

        # Get first frame, then start timer to do it repetitively
        self.update_frame()
        self.frame_update_timer = QTimer()

        # noinspection PyUnresolvedReferences
        # .connect is erroneously detected as unresolved
        self.frame_update_timer.timeout.connect(self.update_frame)
        self.frame_update_timer.start(1000 // frame_rate)

    def update_frame(self):
        """Grab the newest frame from the Stream object"""

        # TODO: Use Stream frame
        if not self.current_frame:
            self.current_frame = self.scene_.addPixmap(self._pixmap_temp)
        else:
            self.current_frame.setPixmap(self._pixmap_temp)
        self.fitInView(self.scene_.itemsBoundingRect(), Qt.KeepAspectRatio)

    # TODO
    def change_stream(self, stream_conf):
        """Change the stream source of the video

        If stream_conf is None, the StreamWidget will stop grabbing frames"""
        self.stream_conf = stream_conf
        self.stream_id = stream_conf.id if stream_conf else None

        for item in self.scene_.items():
            self.scene_.removeItem(item)
            self.current_frame = None

        # TODO: Without caching this, UI gets laggy. This might be an issue
        # It might also be because of the IO read. If the frame is from a video
        # object
        try:
            # TODO: Remove ast dependency
            import ast
            params = ast.literal_eval(stream_conf.parameters)
            self._pixmap_temp = QPixmap(str(params["filepath"]))
        except AttributeError:
            # TODO: Don't hardcode path
            self._pixmap_temp = QPixmap(str(image_paths.video_not_found))

    @pyqtProperty(int)
    def frame_rate(self):
        return self._frame_rate

    @frame_rate.setter
    def frame_rate(self, frame_rate):
        self.frame_update_timer.setInterval(1000 // frame_rate)
        self._frame_rate = frame_rate