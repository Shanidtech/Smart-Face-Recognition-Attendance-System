"""
attendance.py
-------------------------------------------------------
Live attendance screen for the Smart Face Recognition Attendance System.

It reads face profiles created by register.py, recognizes faces from the
selected camera, and writes one attendance record per student per day.
Run directly with ``python attendance.py`` or embed AttendanceFrame in the
main application.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
import cv2
import face_recognition
import numpy as np
from PIL import Image

from camera import CameraManager
from config import (
    APP_NAME,
    ATTENDANCE_FOLDER,
    ATTENDANCE_STATUS,
    DATE_FORMAT,
    DEFAULT_CAMERA,
    FACE_TOLERANCE,
    TIME_FORMAT,
)
from recognizer import FaceRecognizer
from utils import get_current_date, get_current_time, show_error, show_success, show_warning


PREVIEW_SIZE = (720, 540)
FRAME_SCALE = 0.5  # Detection on a smaller frame keeps the GUI responsive.
PROCESS_EVERY_N_FRAMES = 5
ATTENDANCE_HEADERS = ["Student ID", "Student Name", "Date", "Time", "Status"]


class AttendanceManager:
    """Stores daily CSV attendance and prevents duplicate check-ins."""

    def __init__(self, folder: str = ATTENDANCE_FOLDER) -> None:
        self.folder = Path(folder)

    def file_for_today(self) -> Path:
        """Return the daily CSV filename, creating its parent folder if needed."""
        self.folder.mkdir(parents=True, exist_ok=True)
        return self.folder / f"attendance_{get_current_date()}.csv"

    def _ensure_file(self, path: Path) -> None:
        if not path.exists():
            with path.open("w", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow(ATTENDANCE_HEADERS)

    def already_marked(self, student_id: str) -> bool:
        """Return True when the ID already has an entry in today's file."""
        path = self.file_for_today()
        self._ensure_file(path)
        with path.open("r", newline="", encoding="utf-8") as file:
            return any(row.get("Student ID") == student_id for row in csv.DictReader(file))

    def mark_present(self, student_id: str, student_name: str) -> bool:
        """Append a record once.  Returns False when it is already present."""
        path = self.file_for_today()
        self._ensure_file(path)
        if self.already_marked(student_id):
            return False
        with path.open("a", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(
                [student_id, student_name, get_current_date(), get_current_time(), ATTENDANCE_STATUS]
            )
        return True


class AttendanceFrame(ctk.CTkFrame):
    """Reusable CustomTkinter interface for recognizing and marking attendance."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_close: Optional[Callable[[], None]] = None,
        camera_source: int | str = DEFAULT_CAMERA,
    ) -> None:
        super().__init__(master)
        self.on_close = on_close
        self.camera_source = camera_source
        self.camera = CameraManager()
        self.attendance = AttendanceManager()
        self.recognizer = FaceRecognizer(tolerance=FACE_TOLERANCE)
        self.camera_running = False
        self._preview_job: Optional[str] = None
        self._preview_image: Optional[ctk.CTkImage] = None
        self._frame_number = 0
        self._latest_matches: list[tuple[tuple[int, int, int, int], str, str, bool]] = []
        self._build_interface()
        self._set_profile_status()
        self._set_close_protocol()

    def _build_interface(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            self, text="Take Attendance", font=ctk.CTkFont(size=26, weight="bold")
        ).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="w")

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, padx=24, pady=12, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            body,
            text="Start the camera to recognize registered students.",
            width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1], corner_radius=8,
        )
        self.preview_label.grid(row=0, column=0, padx=14, pady=14, sticky="nsew")

        controls = ctk.CTkFrame(body, width=260)
        controls.grid(row=0, column=1, padx=(0, 14), pady=14, sticky="ns")
        controls.grid_propagate(False)
        self.profile_var = ctk.StringVar()
        ctk.CTkLabel(controls, textvariable=self.profile_var, wraplength=220, justify="left").pack(
            padx=18, pady=(24, 20), anchor="w"
        )
        self.start_button = ctk.CTkButton(controls, text="Start Camera", command=self.start_camera)
        self.start_button.pack(padx=18, pady=8, fill="x")
        self.stop_button = ctk.CTkButton(
            controls, text="Stop Camera", state="disabled", fg_color="#a66a00", command=self.stop_camera
        )
        self.stop_button.pack(padx=18, pady=8, fill="x")
        self.reload_button = ctk.CTkButton(
            controls, text="Reload Face Profiles", command=self.reload_profiles
        )
        self.reload_button.pack(padx=18, pady=8, fill="x")
        self.close_button = ctk.CTkButton(
            controls, text="Close", fg_color="#9b2525", hover_color="#761b1b", command=self.close
        )
        self.close_button.pack(padx=18, pady=(8, 18), fill="x")

        self.status_var = ctk.StringVar(value="Camera is off.")
        ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=2, column=0, padx=24, pady=(0, 20), sticky="w"
        )

    def _set_close_protocol(self) -> None:
        try:
            self.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.close)
        except Exception:
            pass

    def _set_profile_status(self) -> None:
        count = len(self.recognizer.known_encodings)
        if count:
            self.profile_var.set(f"Loaded face profiles: {count}\n\nRecognition marks a student present only once today.")
        else:
            self.profile_var.set("No face profiles found. Register at least one student first.")

    def reload_profiles(self) -> None:
        """Refresh face data after registrations made while this screen was open."""
        try:
            self.recognizer.load_saved_encodings()
        except Exception as error:
            show_error(f"Could not load face profiles. {error}")
            return
        self._set_profile_status()
        self.status_var.set("Face profiles reloaded.")

    def start_camera(self) -> None:
        if not self.recognizer.known_encodings:
            show_warning("No registered face profiles are available. Register a student first.")
            return
        if self.camera_running:
            return
        if not self.camera.open_camera(self.camera_source):
            show_error("Unable to open the camera. Check its connection and permissions.")
            return
        self.camera_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Camera started. Look toward the camera to mark attendance.")
        self._update_preview()

    def _recognize(self, frame: np.ndarray) -> list[tuple[tuple[int, int, int, int], str, str, bool]]:
        """Find faces and return (location, id, display name, matched) tuples."""
        small_frame = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small, model="hog")
        encodings = face_recognition.face_encodings(rgb_small, locations)
        results: list[tuple[tuple[int, int, int, int], str, str, bool]] = []

        for location, encoding in zip(locations, encodings):
            name, student_id, matched = "Unknown", "", False
            if self.recognizer.known_encodings:
                distances = face_recognition.face_distance(self.recognizer.known_encodings, encoding)
                best_index = int(np.argmin(distances))
                if distances[best_index] <= self.recognizer.tolerance:
                    student_id = self.recognizer.known_ids[best_index]
                    name = self.recognizer.known_names[best_index]
                    matched = True
            top, right, bottom, left = (int(value / FRAME_SCALE) for value in location)
            results.append(((top, right, bottom, left), student_id, name, matched))
        return results

    @staticmethod
    def _draw_matches(
        frame: np.ndarray, matches: list[tuple[tuple[int, int, int, int], str, str, bool]]
    ) -> np.ndarray:
        """Draw readable recognition labels on a preview frame."""
        for (top, right, bottom, left), student_id, name, matched in matches:
            color = (45, 180, 45) if matched else (40, 40, 220)
            label = f"{name} ({student_id})" if matched else "Unknown"
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label_y = max(top - 10, 25)
            cv2.putText(frame, label, (left, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        return frame

    def _mark_matches(self) -> None:
        """Save each newly recognized student; duplicates are intentionally ignored."""
        for _, student_id, name, matched in self._latest_matches:
            if not matched:
                continue
            try:
                if self.attendance.mark_present(student_id, name):
                    self.status_var.set(f"Attendance marked: {name} ({student_id})")
                else:
                    self.status_var.set(f"Already marked today: {name} ({student_id})")
            except OSError as error:
                self.status_var.set("Could not save attendance.")
                show_error(f"Could not save attendance. {error}")

    def _update_preview(self) -> None:
        """Keep the camera preview responsive while recognizing periodically."""
        if not self.camera_running:
            return
        ok, frame = self.camera.read_frame()
        if not ok or frame is None:
            self.stop_camera()
            show_error("The camera stopped returning images.")
            return

        self._frame_number += 1
        if self._frame_number % PROCESS_EVERY_N_FRAMES == 0:
            try:
                self._latest_matches = self._recognize(frame)
                self._mark_matches()
            except Exception as error:
                self.status_var.set("Recognition could not process this frame.")
                # Keep the camera working: a single bad frame must not end the session.
                print(f"Recognition error: {error}")

        display = self._draw_matches(frame.copy(), self._latest_matches)
        display = cv2.resize(display, PREVIEW_SIZE)
        display = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        self._preview_image = ctk.CTkImage(
            light_image=Image.fromarray(display), dark_image=Image.fromarray(display), size=PREVIEW_SIZE
        )
        self.preview_label.configure(image=self._preview_image, text="")
        self._preview_job = self.after(15, self._update_preview)

    def stop_camera(self) -> None:
        """Cancel preview work and release camera resources safely."""
        self.camera_running = False
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None
        self.camera.release_camera()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._latest_matches.clear()
        self.status_var.set("Camera is off.")

    def close(self) -> None:
        """Release the camera before returning to the parent screen or closing."""
        self.stop_camera()
        if self.on_close:
            self.on_close()
        else:
            self.winfo_toplevel().destroy()


def open_attendance_window(camera_source: int | str = DEFAULT_CAMERA) -> None:
    """Run the attendance page as a standalone application window."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.title(f"{APP_NAME} - Take Attendance")
    app.geometry("1080x700")
    app.minsize(900, 600)
    AttendanceFrame(app, camera_source=camera_source).pack(fill="both", expand=True)
    app.mainloop()


if __name__ == "__main__":
    open_attendance_window()
