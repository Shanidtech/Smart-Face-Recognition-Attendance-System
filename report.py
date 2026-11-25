"""
report.py
-------------------------------------------------------
Attendance reporting screen for the Smart Face Recognition Attendance System.

It reads daily CSV files produced by attendance.py, displays a searchable
report, calculates simple attendance totals, and exports the currently visible
records to a separate CSV file.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from tkinter import filedialog, ttk

from config import APP_NAME, ATTENDANCE_FOLDER, DATE_FORMAT, REPORT_FOLDER
from utils import get_current_date, show_error, show_success, show_warning


HEADERS = ["Student ID", "Student Name", "Date", "Time", "Status"]


class ReportManager:
    """Reads and filters attendance CSV records without modifying source data."""

    def __init__(self, attendance_folder: str = ATTENDANCE_FOLDER) -> None:
        self.attendance_folder = Path(attendance_folder)

    def available_dates(self) -> list[str]:
        """Return attendance dates found in filenames, newest first."""
        if not self.attendance_folder.exists():
            return []
        dates: list[str] = []
        for file_path in self.attendance_folder.glob("attendance_*.csv"):
            date = file_path.stem.removeprefix("attendance_")
            try:
                # Validate the filename before displaying it as a report date.
                from datetime import datetime

                datetime.strptime(date, DATE_FORMAT)
                dates.append(date)
            except ValueError:
                continue
        return sorted(set(dates), reverse=True)

    def load_date(self, date: str) -> list[dict[str, str]]:
        """Load one daily attendance CSV, returning no rows when it is absent."""
        path = self.attendance_folder / f"attendance_{date}.csv"
        if not path.exists():
            return []
        try:
            with path.open("r", newline="", encoding="utf-8") as file:
                return [
                    {header: row.get(header, "") for header in HEADERS}
                    for row in csv.DictReader(file)
                ]
        except (OSError, csv.Error) as error:
            raise ValueError(f"Could not read {path.name}: {error}") from error

    @staticmethod
    def filter_records(records: list[dict[str, str]], query: str) -> list[dict[str, str]]:
        """Return records whose ID or name contains *query*, case-insensitively."""
        query = query.strip().casefold()
        if not query:
            return records
        return [
            row
            for row in records
            if query in row["Student ID"].casefold() or query in row["Student Name"].casefold()
        ]


class ReportFrame(ctk.CTkFrame):
    """Reusable CustomTkinter interface for attendance reports."""

    def __init__(self, master: ctk.CTkBaseClass, on_close: Optional[Callable[[], None]] = None) -> None:
        super().__init__(master)
        self.on_close = on_close
        self.manager = ReportManager()
        self.all_records: list[dict[str, str]] = []
        self.visible_records: list[dict[str, str]] = []
        self._build_interface()
        self.refresh_dates(select_date=get_current_date())
        self._set_close_protocol()

    def _build_interface(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            self, text="Attendance Reports", font=ctk.CTkFont(size=26, weight="bold")
        ).grid(row=0, column=0, padx=24, pady=(20, 10), sticky="w")

        filters = ctk.CTkFrame(self)
        filters.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="ew")
        filters.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(filters, text="Attendance date").grid(row=0, column=0, padx=(16, 6), pady=14)
        self.date_var = ctk.StringVar()
        self.date_menu = ctk.CTkOptionMenu(filters, values=["No reports"], variable=self.date_var, command=self.load_selected_date)
        self.date_menu.grid(row=0, column=1, padx=6, pady=14)
        ctk.CTkButton(filters, text="Refresh", width=90, command=self.refresh_dates).grid(
            row=0, column=2, padx=6, pady=14
        )
        self.search_entry = ctk.CTkEntry(filters, placeholder_text="Search by student ID or name")
        self.search_entry.grid(row=0, column=3, padx=(18, 6), pady=14, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _event: self.apply_filter())
        ctk.CTkButton(filters, text="Export visible rows", command=self.export_visible).grid(
            row=0, column=4, padx=(6, 16), pady=14
        )

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, padx=24, pady=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        style = ttk.Style()
        style.configure("Attendance.Treeview", rowheight=28, font=("Arial", 10))
        self.table = ttk.Treeview(table_frame, columns=HEADERS, show="headings", style="Attendance.Treeview")
        for header in HEADERS:
            self.table.heading(header, text=header)
            self.table.column(header, width=140, anchor="center")
        self.table.column("Student Name", width=240, anchor="w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=0, column=0, padx=(12, 0), pady=12, sticky="nsew")
        scroll.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="ns")

        footer = ctk.CTkFrame(self)
        footer.grid(row=3, column=0, padx=24, pady=12, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        self.summary_var = ctk.StringVar(value="No report loaded.")
        ctk.CTkLabel(footer, textvariable=self.summary_var, font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=16, pady=12, sticky="w"
        )
        ctk.CTkButton(footer, text="Close", width=100, fg_color="#9b2525", command=self.close).grid(
            row=0, column=1, padx=12, pady=8
        )

    def _set_close_protocol(self) -> None:
        try:
            self.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.close)
        except Exception:
            pass

    def refresh_dates(self, select_date: Optional[str] = None) -> None:
        """Reload available daily report dates, preserving a selected date if possible."""
        dates = self.manager.available_dates()
        if not dates:
            self.date_menu.configure(values=["No reports"])
            self.date_var.set("No reports")
            self.all_records = []
            self.apply_filter()
            return
        self.date_menu.configure(values=dates)
        chosen = select_date if select_date in dates else self.date_var.get()
        self.date_var.set(chosen if chosen in dates else dates[0])
        self.load_selected_date(self.date_var.get())

    def load_selected_date(self, date: str) -> None:
        """Load the chosen date and refresh the table."""
        if date == "No reports":
            self.all_records = []
            self.apply_filter()
            return
        try:
            self.all_records = self.manager.load_date(date)
        except ValueError as error:
            self.all_records = []
            show_error(str(error))
        self.apply_filter()

    def apply_filter(self) -> None:
        """Show only rows matching the current search phrase and update totals."""
        self.visible_records = self.manager.filter_records(self.all_records, self.search_entry.get())
        for item in self.table.get_children():
            self.table.delete(item)
        for row in self.visible_records:
            self.table.insert("", "end", values=[row[header] for header in HEADERS])
        statuses = Counter(row["Status"] for row in self.visible_records)
        self.summary_var.set(
            f"Visible records: {len(self.visible_records)}   |   "
            + "   ".join(f"{status}: {count}" for status, count in sorted(statuses.items()))
        )

    def export_visible(self) -> None:
        """Export filtered data; source attendance files are never overwritten."""
        if not self.visible_records:
            show_warning("There are no visible rows to export.")
            return
        Path(REPORT_FOLDER).mkdir(parents=True, exist_ok=True)
        suggested = f"attendance_report_{self.date_var.get()}.csv"
        destination = filedialog.asksaveasfilename(
            title="Save attendance report",
            initialdir=REPORT_FOLDER,
            initialfile=suggested,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not destination:
            return
        try:
            with open(destination, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(self.visible_records)
        except OSError as error:
            show_error(f"Could not export report. {error}")
            return
        show_success(f"Exported {len(self.visible_records)} record(s).")

    def close(self) -> None:
        """Return to the host screen or close the standalone report window."""
        if self.on_close:
            self.on_close()
        else:
            self.winfo_toplevel().destroy()


def open_report_window() -> None:
    """Run the reporting page as a standalone application window."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.title(f"{APP_NAME} - Reports")
    app.geometry("1050x680")
    app.minsize(850, 550)
    ReportFrame(app).pack(fill="both", expand=True)
    app.mainloop()


if __name__ == "__main__":
    open_report_window()
