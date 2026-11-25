"""
database.py
-------------------------------------------------------
Database Module

Purpose:
    Handles all CSV and JSON database operations.

Author: Shanid
"""

# ==========================================================
# IMPORTS
# ==========================================================

import os
import csv
import json

import config


class DatabaseManager:
    """
    Handles all database operations.
    """

    def __init__(self):

        os.makedirs(config.DATABASE_FOLDER, exist_ok=True)
        os.makedirs(config.ENCODING_FOLDER, exist_ok=True)

        self.student_file = config.STUDENT_FILE
        self.encoding_file = config.ENCODING_FILE

        self.create_student_file()
        self.create_encoding_file()

    # ======================================================
    # CREATE STUDENT FILE
    # ======================================================

    def create_student_file(self):

        if not os.path.exists(self.student_file):

            with open(
                self.student_file,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Student ID",
                    "Student Name"
                ])

    # ======================================================
    # CREATE ENCODING FILE
    # ======================================================

    def create_encoding_file(self):

        if not os.path.exists(self.encoding_file):

            with open(
                self.encoding_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump([], file, indent=4)

    # ======================================================
    # SAVE STUDENT
    # ======================================================

    def save_student(
        self,
        student_id,
        student_name
    ):

        with open(
            self.student_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                student_id,
                student_name
            ])

    # ======================================================
    # LOAD STUDENTS
    # ======================================================

    def load_students(self):

        students = []

        with open(
            self.student_file,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                students.append(row)

        return students

    # ======================================================
    # SEARCH STUDENT
    # ======================================================

    def get_student(self, student_id):

        students = self.load_students()

        for student in students:

            if student["Student ID"] == student_id:

                return student

        return None

    # ======================================================
    # STUDENT EXISTS
    # ======================================================

    def student_exists(self, student_id):

        return self.get_student(student_id) is not None

    # ======================================================
    # UPDATE STUDENT
    # ======================================================

    def update_student(
        self,
        student_id,
        new_name
    ):

        students = self.load_students()

        with open(
            self.student_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Student ID",
                "Student Name"
            ])

            for student in students:

                if student["Student ID"] == student_id:

                    student["Student Name"] = new_name

                writer.writerow([
                    student["Student ID"],
                    student["Student Name"]
                ])

    # ======================================================
    # DELETE STUDENT
    # ======================================================

    def delete_student(self, student_id):

        students = self.load_students()

        with open(
            self.student_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Student ID",
                "Student Name"
            ])

            for student in students:

                if student["Student ID"] != student_id:

                    writer.writerow([
                        student["Student ID"],
                        student["Student Name"]
                    ])

    # ======================================================
    # SAVE ENCODINGS
    # ======================================================

    def save_encodings(self, data):

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

    # ======================================================
    # LOAD ENCODINGS
    # ======================================================

    def load_encodings(self):

        with open(
            self.encoding_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    # ======================================================
    # TEST
    # ======================================================

if __name__ == "__main__":

    db = DatabaseManager()

    db.save_student("101", "Rahul")

    print(db.load_students())

    print(db.student_exists("101"))

    print(db.get_student("101"))