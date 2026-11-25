"""
main.py
-------------------------------------------------------
Application entry point for the Smart Face Recognition Attendance System.

This file owns the main window, handles the administrator login, and switches
between the dashboard, registration, attendance, and reports screens.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from attendance import AttendanceFrame
from config import (
    ADMIN_PASSWORD,
    APPEARANCE_MODE,
    APP_NAME,
    APP_VERSION,
    MIN_HEIGHT,
    MIN_WIDTH,
    THEME,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from register import StudentRegistrationFrame
from report import ReportFrame
from utils import center_window


class AttendanceApplication(ctk.CTk):
    """The main application window and navigation controller."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(THEME)

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self.exit_application)
        self.password_entry: ctk.CTkEntry | None = None
        self.show_login()

    def clear_screen(self) -> None:
        """Destroy all widgets on the current screen before navigation."""
        for widget in self.winfo_children():
            # Screens with cameras expose close(); call it before removal so a
            # camera can never remain locked after returning to the dashboard.
            if hasattr(widget, "stop_camera"):
                widget.stop_camera()
            widget.destroy()

    def show_login(self) -> None:
        """Display the administrator password screen."""
        self.clear_screen()
        container = ctk.CTkFrame(self, width=420, height=320)
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.pack_propagate(False)
        ctk.CTkLabel(container, text=APP_NAME, font=ctk.CTkFont(size=23, weight="bold"), wraplength=360).pack(
            pady=(48, 20), padx=24
        )
        ctk.CTkLabel(container, text="Administrator Login", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=4)
        self.password_entry = ctk.CTkEntry(container, width=280, placeholder_text="Enter password", show="*")
        self.password_entry.pack(pady=(16, 12))
        self.password_entry.bind("<Return>", lambda _event: self.verify_login())
        ctk.CTkButton(container, text="Login", width=280, command=self.verify_login).pack(pady=6)
        ctk.CTkButton(container, text="Exit", width=280, fg_color="#9b2525", command=self.exit_application).pack(pady=6)
        self.password_entry.focus_set()

    def verify_login(self) -> None:
        """Validate the administrator password and open the dashboard."""
        if self.password_entry is not None and self.password_entry.get() == ADMIN_PASSWORD:
            self.show_dashboard()
            return
        messagebox.showerror("Login failed", "Incorrect password.")
        if self.password_entry is not None:
            self.password_entry.delete(0, "end")
            self.password_entry.focus_set()

    def show_dashboard(self) -> None:
        """Show the application's main navigation screen."""
        self.clear_screen()
        wrapper = ctk.CTkFrame(self)
        wrapper.pack(fill="both", expand=True, padx=40, pady=35)
        ctk.CTkLabel(wrapper, text=APP_NAME, font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(70, 10))
        ctk.CTkLabel(wrapper, text="Select an action to continue", font=ctk.CTkFont(size=16)).pack(pady=(0, 28))
        self._dashboard_button(wrapper, "Register Student", self.show_registration).pack(pady=9)
        self._dashboard_button(wrapper, "Take Attendance", self.show_attendance).pack(pady=9)
        self._dashboard_button(wrapper, "View Reports", self.show_reports).pack(pady=9)
        self._dashboard_button(wrapper, "Log Out", self.show_login, color="#a66a00").pack(pady=(30, 9))
        self._dashboard_button(wrapper, "Exit", self.exit_application, color="#9b2525").pack(pady=9)

    @staticmethod
    def _dashboard_button(parent: ctk.CTkFrame, text: str, command, color: str | None = None) -> ctk.CTkButton:
        """Build consistently sized dashboard buttons."""
        options = {"master": parent, "text": text, "width": 300, "height": 42, "command": command}
        if color:
            options["fg_color"] = color
        return ctk.CTkButton(**options)

    def show_registration(self) -> None:
        """Navigate to the student registration screen."""
        self.clear_screen()
        StudentRegistrationFrame(self, on_close=self.show_dashboard).pack(fill="both", expand=True)

    def show_attendance(self) -> None:
        """Navigate to the live attendance screen."""
        self.clear_screen()
        AttendanceFrame(self, on_close=self.show_dashboard).pack(fill="both", expand=True)

    def show_reports(self) -> None:
        """Navigate to the attendance reports screen."""
        self.clear_screen()
        ReportFrame(self, on_close=self.show_dashboard).pack(fill="both", expand=True)

    def exit_application(self) -> None:
        """Ask before closing the program and release any active camera."""
        if messagebox.askyesno("Exit", "Do you really want to exit?"):
            self.clear_screen()
            self.destroy()


if __name__ == "__main__":
    AttendanceApplication().mainloop()
