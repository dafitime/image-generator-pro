from .main_window import ImageOrganizerGUI

def main():
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ImageOrganizerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()