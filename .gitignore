import os
import csv
import math
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import pyttsx3

CSV_FILE = "operators_db.csv"
PHOTOS_DIR = "operators"

CSV_HEADERS = [
    "id", "last_name", "first_name", "middle_name", "age",
    "date", "time", "software_start_time", "drive_duration",
    "pulse_threshold_warning", "pulse_threshold_critical", "pulse_normal",
    "current_pulse", "operator_status", "verification_result", "last_voice_command"
]

# Инициализация MediaPipe Face Mesh для детекции лица, глаз и наклона
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6
)

def speak_async(text):
    """Озвучивание текста в отдельном потоке, чтобы не зависал интерфейс"""
    def _run():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 165)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Ошибка синтеза речи: {e}")
    threading.Thread(target=_run, daemon=True).start()


class ModuleARegistration:
    def __init__(self, root):
        self.root = root
        self.root.title("Форма №1. Регистрация оператора (Модуль А)")
        self.root.geometry("950x650")

        os.makedirs(PHOTOS_DIR, exist_ok=True)

        # Состояние регистрации
        self.current_id = None
        self.first_name = ""
        self.data_saved = False
        self.photo_saved = False
        self.pulse_saved = False

        # Переменные камеры
        self.cap = None
        self.camera_running = False
        self.cam_start_time = 0
        self.last_shot_time = 0
        self.captured_shots = []

        self._build_ui()

    def _build_ui(self):
        # === БЛОК 1: Данные оператора ===
        frame_b1 = tk.LabelFrame(self.root, text="Блок 1. Данные оператора", padx=10, pady=10, font=("Arial", 10, "bold"))
        frame_b1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        tk.Label(frame_b1, text="Фамилия:").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_last = tk.Entry(frame_b1, width=25)
        self.ent_last.grid(row=0, column=1, pady=3)

        tk.Label(frame_b1, text="Имя:").grid(row=1, column=0, sticky="w", pady=3)
        self.ent_first = tk.Entry(frame_b1, width=25)
        self.ent_first.grid(row=1, column=1, pady=3)

        tk.Label(frame_b1, text="Отчество:").grid(row=2, column=0, sticky="w", pady=3)
        self.ent_middle = tk.Entry(frame_b1, width=25)
        self.ent_middle.grid(row=2, column=1, pady=3)

        tk.Label(frame_b1, text="Возраст (полных лет):").grid(row=3, column=0, sticky="w", pady=3)
        self.ent_age = tk.Entry(frame_b1, width=25)
        self.ent_age.grid(row=3, column=1, pady=3)

        self.btn_save = tk.Button(frame_b1, text="Записать", bg="#2196F3", fg="white", font=("Arial", 10, "bold"), command=self.on_save_clicked)
        self.btn_save.grid(row=4, column=0, columnspan=2, pady=10, sticky="we")

        self.lbl_id_info = tk.Label(frame_b1, text="ID оператора: не присвоен", fg="gray")
        self.lbl_id_info.grid(row=5, column=0, columnspan=2, sticky="w")

        # === БЛОК 2: Автоматическая идентификация лица ===
        frame_b2 = tk.LabelFrame(self.root, text="Блок 2. Автоматическая фиксация лица", padx=10, pady=10, font=("Arial", 10, "bold"))
        frame_b2.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.lbl_video = tk.Label(frame_b2, text="Видеопоток не активен\n(Нажмите «Записать»)", width=55, height=18, bg="#e0e0e0")
        self.lbl_video.pack(pady=5)

        self.lbl_cam_status = tk.Label(frame_b2, text="Ожидание активации...", fg="gray", font=("Arial", 9))
        self.lbl_cam_status.pack(pady=3)

        self.btn_retry_face = tk.Button(frame_b2, text="Повторить захват лица", state="disabled", command=self.start_camera_block)
        self.btn_retry_face.pack(pady=5)

        # === БЛОК 3: Измерение пульса (Arduino) ===
        frame_b3 = tk.LabelFrame(self.root, text="Блок 3. Измерение пульса (30 сек)", padx=10, pady=10, font=("Arial", 10, "bold"))
        frame_b3.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.lbl_port = tk.Label(frame_b3, text="COM-порт: поиск не запущен")
        self.lbl_port.pack(anchor="w")

        self.progress_pulse = ttk.Progressbar(frame_b3, orient="horizontal", length=280, mode="determinate", maximum=30)
        self.progress_pulse.pack(pady=8)

        self.lbl_pulse_results = tk.Label(
            frame_b3,
            text="Норма (pulse_normal): —\nПорог внимания (warning): —\nКритический порог (critical): —",
            justify="left", font=("Arial", 9)
        )
        self.lbl_pulse_results.pack(anchor="w", pady=5)

        # Чекбокс подстраховки (эмуляция сигнала, если плата не подключена)
        self.use_sim_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_b3, text="Эмуляция датчика при отсутствии COM-порта", variable=self.use_sim_var).pack(anchor="w")

        self.btn_remeasure = tk.Button(frame_b3, text="Перемерить", state="disabled", command=self.start_pulse_block)
        self.btn_remeasure.pack(fill="x", pady=5)

        # === БЛОК 4: Завершение регистрации ===
        frame_b4 = tk.Frame(self.root, padx=10, pady=10)
        frame_b4.grid(row=2, column=0, columnspan=2, sticky="we")

        self.btn_finish = tk.Button(
            frame_b4, text="Завершить регистрацию", bg="#4CAF50", fg="white",
            font=("Arial", 12, "bold"), height=2, state="disabled", command=self.on_finish_clicked
        )
        self.btn_finish.pack(fill="x")

    # -------------------------------------------------------------------------
    # ЛОГИКА БЛОКА 1: Валидация и создание записи в CSV
    # -------------------------------------------------------------------------
    def on_save_clicked(self):
        last_name = self.ent_last.get().strip()
        first_name = self.ent_first.get().strip()
        middle_name = self.ent_middle.get().strip()
        age_str = self.ent_age.get().strip()

        if not (last_name and first_name and middle_name and age_str):
            messagebox.showwarning("Внимание", "Пожалуйста, заполните все поля ФИО и возраст!")
            return

        try:
            age = int(age_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Возраст должен быть целым числом!")
            return

        if age < 18:
            messagebox.showerror("Ошибка", "Возраст должен быть не менее 18 лет")
            return

        # Автоинкремент ID
        file_exists = os.path.isfile(CSV_FILE)
        new_id = 1
        if file_exists:
            with open(CSV_FILE, mode="r", encoding="utf-8") as f:
                rows = list(csv.reader(f))
                if len(rows) > 1:
                    try:
                        new_id = int(rows[-1][0]) + 1
                    except ValueError:
                        new_id = len(rows)

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        row_data = [
            new_id, last_name, first_name, middle_name, age,
            date_str, time_str, "—", "—",
            "—", "—", "—",
            "—", "—", "—", "—"
        ]

        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(CSV_HEADERS)
            writer.writerow(row_data)

        self.current_id = new_id
        self.first_name = first_name
        self.data_saved = True

        # Блокируем повторный ввод ФИО
        for ent in (self.ent_last, self.ent_first, self.ent_middle, self.ent_age):
            ent.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.lbl_id_info.config(text=f"ID оператора: {new_id} (сохранено в {CSV_FILE})", fg="green")

        # Последовательно запускаем Блок 2 (фото), а после него запустится Блок 3 (пульс)
        self.start_camera_block()

    # -------------------------------------------------------------------------
    # ЛОГИКА БЛОКА 2: Детекция лица, 3-5 снимков, выбор лучшего
    # -------------------------------------------------------------------------
    def analyze_frame(self, frame):
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        if not res.multi_face_landmarks:
            return None

        lm = res.multi_face_landmarks[0].landmark
        pts = [(int(p.x * w), int(p.y * h)) for p in lm]

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x1, x2 = max(0, min(xs)), min(w, max(xs))
        y1, y2 = max(0, min(ys)), min(h, max(ys))

        face_ratio = (x2 - x1) / float(w)

        # Проверка открытости глаз (EAR)
        def calc_ear(top, bot, left, right):
            v = np.linalg.norm(np.array(pts[top]) - np.array(pts[bot]))
            hz = np.linalg.norm(np.array(pts[left]) - np.array(pts[right]))
            return v / (hz + 1e-6)

        ear_l = calc_ear(159, 145, 33, 133)
        ear_r = calc_ear(386, 374, 362, 263)
        eyes_open = (ear_l > 0.19) and (ear_r > 0.19)

        # Наклон головы (Roll) и прямой взгляд (Yaw)
        l_eye, r_eye, nose = np.array(pts[33]), np.array(pts[263]), np.array(pts[1])
        dy, dx = r_eye[1] - l_eye[1], r_eye[0] - l_eye[0]
        roll = abs(np.degrees(np.arctan2(dy, dx)))

        yaw_diff = abs(abs(nose[0] - l_eye[0]) - abs(r_eye[0] - nose[0])) / (dx + 1e-6)

        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size > 0:
            gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray_roi, cv2.CV_64F).var()
        else:
            sharpness = 0.0

        is_stable = (0.18 <= face_ratio <= 0.70) and eyes_open and (roll < 15.0) and (yaw_diff < 0.28)

        return {
            "bbox": (x1, y1, x2, y2),
            "is_stable": is_stable,
            "sharpness": sharpness,
            "roll": roll
        }

    def start_camera_block(self):
        self.btn_retry_face.config(state="disabled")
        self.captured_shots = []
        self.photo_saved = False
        self.check_finish_ready()

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Ошибка", "Лицо не обнаружено. Убедитесь, что камера работает, и повторите попытку")
            self.btn_retry_face.config(state="normal")
            return

        self.camera_running = True
        self.cam_start_time = time.time()
        self.last_shot_time = 0
        self.update_camera_loop()

    def update_camera_loop(self):
        if not self.camera_running:
            return

        ret, frame = self.cap.read()
        elapsed = time.time() - self.cam_start_time

        # Если за 10 секунд не сняли нужные кадры — ошибка по ТЗ
        if elapsed > 10.0 and len(self.captured_shots) < 3:
            self.stop_camera()
            self.lbl_cam_status.config(text="Ошибка: Лицо не обнаружено за 10 секунд!", fg="red")
            messagebox.showerror("Ошибка", "Лицо не обнаружено. Убедитесь, что камера работает, и повторите попытку")
            self.btn_retry_face.config(state="normal")
            return

        if ret:
            clean_frame = frame.copy()
            info = self.analyze_frame(frame)

            if info:
                # Если лицо найдено — продлеваем таймер ожидания, чтобы не оборвать на полуслове
                self.cam_start_time = time.time()
                x1, y1, x2, y2 = info["bbox"]
                color = (0, 255, 0) if info["is_stable"] else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                if info["is_stable"] and (time.time() - self.last_shot_time >= 0.5):
                    self.captured_shots.append({
                        "frame": clean_frame,
                        "sharpness": info["sharpness"],
                        "roll": info["roll"]
                    })
                    self.last_shot_time = time.time()

                self.lbl_cam_status.config(
                    text=f"Кадров: {len(self.captured_shots)}/5 | Чёткость: {info['sharpness']:.0f} | Наклон: {info['roll']:.1f}°",
                    fg="green" if info["is_stable"] else "#FF8C00"
                )
            else:
                self.lbl_cam_status.config(
                    text=f"Поиск лица... ({max(0, int(10 - elapsed))} сек до таймаута)", fg="red"
                )

            # Вывод в окно Tkinter
            disp = cv2.cvtColor(cv2.resize(frame, (440, 330)), cv2.COLOR_BGR2RGB)
            img_tk = ImageTk.PhotoImage(image=Image.fromarray(disp))
            self.lbl_video.imgtk = img_tk
            self.lbl_video.config(image=img_tk, width=440, height=330)

            # Когда сделано 5 снимков — выбираем лучший
            if len(self.captured_shots) >= 5:
                self.stop_camera()
                best = max(self.captured_shots, key=lambda x: x["sharpness"] - (x["roll"] * 5))
                photo_filename = os.path.join(PHOTOS_DIR, f"ID_{self.current_id:05d}.jpg")
                cv2.imwrite(photo_filename, best["frame"])

                self.photo_saved = True
                self.lbl_cam_status.config(text=f"Лучший снимок сохранён: {photo_filename}", fg="blue")
                self.btn_retry_face.config(state="normal")
                self.check_finish_ready()

                # Автоматически запускаем Блок 3 (Пульс), если он ещё не измерен
                if not self.pulse_saved:
                    self.start_pulse_block()
                return

        self.root.after(30, self.update_camera_loop)

    def stop_camera(self):
        self.camera_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()

    # -------------------------------------------------------------------------
    # ЛОГИКА БЛОКА 3: Автопоиск COM-порта и замер пульса 30 секунд
    # -------------------------------------------------------------------------
    def find_arduino_port(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.description or "").lower()
            if any(k in desc for k in ["arduino", "ch340", "usb", "serial", "cp210"]):
                return p.device
        return ports[0].device if ports else None

    def start_pulse_block(self):
        self.btn_remeasure.config(state="disabled")
        self.pulse_saved = False
        self.check_finish_ready()
        self.progress_pulse["value"] = 0
        threading.Thread(target=self._pulse_worker, daemon=True).start()

    def _pulse_worker(self):
        port = self.find_arduino_port()
        ser = None
        if port:
            try:
                ser = serial.Serial(port, 9600, timeout=1)
                self.root.after(0, lambda: self.lbl_port.config(text=f"COM-порт: подключено ({port})", fg="green"))
            except Exception:
                ser = None

        if ser is None and not self.use_sim_var.get():
            self.root.after(0, lambda: self.lbl_port.config(text="COM-порт: устройство не найдено!", fg="red"))
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", "Не удалось измерить пульс. Проверьте подключение Arduino и датчика"
            ))
            self.root.after(0, lambda: self.btn_remeasure.config(state="normal"))
            return

        if ser is None:
            self.root.after(0, lambda: self.lbl_port.config(text="COM-порт: режим эмуляции (тест)", fg="orange"))

        bpm_values = []
        start_t = time.time()

        # Измерение ровно 30 секунд с обновлением прогресс-бара
        while time.time() - start_t < 30.0:
            elapsed = time.time() - start_t
            self.root.after(0, lambda v=elapsed: self.progress_pulse.config(value=v))

            if ser:
                try:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    # Парсим строки формата "BPM: 72" или просто числа
                    if "BPM:" in line:
                        val = int(line.split("BPM:")[1].strip())
                        if 40 <= val <= 200:
                            bpm_values.append(val)
                    elif line.isdigit():
                        val = int(line)
                        if 40 <= val <= 200:
                            bpm_values.append(val)
                except Exception:
                    pass
            else:
                # Тестовая генерация пульса в районе 72-76 уд/мин
                bpm_values.append(int(np.random.normal(74, 2)))
                time.sleep(0.5)

        if ser:
            ser.close()

        self.root.after(0, lambda: self.progress_pulse.config(value=30))

        if not bpm_values:
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", "Не удалось измерить пульс. Проверьте подключение Arduino и датчика"
            ))
            self.root.after(0, lambda: self.btn_remeasure.config(state="normal"))
            return

        # Точные формулы из Таблицы №1 Модуля А:
        pulse_normal = round(sum(bpm_values) / len(bpm_values))
        pulse_warning = math.ceil(pulse_normal * 1.15)
        pulse_critical = math.ceil(pulse_normal * 1.30)

        self.update_csv_pulse(pulse_normal, pulse_warning, pulse_critical)
        self.pulse_saved = True

        res_text = (
            f"Норма (pulse_normal): {pulse_normal} уд/мин\n"
            f"Порог внимания (warning): {pulse_warning} уд/мин\n"
            f"Критический порог (critical): {pulse_critical} уд/мин"
        )
        self.root.after(0, lambda: self.lbl_pulse_results.config(text=res_text, fg="green"))
        self.root.after(0, lambda: self.btn_remeasure.config(state="normal"))
        self.root.after(0, self.check_finish_ready)

    def update_csv_pulse(self, normal, warning, critical):
        """Записывает рассчитанные пороги в строку текущего id в operators_db.csv"""
        if not os.path.isfile(CSV_FILE):
            return
        with open(CSV_FILE, mode="r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        for i in range(1, len(rows)):
            if rows[i] and int(rows[i][0]) == self.current_id:
                rows[i][9] = str(warning)   # pulse_threshold_warning
                rows[i][10] = str(critical) # pulse_threshold_critical
                rows[i][11] = str(normal)   # pulse_normal
                break

        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    # -------------------------------------------------------------------------
    # ЛОГИКА БЛОКА 4: Активация кнопки завершения и синтез речи
    # -------------------------------------------------------------------------
    def check_finish_ready(self):
        if self.data_saved and self.photo_saved and self.pulse_saved:
            self.btn_finish.config(state="normal")
        else:
            self.btn_finish.config(state="disabled")

    def on_finish_clicked(self):
        msg = f"Регистрация завершена, {self.first_name}. Теперь вы можете авторизоваться."
        speak_async(msg)
        messagebox.showinfo("Завершение", msg)
        # Здесь можно закрыть текущее окно или открыть Форму №2 (Модуль Б)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModuleARegistration(root)
    root.mainloop()