"""
recognizer.py
-------------------------------------------------------
Smart Face Recognition Attendance System

Purpose:
    Handles all face recognition operations.

Features:
    - Load Images
    - Detect Faces
    - Generate Face Encodings
    - Load Saved Encodings
    - Compare Faces
    - Recognize Students

Author: Shanid
"""

# ==========================================================
# IMPORTS
# ==========================================================

import os
import json
import cv2
import numpy as np
import face_recognition

import config


# ==========================================================
# FACE RECOGNIZER
# ==========================================================

class FaceRecognizer:
    """
    Handles all face recognition operations.
    """

    def __init__(
        self,
        encoding_file=config.ENCODING_FILE,
        tolerance=config.FACE_TOLERANCE
    ):
        """
        Constructor
        """

        self.encoding_file = encoding_file
        self.tolerance = tolerance

        self.known_encodings = []
        self.known_ids = []
        self.known_names = []

        self.load_saved_encodings()

    # ======================================================
    # LOAD IMAGE
    # ======================================================

    def load_image(self, image_path):
        """
        Loads an image from disk.

        Parameters
        ----------
        image_path : str

        Returns
        -------
        numpy.ndarray
        """

        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(
                "Unable to read image."
            )

        rgb_image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        return rgb_image

    # ======================================================
    # DETECT FACES
    # ======================================================

    def detect_faces(self, image):
        """
        Detect all faces inside an image.

        Returns
        -------
        list
        """

        locations = face_recognition.face_locations(
            image,
            model=config.FACE_DETECTION_MODEL
        )

        return locations

    # ======================================================
    # ENCODE FACE
    # ======================================================

    def encode_face(self, image):
        """
        Generates face encoding.

        Returns
        -------
        numpy.ndarray
        """

        locations = self.detect_faces(image)

        if len(locations) == 0:

            raise ValueError(
                "No face detected."
            )

        if len(locations) > 1:

            raise ValueError(
                "Multiple faces detected."
            )

        encodings = face_recognition.face_encodings(
            image,
            locations
        )

        if len(encodings) == 0:

            raise ValueError(
                "Encoding failed."
            )

        return encodings[0]

    # ======================================================
    # LOAD SAVED ENCODINGS
    # ======================================================

    def load_saved_encodings(self):
        """
        Loads all saved encodings from JSON.
        """

        self.known_encodings.clear()
        self.known_ids.clear()
        self.known_names.clear()

        if not os.path.exists(
            self.encoding_file
        ):
            return

        with open(
            self.encoding_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        for student in data:

            self.known_ids.append(
                student["student_id"]
            )

            self.known_names.append(
                student["student_name"]
            )

            self.known_encodings.append(
                np.array(
                    student["encoding"]
                )
            )
    # ======================================================
    # SAVE ENCODING
    # ======================================================

    def save_encoding(
        self,
        student_id,
        student_name,
        encoding
    ):
        """
        Saves a student's face encoding to the JSON file.
        """

        data = []

        if os.path.exists(self.encoding_file):

            with open(
                self.encoding_file,
                "r",
                encoding="utf-8"
            ) as file:

                try:
                    data = json.load(file)

                except json.JSONDecodeError:
                    data = []

        data.append({

            "student_id": student_id,
            "student_name": student_name,
            "encoding": encoding.tolist()

        })

        with open(
            self.encoding_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

        self.load_saved_encodings()

    # ======================================================
    # RELOAD ENCODINGS
    # ======================================================

    def reload_encodings(self):
        """
        Reloads all saved face encodings.
        """

        self.load_saved_encodings()

    # ======================================================
    # COMPARE FACE
    # ======================================================

    def compare_face(
        self,
        unknown_encoding
    ):
        """
        Compare an unknown face encoding with all
        registered students.

        Returns
        -------
        tuple
            (
                matched,
                student_id,
                student_name,
                distance
            )
        """

        if len(self.known_encodings) == 0:

            return (
                False,
                None,
                None,
                None
            )

        matches = face_recognition.compare_faces(

            self.known_encodings,
            unknown_encoding,
            tolerance=self.tolerance

        )

        distances = face_recognition.face_distance(

            self.known_encodings,
            unknown_encoding

        )

        if len(distances) == 0:

            return (
                False,
                None,
                None,
                None
            )

        best_match_index = np.argmin(
            distances
        )

        if matches[best_match_index]:

            return (

                True,

                self.known_ids[
                    best_match_index
                ],

                self.known_names[
                    best_match_index
                ],

                float(
                    distances[
                        best_match_index
                    ]
                )

            )

        return (

            False,
            None,
            None,
            None

        )

    # ======================================================
    # RECOGNIZE IMAGE
    # ======================================================

    def recognize_image(
        self,
        image
    ):
        """
        Recognize a single face from an image.

        Returns
        -------
        dict
        """

        locations = self.detect_faces(
            image
        )

        if len(locations) == 0:

            return {

                "success": False,
                "message": "No face detected."

            }

        if len(locations) > 1:

            return {

                "success": False,
                "message": "Multiple faces detected."

            }

        encoding = face_recognition.face_encodings(

            image,
            locations

        )[0]

        matched, student_id, student_name, distance = self.compare_face(
            encoding
        )

        if matched:

            return {

                "success": True,
                "student_id": student_id,
                "student_name": student_name,
                "distance": distance,
                "location": locations[0]

            }

        return {

            "success": False,
            "message": "Unknown Face"

        }
    # ======================================================
    # RECOGNIZE FRAME
    # ======================================================

    def recognize_frame(self, frame):
        """
        Recognizes all faces in a live camera frame.

        Returns:
            list
        """

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        locations = face_recognition.face_locations(
            rgb_frame,
            model=config.FACE_DETECTION_MODEL
        )

        encodings = face_recognition.face_encodings(
            rgb_frame,
            locations
        )

        results = []

        for location, encoding in zip(
            locations,
            encodings
        ):

            matched, student_id, student_name, distance = self.compare_face(
                encoding
            )

            if matched:

                results.append({

                    "student_id": student_id,
                    "student_name": student_name,
                    "location": location,
                    "distance": distance,
                    "matched": True

                })

            else:

                results.append({

                    "student_id": None,
                    "student_name": "Unknown",
                    "location": location,
                    "distance": None,
                    "matched": False

                })

        return results

    # ======================================================
    # DRAW RESULTS
    # ======================================================

    def draw_results(
        self,
        frame,
        results
    ):
        """
        Draw rectangles and names around detected faces.
        """

        for result in results:

            top, right, bottom, left = result["location"]

            if result["matched"]:

                color = (0, 255, 0)
                label = result["student_name"]

            else:

                color = (0, 0, 255)
                label = "Unknown"

            cv2.rectangle(

                frame,

                (left, top),

                (right, bottom),

                color,

                2

            )

            cv2.rectangle(

                frame,

                (left, bottom - 30),

                (right, bottom),

                color,

                cv2.FILLED

            )

            cv2.putText(

                frame,

                label,

                (left + 6, bottom - 8),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (255, 255, 255),

                2

            )

        return frame

    # ======================================================
    # GET REGISTERED STUDENTS
    # ======================================================

    def get_registered_students(self):
        """
        Returns all registered students.
        """

        students = []

        for student_id, student_name in zip(

            self.known_ids,

            self.known_names

        ):

            students.append({

                "student_id": student_id,

                "student_name": student_name

            })

        return students

# ==========================================================
# TESTING
# ==========================================================

if __name__ == "__main__":

    recognizer = FaceRecognizer()

    print()

    print("=" * 50)

    print("Face Recognizer Loaded")

    print("=" * 50)

    print()

    print(
        "Registered Students :",
        len(recognizer.known_ids)
    )

    for student in recognizer.get_registered_students():

        print(

            student["student_id"],

            "-",

            student["student_name"]

        )