"""
utils.py
-------------------------------------------------------
Utility Functions

Purpose:
    This file contains helper functions used
    throughout the project.

Author: Shanid
"""

# ==========================================================
# IMPORTS
# ==========================================================

import os
from datetime import datetime
from tkinter import messagebox

# ==========================================================
# FOLDER FUNCTIONS
# ==========================================================

def create_folder(folder_path):
    """
    Creates a folder if it does not already exist.
    """

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


# ==========================================================
# DATE & TIME FUNCTIONS
# ==========================================================

def get_current_date():
    """
    Returns current date.
    Example: 2026-09-07
    """

    return datetime.now().strftime("%Y-%m-%d")


def get_current_time():
    """
    Returns current time.
    Example: 10:30:15
    """

    return datetime.now().strftime("%H:%M:%S")


def get_current_datetime():
    """
    Returns current date and time.
    """

    return datetime.now()


# ==========================================================
# VALIDATION FUNCTIONS
# ==========================================================

def validate_student_name(name):
    """
    Validate student name.
    """

    name = name.strip()

    if len(name) == 0:
        return False

    if len(name) < 3:
        return False

    return True


def validate_student_id(student_id):
    """
    Validate student ID.
    """

    student_id = student_id.strip()

    if len(student_id) == 0:
        return False

    return True


# ==========================================================
# STRING FUNCTIONS
# ==========================================================

def remove_extra_spaces(text):
    """
    Removes leading and trailing spaces.
    """

    return text.strip()


def capitalize_name(name):
    """
    Converts text into title case.
    """

    return name.title()


# ==========================================================
# FILE FUNCTIONS
# ==========================================================

def file_exists(file_path):
    """
    Returns True if file exists.
    """

    return os.path.exists(file_path)


# ==========================================================
# MESSAGE BOX FUNCTIONS
# ==========================================================

def show_success(message):
    """
    Shows success message.
    """

    messagebox.showinfo(
        "Success",
        message
    )


def show_error(message):
    """
    Shows error message.
    """

    messagebox.showerror(
        "Error",
        message
    )


def show_warning(message):
    """
    Shows warning message.
    """

    messagebox.showwarning(
        "Warning",
        message
    )


def ask_confirmation(message):
    """
    Displays Yes/No confirmation dialog.

    Returns:
        True or False
    """

    return messagebox.askyesno(
        "Confirmation",
        message
    )


# ==========================================================
# ENTRY FUNCTIONS
# ==========================================================

def clear_entry(entry):
    """
    Clears a Tkinter Entry widget.
    """

    entry.delete(0, "end")


# ==========================================================
# WINDOW FUNCTIONS
# ==========================================================

def center_window(window, width, height):
    """
    Centers the window on the screen.
    """

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    window.geometry(f"{width}x{height}+{x}+{y}")


# ==========================================================
# TESTING
# ==========================================================

if __name__ == "__main__":

    print("Current Date :", get_current_date())
    print("Current Time :", get_current_time())
    print("Current DateTime :", get_current_datetime())

    print(validate_student_name("Shanid"))
    print(validate_student_id("101"))

    print(capitalize_name("shanid"))
    print(remove_extra_spaces("   Python Project   "))