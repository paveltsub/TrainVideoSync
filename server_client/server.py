import zmq
import cv2
import time
import bisect

class VideoServer:
    def __init__(self, video_files, annotation_files, fps_base=5.0):
        self.video_files = video_files
        self.annotation_files = annotation_files
        self.fps_base = fps_base

        self.captures = []
        self.video_timestamps = []
        self.start_time = None
        self.end_time = None
        self.current_time = None

        self.load_videos()
        self.read_annotations()

        # находим общее время начала и конца
        self.start_time = min(ts[0] for ts in self.video_timestamps)
        self.end_time   = max(ts[-1] for ts in self.video_timestamps)
        self.current_time = self.start_time

    # загрузка видео
    def load_videos(self):
        for path in self.video_files:
            cap = cv2.VideoCapture(path)
            self.captures.append(cap)

    # чтение аннотаций
    def read_annotations(self):
        for path in self.annotation_files:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().strip().split()
                timestamps = [float(x) for x in lines if x.strip()]
                self.video_timestamps.append(timestamps)
                
    # генератор кадров
    def generate_frames(self, speed_factor=1.0):
        dt_sec = 1.0 / self.fps_base
        dt_scaled = dt_sec / speed_factor

        while self.current_time <= self.end_time:
            frames = []
            real_ts = []

            for i in range(4):
                timestamps = self.video_timestamps[i]
                cap = self.captures[i]

                pos = bisect.bisect_right(timestamps, self.current_time)
                frame_idx = pos - 1
                if frame_idx < 0:
                    frame_idx = 0

                # cтавим на нужный кадр
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    frame = None

                frames.append(frame)
                real_ts.append(timestamps[frame_idx])

            # отдаём пачку кадров и метки времени
            yield frames, real_ts

            self.current_time += dt_scaled

    # закрытие видео
    def close(self):
        for cap in self.captures:
            cap.release()


def main():
    video_files = [
        "../data/videos/1.avi",
        "../data/videos/2.avi",
        "../data/videos/3.avi",
        "../data/videos/4.avi"
    ]
    annotation_files = [
        "../data/annotations/1.txt",
        "../data/annotations/2.txt",
        "../data/annotations/3.txt",
        "../data/annotations/4.txt"
    ]

    # cоздаём сервер
    server = VideoServer(video_files, annotation_files, fps_base=5.0)

    # настраиваем ZMQ
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind("tcp://*:5555")

    speed_factor = 1.0  # базовая скорость

    # генерируем кадры и отправляем их
    try:
        for frames, real_ts in server.generate_frames(speed_factor):
            # подготавливаем 4 кадра к отправке (JPEG)
            msg_frames = []
            for fr in frames:
                if fr is None:
                    msg_frames.append(b"")
                else:
                    ret, encoded = cv2.imencode(".jpg", fr)
                    if not ret:
                        msg_frames.append(b"")
                    else:
                        msg_frames.append(encoded.tobytes())

            server_time_str = str(server.current_time)
            real_ts_str = " ".join(str(ts) for ts in real_ts)
            full_str = f"{server_time_str} {real_ts_str}"
            ts_bytes = full_str.encode("utf-8")

            pub_socket.send_multipart([ts_bytes] + msg_frames)

            time.sleep(0.001)

    finally:
        server.close()
        pub_socket.close()
        context.term()


if __name__ == "__main__":
    main()