"""
config.py
-------------------------------------------------------
Project Configuration File

Purpose:
    Stores all project settings, constants,
    folder paths, and application configuration.

Author: Shanid
"""

# ==========================================================
# APPLICATION INFORMATION
# ==========================================================

# Name of the application
APP_NAME = "Smart Face Recognition Attendance System"

# Application version
APP_VERSION = "1.0.0"

# ==========================================================
# WINDOW SETTINGS
# ==========================================================

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

MIN_WIDTH = 1000
MIN_HEIGHT = 600

# ==========================================================
# THEME SETTINGS
# ==========================================================

# Options:
# "Light"
# "Dark"
# "System"

APPEARANCE_MODE = "System"

# Themes:
# "blue"
# "green"
# "dark-blue"

THEME = "blue"

# ==========================================================
# ADMIN SETTINGS
# ==========================================================

import os

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# ==========================================================
# CAMERA SETTINGS
# ==========================================================

# Laptop Camera
DEFAULT_CAMERA = 0

# USB Camera
USB_CAMERA = 1

# IP Camera URL
IP_CAMERA_URL = ""

# Camera Resolution
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ==========================================================
# FACE RECOGNITION SETTINGS
# ==========================================================

# Number of images captured for each student
IMAGES_PER_STUDENT = 5

# Face Recognition Threshold
FACE_TOLERANCE = 0.50

# Detection Model
# "hog" = Faster (CPU)
# "cnn" = More Accurate (GPU)
FACE_DETECTION_MODEL = "hog"

# ==========================================================
# REGISTRATION SETTINGS
# ==========================================================

# Registration pose order
REGISTRATION_POSES = [

    "Look Straight",
    "Turn Left",
    "Turn Right",
    "Look Up",
    "Look Down"

]

# Number of photos captured for every pose
CAPTURES_PER_POSE = 1

# Countdown before automatic capture
COUNTDOWN_SECONDS = 2

# Gap between two captures
CAPTURE_DELAY = 500     # milliseconds

# Retry delay when no valid face found
RETRY_DELAY = 1000      # milliseconds


# ==========================================================
# FACE VALIDATION
# ==========================================================

MIN_FACE_WIDTH = 80

MIN_FACE_HEIGHT = 80

MAX_FACES = 1


# ==========================================================
# CAMERA PREVIEW
# ==========================================================

PREVIEW_WIDTH = 640

PREVIEW_HEIGHT = 480

# ==========================================================
# STATUS MESSAGES
# ==========================================================

MSG_CAMERA_READY = "Camera Ready"

MSG_FACE_NOT_FOUND = "No face detected"

MSG_MULTIPLE_FACE = "Only one face should be visible"

MSG_MOVE_CLOSER = "Move closer to the camera"

MSG_CREATING_PROFILE = "Creating face profile..."

MSG_SAVING = "Saving student..."

MSG_SUCCESS = "Student Registered Successfully"

MSG_RESET = "Ready for Next Student"




# ==========================================================
# PROJECT FOLDERS
# ==========================================================

IMAGE_FOLDER = "images/students"

TEMP_FOLDER = "images/temp"

ENCODING_FOLDER = "encodings"

DATABASE_FOLDER = "database"

ATTENDANCE_FOLDER = "attendance"

REPORT_FOLDER = "reports"

GRAPH_FOLDER = "reports/graphs"

LOG_FOLDER = "logs"

# ==========================================================
# FILE PATHS
# ==========================================================

STUDENT_FILE = "database/students.csv"

ENCODING_FILE = "encodings/face_encodings.json"

LOG_FILE = "logs/system.log"

# ==========================================================
# ATTENDANCE SETTINGS
# ==========================================================

ATTENDANCE_STATUS = "Present"

DATE_FORMAT = "%Y-%m-%d"

TIME_FORMAT = "%H:%M:%S"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==========================================================
# REPORT SETTINGS
# ==========================================================

ENABLE_GRAPHS = True

EXPORT_CSV = True

EXPORT_EXCEL = True

EXPORT_PDF = False

# ==========================================================
# IMAGE SETTINGS
# ==========================================================

IMAGE_FORMAT = ".jpg"

IMAGE_QUALITY = 95

# ==========================================================
# LOG SETTINGS
# ==========================================================

ENABLE_LOGGING = True

LOG_LEVEL = "INFO"

# ==========================================================
# COLORS
# ==========================================================

SUCCESS_COLOR = "green"

WARNING_COLOR = "orange"

ERROR_COLOR = "red"

PRIMARY_COLOR = "#1F6AA5"

# ==========================================================
# FONTS
# ==========================================================

TITLE_FONT = ("Arial", 24, "bold")

HEADING_FONT = ("Arial", 18, "bold")

NORMAL_FONT = ("Arial", 14)

BUTTON_FONT = ("Arial", 14, "bold")