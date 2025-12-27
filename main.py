import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from ui.window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Drichsearch")
    # Thème sombre global
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_bg = QColor(18, 18, 18)
    dark_alt = QColor(28, 28, 28)
    dark_mid = QColor(38, 38, 38)
    text = QColor(235, 235, 235)
    disabled_text = QColor(140, 140, 140)
    highlight = QColor(66, 133, 244)

    dark_palette.setColor(QPalette.Window, dark_bg)
    dark_palette.setColor(QPalette.WindowText, text)
    dark_palette.setColor(QPalette.Base, dark_alt)
    dark_palette.setColor(QPalette.AlternateBase, dark_mid)
    dark_palette.setColor(QPalette.ToolTipBase, text)
    dark_palette.setColor(QPalette.ToolTipText, text)
    dark_palette.setColor(QPalette.Text, text)
    dark_palette.setColor(QPalette.Button, dark_mid)
    dark_palette.setColor(QPalette.ButtonText, text)
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Highlight, highlight)
    dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.PlaceholderText, disabled_text)
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    app.setPalette(dark_palette)

    app.setStyleSheet(
        """
        QWidget { background-color: #121212; color: #eaeaea; }
        QLineEdit { background-color: #1e1e1e; color: #eaeaea; border: 1px solid #3a3a3a; border-radius: 10px; padding: 6px 10px; }
        QLineEdit:focus { border: 1px solid #4285F4; }
        QTextEdit { background-color: #1e1e1e; color: #eaeaea; border: 1px solid #3a3a3a; border-radius: 8px; }
        QComboBox { background-color: #1e1e1e; color: #eaeaea; border: 1px solid #3a3a3a; border-radius: 8px; padding: 4px 8px; }
        QComboBox QAbstractItemView { background-color: #1e1e1e; color: #eaeaea; selection-background-color: #2a2a2a; }
        QPushButton { background-color: #262626; color: #eaeaea; border: 1px solid #3a3a3a; border-radius: 10px; padding: 6px; }
        QPushButton:hover { background-color: #2e2e2e; }
        QPushButton:pressed { background-color: #333333; }
        QSplitter::handle { background-color: #2a2a2a; }
        QToolTip { background-color: #262626; color: #eaeaea; border: 1px solid #3a3a3a; }
        """
    )
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()