"""
camera.py
-------------------------------------------------------
Camera Management Module

Purpose:
    Handles all camera operations for the
    Smart Face Recognition Attendance System.

Author: Shanid
"""

# ==========================================================
# IMPORTS
# ==========================================================

import cv2
import config


class CameraManager:
    """
    Handles all camera-related operations.
    """

    def __init__(self):
        """
        Initialize camera object.
        """
        self.camera = None

    # ======================================================
    # OPEN CAMERA
    # ======================================================

    def open_camera(self, source=None):
        """
        Opens the selected camera.

        Parameters:
            source:
                None = Default Camera
                0 = Laptop Webcam
                1 = USB Webcam
                "http://..." = IP Camera

        Returns:
            True if camera opened successfully,
            otherwise False.
        """

        if source is None:
            source = config.DEFAULT_CAMERA

        self.camera = cv2.VideoCapture(source)

        if not self.camera.isOpened():
            return False

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        return True

    # ======================================================
    # READ FRAME
    # ======================================================

    def read_frame(self):
        """
        Reads one frame from the camera.

        Returns:
            (success, frame)
        """

        if self.camera is None:
            return False, None

        return self.camera.read()

    # ======================================================
    # SHOW CAMERA
    # ======================================================

    def show_camera(self):
        """
        Displays live camera preview.

        Press Q to close.
        """

        if self.camera is None:
            print("Camera is not opened.")
            return

        while True:

            success, frame = self.read_frame()

            if not success:
                print("Unable to read frame.")
                break

            cv2.imshow(
                "Camera Preview",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

        self.release_camera()

    # ======================================================
    # SAVE FRAME
    # ======================================================

    def save_frame(self, frame, filename):
        """
        Saves an image to disk.

        Parameters:
            frame
            filename
        """

        cv2.imwrite(filename, frame)

    # ======================================================
    # RELEASE CAMERA
    # ======================================================

    def release_camera(self):
        """
        Releases the camera safely.
        """

        if self.camera is not None:

            self.camera.release()
            self.camera = None

        cv2.destroyAllWindows()

    # ======================================================
    # CAMERA STATUS
    # ======================================================

    def is_camera_open(self):
        """
        Returns True if camera is open.
        """

        if self.camera is None:
            return False

        return self.camera.isOpened()


# ==========================================================
# TESTING
# ==========================================================

if __name__ == "__main__":

    camera = CameraManager()

    if camera.open_camera():

        print("Camera opened successfully.")
        print("Press Q to close.")

        camera.show_camera()

    else:

        print("Unable to open camera.")