"""
BenchGuard Pro - Professional Bench Press Safety Monitoring System
Main GUI Application Entry Point
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
from gui.main_window import MainWindow

def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("BenchGuard Pro")
    app.setOrganizationName("GymerGuard")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
