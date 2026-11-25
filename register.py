"""
register.py
-------------------------------------------------------
Student registration screen for the Smart Face Recognition
Attendance System.

The module collects a student's ID and name, captures several
face images from a camera, creates one stable face encoding, and
saves the student to the project's CSV/JSON data stores.

It can be started directly (``python register.py``) or embedded in
another CustomTkinter window through :class:`StudentRegistrationFrame`.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image

from camera import CameraManager
from config import (
    APP_NAME,
    DEFAULT_CAMERA,
    FACE_TOLERANCE,
    IMAGE_FOLDER,
    IMAGES_PER_STUDENT,
    REGISTRATION_POSES,
    CAPTURES_PER_POSE,
    COUNTDOWN_SECONDS,
    CAPTURE_DELAY,
    RETRY_DELAY,
    MSG_CAMERA_READY,
    MSG_CREATING_PROFILE,
)
from database import DatabaseManager
from recognizer import FaceRecognizer
from utils import (
    capitalize_name,
    remove_extra_spaces,
    show_error,
    show_success,
    show_warning,
    validate_student_id,
    validate_student_name,
)


# A face must have a reasonable size in the camera preview.  Tiny faces often
# produce inaccurate encodings even when the detector finds them.
MIN_FACE_WIDTH = 80
MIN_FACE_HEIGHT = 80
PREVIEW_SIZE = (640, 480)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class StudentRegistrationFrame(ctk.CTkFrame):
    """A reusable CustomTkinter frame that registers one student at a time.

    Parameters
    ----------
    master:
        Parent Tk/CustomTkinter widget.
    on_close:
        Optional function called after this frame has released the camera.
        A dashboard can use it to return to its previous screen.
    camera_source:
        OpenCV camera source (normally ``0`` for the laptop webcam).
    """

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
        self.database = DatabaseManager()
        self.captured_files: list[Path] = []
        self.camera_running = False
        self._preview_job: Optional[str] = None
        self._preview_image: Optional[ctk.CTkImage] = None


        self.current_pose = 0
        self.current_capture = 0
        self.countdown = COUNTDOWN_SECONDS
        self.automation_running = False
        self.countdown_job = None
        self.capture_job = None

        # Images are first captured into a unique temporary folder.  They are
        # moved into images/students/<student_id> only after registration works.
        self.temp_root = Path("images") / "temp"
        self.student_root = Path(IMAGE_FOLDER)

        self._build_interface()
        self.protocol_root_close()

    # ------------------------------------------------------------------
    # User interface
    # ------------------------------------------------------------------
    def _build_interface(self) -> None:
        """Create the form, preview area, and action buttons."""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Register a Student",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, padx=24, pady=(20, 10), sticky="w")

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, padx=(24, 12), pady=12, sticky="nsew")
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="Student ID", anchor="w").grid(
            row=0, column=0, padx=18, pady=(20, 4), sticky="ew"
        )
        self.student_id_entry = ctk.CTkEntry(
            form, width=270, placeholder_text="Example: 2026001"
        )
        self.student_id_entry.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="ew")

        ctk.CTkLabel(form, text="Student name", anchor="w").grid(
            row=2, column=0, padx=18, pady=(0, 4), sticky="ew"
        )
        self.student_name_entry = ctk.CTkEntry(
            form, width=270, placeholder_text="Example: Asha Kumar"
        )
        self.student_name_entry.grid(row=3, column=0, padx=18, pady=(0, 14), sticky="ew")

        self.start_button = ctk.CTkButton(
            form, text="Start Camera", command=self.start_camera
        )
        self.start_button.grid(row=4, column=0, padx=18, pady=(4, 8), sticky="ew")

        self.clear_button = ctk.CTkButton(
            form, text="Clear / Start Over", fg_color="#a66a00", command=self.clear_form
        )
        self.clear_button.grid(row=7, column=0, padx=18, pady=8, sticky="ew")
        self.cancel_button = ctk.CTkButton(
            form, text="Close", fg_color="#9b2525", hover_color="#761b1b", command=self.close
        )
        self.cancel_button.grid(row=8, column=0, padx=18, pady=(8, 20), sticky="ew")

        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=1, column=1, padx=(12, 24), pady=12, sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Enter the student's details, then start the camera.",
            width=PREVIEW_SIZE[0],
            height=PREVIEW_SIZE[1],
            corner_radius=8,
        )
        self.preview_label.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")


        # ---------------------------------------------------------
        # Registration Instruction
        # ---------------------------------------------------------
        self.instruction_var = ctk.StringVar(value="Press 'Start Camera'")

        self.instruction_label = ctk.CTkLabel(
            preview_frame,
            textvariable=self.instruction_var,
            font=ctk.CTkFont(size=18, weight="bold"),
            justify="center",
        )

        self.instruction_label.grid(
            row=1,
            column=0,
            padx=12,
            pady=(0, 5),
            sticky="ew",
        )
        # ---------------------------------------------------------
        # Countdown Label
        # ---------------------------------------------------------
        self.countdown_var = ctk.StringVar(value="")

        self.countdown_label = ctk.CTkLabel(
            preview_frame,
            textvariable=self.countdown_var,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="red",
        )

        self.countdown_label.grid(
            row=2,
            column=0,
            padx=12,
            pady=(0, 5),
        )





        self.status_var = ctk.StringVar(value=f"Captured: 0 / {IMAGES_PER_STUDENT}")
        self.status_label = ctk.CTkLabel(
            preview_frame, textvariable=self.status_var, font=ctk.CTkFont(size=15, weight="bold")
        )
        self.status_label.grid(
            row=3,
            column=0,
            padx=12,
            pady=(0, 12),
        )



    def protocol_root_close(self) -> None:
        """Release the camera if the enclosing top-level window is closed."""
        root = self.winfo_toplevel()
        # The standalone window owns its close protocol.  In an embedded app,
        # this still guarantees camera cleanup when the whole app exits.
        try:
            root.protocol("WM_DELETE_WINDOW", self.close)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Input and camera handling
    # ------------------------------------------------------------------
    def _student_details(self) -> tuple[Optional[str], Optional[str]]:
        """Validate and normalize the details currently entered in the form."""
        student_id = remove_extra_spaces(self.student_id_entry.get())
        name = capitalize_name(remove_extra_spaces(self.student_name_entry.get()))

        if not validate_student_id(student_id):
            show_error("Please enter a student ID.")
            self.student_id_entry.focus_set()
            return None, None
        if not validate_student_name(name):
            show_error("Please enter the student's name.")
            self.student_name_entry.focus_set()
            return None, None
        # IDs become part of a folder name.  Restricting them prevents accidental
        # path traversal and keeps the data folders portable across platforms.
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", student_id):
            show_error("Student ID may contain only letters, numbers, hyphens, and underscores.")
            self.student_id_entry.focus_set()
            return None, None
        return student_id, name

    def start_camera(self) -> None:
        """Open the selected camera after validating that this is a new student."""
        student_id, _ = self._student_details()
        if student_id is None:
            return
        if self.database.student_exists(student_id):
            show_warning("That student ID is already registered. Use a different ID.")
            return
        if self.camera_running:
            return
        if not self.camera.open_camera(self.camera_source):
            show_error("Unable to open the camera. Check its connection and camera permissions.")
            return

        self.camera_running = True
        self.start_button.configure(state="disabled")
        
        self.status_var.set(MSG_CAMERA_READY)
        self._update_preview()
        self.start_registration()


    def start_registration(self) -> None:
        """
        Starts the automatic registration workflow.
        """

        self.automation_running = True

        self.current_pose = 0
        self.current_capture = 0

        self.countdown = COUNTDOWN_SECONDS

        self.instruction_var.set(
            f"Step 1 / {len(REGISTRATION_POSES)}\n"
            f"{REGISTRATION_POSES[0]}"
        )

        self.countdown_var.set(str(self.countdown))

        self.status_var.set(MSG_CAMERA_READY)

        self.after(
            500,
            self.start_countdown
        )

    def start_countdown(self) -> None:
        """
        Starts the countdown for the current pose.
        """

        if not self.automation_running:
            return

        self.countdown = COUNTDOWN_SECONDS

        self.countdown_var.set(str(self.countdown))

        self.status_var.set(
            f"Get Ready : {REGISTRATION_POSES[self.current_pose]}"
        )

        self.countdown_job = self.after(
            1000,
            self.countdown_tick
        )


    def countdown_tick(self) -> None:
        """
        Updates the countdown every second and starts
        automatic capture when it reaches zero.
        """

        if not self.automation_running:
            return

        self.countdown -= 1

        if self.countdown > 0:

            self.countdown_var.set(str(self.countdown))

            self.countdown_job = self.after(
                1000,
                self.countdown_tick
            )

            return

        self.countdown_var.set("")

        self.status_var.set("Capturing...")

        self.capture_job = self.after(
            300,
            self.capture_pose
        )

    def capture_pose(self) -> None:
        """Capture the current pose, retrying automatically until it is valid."""
        self.capture_job = None
        if not self.automation_running:
            return

        ok, frame = self.camera.read_frame()
        if not ok or frame is None:
            self.stop_camera()
            show_error("The camera stopped returning images.")
            return

        valid, message = self._has_one_usable_face(frame)
        if not valid:
            self.status_var.set(message)
            self.countdown_var.set("")
            self.capture_job = self.after(RETRY_DELAY, self.start_countdown)
            return

        student_id, _ = self._student_details()
        if student_id is None:
            self.stop_camera()
            return

        session_dir = self.temp_root / student_id
        session_dir.mkdir(parents=True, exist_ok=True)
        pose_name = re.sub(r"[^A-Za-z0-9]+", "_", REGISTRATION_POSES[self.current_pose]).lower()
        capture_number = self.current_capture + 1
        image_path = session_dir / f"{len(self.captured_files) + 1:02d}_{pose_name}_{capture_number}.jpg"
        if not cv2.imwrite(str(image_path), frame):
            self.status_var.set("Unable to save the captured image. Retrying...")
            self.capture_job = self.after(RETRY_DELAY, self.start_countdown)
            return

        self.captured_files.append(image_path)
        self.current_capture += 1
        self.status_var.set(f"Captured: {len(self.captured_files)} / {IMAGES_PER_STUDENT}")

        if len(self.captured_files) >= IMAGES_PER_STUDENT:
            self.instruction_var.set(MSG_CREATING_PROFILE)
            self.countdown_var.set("")
            self.after(CAPTURE_DELAY, self.save_student)
            return

        if self.current_capture >= CAPTURES_PER_POSE:
            self.current_pose += 1
            self.current_capture = 0

        self.instruction_var.set(
            f"Step {self.current_pose + 1} / {len(REGISTRATION_POSES)}\n"
            f"{REGISTRATION_POSES[self.current_pose]}"
        )
        self.capture_job = self.after(CAPTURE_DELAY, self.start_countdown)



    def _update_preview(self) -> None:
        """Read one frame and schedule the next preview update without blocking Tk."""
        if not self.camera_running:
            return

        ok, frame = self.camera.read_frame()
        if not ok or frame is None:
            self.stop_camera()
            show_error("The camera stopped returning images.")
            return

        preview = cv2.resize(frame, PREVIEW_SIZE)
        preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        self._preview_image = ctk.CTkImage(
            light_image=Image.fromarray(preview), dark_image=Image.fromarray(preview), size=PREVIEW_SIZE
        )
        self.preview_label.configure(image=self._preview_image, text="")
        self._preview_job = self.after(15, self._update_preview)

    @staticmethod
    def _has_one_usable_face(frame: np.ndarray) -> tuple[bool, str]:
        """Return whether *frame* has exactly one adequately sized face."""
        try:
            import face_recognition

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")
        except Exception as error:
            return False, f"Face detection failed: {error}"

        if not locations:
            return False, "No face detected. Face the camera and try again."
        if len(locations) != 1:
            return False, "More than one face detected. Keep only one person in view."
        top, right, bottom, left = locations[0]
        if right - left < MIN_FACE_WIDTH or bottom - top < MIN_FACE_HEIGHT:
            return False, "Move a little closer to the camera, then try again."
        return True, ""


    def stop_camera(self) -> None:
        """Stop scheduled preview updates and release the OpenCV camera."""
        self.camera_running = False
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None

        if self.countdown_job is not None:
            self.after_cancel(self.countdown_job)
            self.countdown_job = None
        
        if self.capture_job is not None:
            self.after_cancel(self.capture_job)
            self.capture_job = None
        
        self.automation_running = False
        
        self.camera.release_camera()
        self.start_button.configure(state="normal")
        

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def _create_average_encoding(self) -> np.ndarray:
        """Create a normalized average encoding from every captured image.

        ``FaceRecognizer.encode_face`` rejects images containing no face or
        multiple faces.  A registration needs all requested captures to pass;
        this makes the saved profile predictable and avoids silently using an
        unexpectedly small sample.
        """
        recognizer = FaceRecognizer(tolerance=FACE_TOLERANCE)
        encodings: list[np.ndarray] = []
        for image_path in self.captured_files:
            image = recognizer.load_image(str(image_path))
            encodings.append(recognizer.encode_face(image))

        if len(encodings) != IMAGES_PER_STUDENT:
            raise ValueError(f"Exactly {IMAGES_PER_STUDENT} valid images are required.")
        average = np.mean(np.vstack(encodings), axis=0)
        norm = np.linalg.norm(average)
        if norm == 0:
            raise ValueError("Unable to create a valid face encoding.")
        return average / norm

    def _move_images_to_student_folder(self, student_id: str) -> Path:
        """Move temporary captures into the permanent student image folder."""
        target = self.student_root / student_id
        if target.exists():
            raise FileExistsError(f"Image folder already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source = self.temp_root / student_id
        shutil.move(str(source), str(target))
        return target

    def save_student(self) -> None:
        """Generate the profile, update JSON/CSV, and commit captured images."""
        student_id, student_name = self._student_details()
        if student_id is None or student_name is None:
            return
        if len(self.captured_files) != IMAGES_PER_STUDENT:
            show_warning(f"Capture all {IMAGES_PER_STUDENT} face images before saving.")
            return
        if self.database.student_exists(student_id):
            show_warning("That student ID was registered already. No data was changed.")
            return

        self.update_idletasks()
        try:
            encoding = self._create_average_encoding()
            existing = self.database.load_encodings()
            # Existing projects may have an empty dict from DatabaseManager;
            # recognizer.py expects a list of records.
            if not isinstance(existing, list):
                existing = []
            if any(record.get("student_id") == student_id for record in existing):
                raise ValueError("This student ID already has a face profile.")

            existing.append(
                {
                    "student_id": student_id,
                    "student_name": student_name,
                    "encoding": encoding.tolist(),
                }
            )

            # Write the encoding file atomically.  A power loss cannot leave a
            # half-written JSON file that prevents all future recognition.
            encoding_path = Path(self.database.encoding_file)
            encoding_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, dir=encoding_path.parent, suffix=".json"
            ) as temp_file:
                import json

                json.dump(existing, temp_file, indent=4)
                temp_name = temp_file.name
            os.replace(temp_name, encoding_path)

            self.database.save_student(student_id, student_name)
            self._move_images_to_student_folder(student_id)
        except Exception as error:
            # Captures stay in images/temp so the user can retry or inspect them.
            show_error(f"Student was not saved. {error}")
            
            return

        self.stop_camera()
        show_success(f"{student_name} ({student_id}) was registered successfully.")
        self.clear_form(release_camera=False)

    # ------------------------------------------------------------------
    # Reset and shutdown
    # ------------------------------------------------------------------
    def clear_form(self, release_camera: bool = True) -> None:
        """Discard unsaved temporary captures and reset the form for the next student."""
        if release_camera:
            self.stop_camera()
        student_id = remove_extra_spaces(self.student_id_entry.get())
        if student_id and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", student_id):
            session_dir = self.temp_root / student_id
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
        self.captured_files.clear()

        self.current_pose = 0
        self.current_capture = 0
        self.countdown = COUNTDOWN_SECONDS
        self.automation_running = False
        
        self.instruction_var.set("Press 'Start Camera'")
        self.countdown_var.set("")
        
        self.student_id_entry.delete(0, "end")
        self.student_name_entry.delete(0, "end")
        
        self.status_var.set(f"Captured: 0 / {IMAGES_PER_STUDENT}")
        self.preview_label.configure(image=None, text="Enter the student's details, then start the camera.")
        self._preview_image = None

    def close(self) -> None:
        """Release resources and close this registration screen safely."""
        self.stop_camera()
        if self.on_close:
            self.on_close()
        else:
            self.winfo_toplevel().destroy()


def open_registration_window(camera_source: int | str = DEFAULT_CAMERA) -> None:
    """Run the registration page as a standalone application window."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.title(f"{APP_NAME} - Register Student")
    app.geometry("1040x650")
    app.minsize(900, 600)
    frame = StudentRegistrationFrame(app, camera_source=camera_source)
    frame.pack(fill="both", expand=True)
    app.mainloop()


if __name__ == "__main__":
    open_registration_window()
