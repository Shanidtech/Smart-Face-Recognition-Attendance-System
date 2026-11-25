# Smart Face Recognition Attendance System

A modern desktop attendance management system built with Python, CustomTkinter, and OpenCV. The application automates classroom and organizational attendance by registering student facial profiles across multiple poses, generating 128-dimensional facial embeddings, and matching faces in real time via live camera feeds.

---

## Key Features

- **Administrator Authentication**: Password-protected access supporting environment variables (`ADMIN_PASSWORD`).
- **Guided 5-Pose Student Registration**: Captures front, left, right, up, and down angles to create stable average facial encodings.
- **Real-Time Face Recognition**: Live webcam detection with multi-face detection handling, distance scoring, and bounding box visual labels.
- **One-Mark Daily Attendance**: Prevents duplicate attendance logging within the same date.
- **CSV and JSON Storage**: Lightweight, transparent file-based database for students and facial profiles.
- **Attendance Reporting & Filtering**: Searchable attendance records by student ID or name, with one-click filtered CSV exports.
- **Clean Application Shutdown**: Ensures camera hardware handles and UI threads release safely.

---

## Project Structure

```text
Face-Recognition-Attendance-System/
├── main.py              # Application controller & administrator login
├── register.py          # 5-pose student registration screen
├── attendance.py        # Real-time face recognition & attendance logger
├── report.py            # Searchable attendance viewer & CSV export
├── recognizer.py        # Face detection, 128-d encoding & vector comparison
├── camera.py            # OpenCV camera capture & resource manager
├── database.py          # CSV & JSON data store manager
├── config.py            # Central settings, constants & environment config
├── utils.py             # Validation, string helpers & UI dialogs
│
├── database/            # Contains students.csv
├── encodings/           # Contains face_encodings.json
├── attendance/          # Daily attendance logs (e.g., attendance_YYYY-MM-DD.csv)
├── images/
│   ├── students/        # Registered student facial captures (by ID)
│   └── temp/            # Temporary capture cache during registration
├── reports/             # Exported attendance report files
├── screenshots/         # Application interface previews
│
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment configuration
├── .gitignore           # Git ignore rules for personal/biometric data
├── LICENSE              # MIT License
└── README.md            # Project documentation
```

---

## System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.10 to 3.12 (Recommended for dlib pre-built wheel support)
- **Camera**: Standard built-in webcam or external USB webcam

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### 3. Install CMake and dlib
`face-recognition` relies on `dlib`.
- **Windows**: Install [CMake](https://cmake.org/download/) or install a pre-compiled `dlib` wheel compatible with your Python version.
- **Linux**:
  ```bash
  sudo apt-get update
  sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
  ```
- **macOS**:
  ```bash
  brew install cmake
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment (Optional)
Copy `.env.example` to `.env` and set your administrator password:
```bash
cp .env.example .env
```
Default administrator password is `admin123`.

---

## How to Run

Launch the application:
```bash
python main.py
```

### Standalone Modules
Individual screens can also be launched directly:
- **Registration**: `python register.py`
- **Attendance**: `python attendance.py`
- **Reports**: `python report.py`

---

## Application Workflow

1. **Administrator Login**: Enter the administrator password to access the main dashboard.
2. **Student Registration**:
   - Provide Student ID and Student Name.
   - Start the camera.
   - Follow the 5-step guided pose instructions (Look Straight, Turn Left, Turn Right, Look Up, Look Down).
   - An average normalized face embedding is created and committed to `encodings/face_encodings.json`.
3. **Take Attendance**:
   - Start the camera in the Attendance window.
   - Faces in frame are recognized against stored encodings.
   - Recognized students are marked present in today's daily CSV file (`attendance/attendance_YYYY-MM-DD.csv`).
   - Duplicate marks on the same day are automatically skipped.
4. **Attendance Reports**:
   - Select an attendance date.
   - Filter records in real time using the search box.
   - Export visible records to a new CSV file.

---

## Privacy & Security

Biometric facial encodings and photographs are classified as sensitive personal data. The repository's `.gitignore` is pre-configured to ensure no student photographs, personal face encodings, real databases, or attendance records are committed to version control.

---

## License

This project is open-source and licensed under the [MIT License](LICENSE).
