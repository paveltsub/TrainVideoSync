import sys
import zmq
import numpy as np
import cv2
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap
from PyQt6.QtGui import QImage
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
from PyQt6 import uic


class VideoClient(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("client.ui", self)

        self.scenes = []
        self.pix_items = []
        self.old_labels = []
        self.views = []

        # создаем 4 сцены
        for i in range(1, 5):
            view_name = f"graphicsView_{i}"
            gview = self.findChild(QGraphicsView, view_name)

            scene = QGraphicsScene(self)
            gview.setScene(scene)

            pix_item = QGraphicsPixmapItem()
            scene.addItem(pix_item)

            text_item = scene.addText("Старый кадр")
            text_item.setDefaultTextColor(QColor(Qt.GlobalColor.red))
            text_item.setPos(10, 10)
            text_item.setZValue(9999)
            text_item.setVisible(False)

            self.scenes.append(scene)
            self.pix_items.append(pix_item)
            self.old_labels.append(text_item)
            self.views.append(gview)

        # ZMQ
        context = zmq.Context()
        self.sub_socket = context.socket(zmq.SUB)
        self.sub_socket.connect("tcp://127.0.0.1:5555")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # таймер опроса
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.receive_frames)
        self.poll_timer.start(10)

        self.fps_base = 5.0
        self.old_threshold = 2.0 / self.fps_base

    # получение кадров
    def receive_frames(self):
        try:
            parts = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
        except zmq.Again:
            return

        if len(parts) != 5:
            return

        ts_bytes = parts[0]
        frames_jpeg = parts[1:]
        ts_str = ts_bytes.decode("utf-8")
        floats = [float(x) for x in ts_str.split()]
        server_time = floats[0]
        real_ts = floats[1:]

        for i in range(4):
            jpeg_data = frames_jpeg[i]
            if not jpeg_data:
                self.pix_items[i].setPixmap(QPixmap())
                self.old_labels[i].setVisible(False)
                continue

            arr = np.frombuffer(jpeg_data, dtype=np.uint8)
            frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame_bgr is None:
                self.pix_items[i].setPixmap(QPixmap())
                self.old_labels[i].setVisible(False)
                continue

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qt_img)

            # растягиваем изображение
            gview = self.views[i]
            v_width = gview.viewport().width()
            v_height = gview.viewport().height()
            if v_width > 0 and v_height > 0:
                scaled_pix = pix.scaled(
                    v_width,
                    v_height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled_pix = pix

            self.pix_items[i].setPixmap(scaled_pix)

            # cтарый кадр
            dt = server_time - real_ts[i]
            self.old_labels[i].setVisible(dt > self.old_threshold)

    # изменение размеров окна
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for i in range(4):
            pixmap_now = self.pix_items[i].pixmap()
            if not pixmap_now.isNull():
                gview = self.views[i]
                vw = gview.viewport().width()
                vh = gview.viewport().height()
                if vw > 0 and vh > 0:
                    new_pix = pixmap_now.scaled(
                        vw, vh,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.pix_items[i].setPixmap(new_pix)

    # закрытие окна
    def closeEvent(self, event):
        self.sub_socket.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    client = VideoClient()
    client.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
