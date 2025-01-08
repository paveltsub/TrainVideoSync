import bisect
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtCore import QUrl
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
from PyQt6 import uic


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui.ui", self)

        # видео
        self.video_files = [
            "../data/videos/1.avi",
            "../data/videos/2.avi",
            "../data/videos/3.avi",
            "../data/videos/4.avi"
        ]
        # аннотации
        self.annotation_files = [
            "../data/annotations/1.txt",
            "../data/annotations/2.txt",
            "../data/annotations/3.txt",
            "../data/annotations/4.txt"
        ]

        self.players = []
        self.video_widgets = []
        self.scenes = []
        self.old_frame_labels = []
        self.gviews = []

        self.init_video_views_and_players()

        self.video_timestamps = []
        self.read_annotations()

        # переменные времени
        self.start_time = min(t[0] for t in self.video_timestamps)
        self.end_time = max(t[-1] for t in self.video_timestamps)
        self.current_time = self.start_time

        # частота кадров
        self.fps_base = 5.0
        self.speed_factor = 1.0

        # таймер
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.update_frames)
        self.timer_interval()

        self.is_paused = True

        self.connect_buttons()

        self.speed_combobox = self.findChild(QComboBox, "speed_combobox")
        if self.speed_combobox:
            self.speed_combobox.currentIndexChanged.connect(self.speed_change)

        self.step_forward_button = self.findChild(QPushButton, "step_forward_button")
        self.step_backward_button = self.findChild(QPushButton, "step_backward_button")
        if self.step_forward_button:
            self.step_forward_button.clicked.connect(self.step_forward)
        if self.step_backward_button:
            self.step_backward_button.clicked.connect(self.step_backward)

    # инициализация видео
    def init_video_views_and_players(self):
        for i in range(4):
            gview = self.findChild(QGraphicsView, f"graphicsView_{i+1}")
            if gview is None:
                raise ValueError(f"QGraphicsView graphicsView_{i+1} не найден в интерфейсе!")

            scene = QGraphicsScene(self)
            gview.setScene(scene)
            scene.setSceneRect(0, 0, gview.viewport().width(), gview.viewport().height())

            video_item = QGraphicsVideoItem()
            video_item.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
            video_item.setPos(0, 0)
            video_item.setSize(scene.sceneRect().size())
            scene.addItem(video_item)

            player = QMediaPlayer(self)
            player.setVideoOutput(video_item)
            player.setSource(QUrl.fromLocalFile(self.video_files[i]))

            text_item = QGraphicsTextItem("Старый кадр")
            text_item.setDefaultTextColor(QColor(Qt.GlobalColor.red))
            text_item.setPos(0, 0)
            text_item.setZValue(9999)
            text_item.setVisible(False)
            scene.addItem(text_item)

            self.scenes.append(scene)
            self.video_widgets.append(video_item)
            self.players.append(player)
            self.old_frame_labels.append(text_item)
            self.gviews.append(gview)

        self.adjust_all_views()

    # изменение размера видео
    def adjust_all_views(self):
        for i in range(4):
            gview = self.gviews[i]
            scene = self.scenes[i]
            video_item = self.video_widgets[i]

            scene.setSceneRect(0, 0, gview.viewport().width(), gview.viewport().height())
            video_item.setPos(0, 0)
            video_item.setSize(scene.sceneRect().size())
            
    # показ окна
    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_all_views()

    # чтение аннотаций
    def read_annotations(self):
        for i in range(4):
            filepath = self.annotation_files[i]
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.read().strip().split()
                timestamps = [float(x) for x in lines if x.strip()]
                self.video_timestamps.append(timestamps)

    # кнопки
    def connect_buttons(self):
        self.play_button.clicked.connect(self.play_videos)
        self.pause_button.clicked.connect(self.switch_pause)
        self.restart_button.clicked.connect(self.restart_videos)

    # изменение размера окна
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_all_views()

    # скорость воспроизведения
    def timer_interval(self):
        actual_fps = self.fps_base * self.speed_factor
        if actual_fps <= 1e-9:
            actual_fps = 1e-9
        interval_ms = int(1000 / actual_fps)
        self.sync_timer.setInterval(interval_ms)

    # изменение скорости
    def speed_change(self):
        if not self.speed_combobox:
            return
        text = self.speed_combobox.currentText()
        if text.endswith("x"):
            text = text[:-1]
        try:
            val = float(text)
        except ValueError:
            val = 1.0
        self.speed_factor = val
        self.timer_interval()

        if not self.is_paused:
            self.sync_timer.stop()
            self.sync_timer.start()

    # кнопки управления
    def play_videos(self):
        if self.is_paused:
            self.is_paused = False
        if not self.sync_timer.isActive():
            self.sync_timer.start()

    # пуск/пауза
    def switch_pause(self):
        if self.is_paused:
            self.is_paused = False
            if not self.sync_timer.isActive():
                self.sync_timer.start()
        else:
            self.is_paused = True
            if self.sync_timer.isActive():
                self.sync_timer.stop()

    # рестар видео
    def restart_videos(self):
        self.current_time = self.start_time
        self.is_paused = True
        self.sync_timer.stop()
        self.update_frames()

    # перемотка
    def step_forward(self):
        if self.sync_timer.isActive():
            self.sync_timer.stop()
            self.is_paused = True

        dt_frame = 1.0 / self.fps_base
        new_time = self.current_time + dt_frame
        if new_time > self.end_time:
            new_time = self.end_time
        self.current_time = new_time
        self.update_frames()

    # перемотка назад
    def step_backward(self):
        if self.sync_timer.isActive():
            self.sync_timer.stop()
            self.is_paused = True

        dt_frame = 1.0 / self.fps_base
        new_time = self.current_time - dt_frame
        if new_time < self.start_time:
            new_time = self.start_time
        self.current_time = new_time
        self.update_frames()

    # синхронизация кадров
    def update_frames(self):
        if self.current_time > self.end_time:
            self.sync_timer.stop()
            return

        for i in range(4):
            timestamps = self.video_timestamps[i]
            player = self.players[i]
            text_item = self.old_frame_labels[i]

            pos = bisect.bisect_right(timestamps, self.current_time)
            frame_idx = pos - 1
            if frame_idx < 0:
                frame_idx = 0

            ms_position = int(frame_idx * 1000 / self.fps_base)
            player.setPosition(ms_position)
            player.pause()

            dt_frame = 1.0 / self.fps_base
            actual_ts = timestamps[frame_idx]
            if (self.current_time - actual_ts) > 2 * dt_frame:
                text_item.setVisible(True)
            else:
                text_item.setVisible(False)

        if not self.is_paused and self.sync_timer.isActive():
            dt = 1.0 / self.fps_base
            self.current_time += dt


# запуск
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = VideoPlayer()
    window.show()
    sys.exit(app.exec())