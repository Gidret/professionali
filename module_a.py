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

#Инициализируем MediaPipe Face Mesh для детекции лица, глаз и наклона
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image = False,
    max_num_faces = 1,
    refune_landmarks = True,
    min_detection_confidence = 0.6
)

def speak_async(text):
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

        #Состояние регистрации
        self.curren_id = None
        self.firs_name = ""
        self.data_saved = False
        self.photo_saved = False
        self.pulse_saved = False

        #Параметры камеры
        self.cap = None
        self.camera_running = False
        self.cam_start_time = 0
        self.last_shot_time = 0
        self.captured_shots = []

        self.build_ui()

    def _builf_ui(self):
