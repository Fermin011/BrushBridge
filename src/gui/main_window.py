import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.parsers.abr_parser import read_abr
from src.exporters.gbr_writer import write_gbr
from src.exporters.krita_bundle import create_bundle


class ConvertWorker(QThread):
    # Hilo de conversion para no bloquear la GUI
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, abr_path, output_dir):
        super().__init__()
        self.abr_path = abr_path
        self.output_dir = output_dir

    def run(self):
        try:
            self.progress.emit(f"Leyendo '{self.abr_path}'...")
            brushes = read_abr(self.abr_path)
            self.progress.emit(f"Se encontraron {len(brushes)} pinceles.")

            if not brushes:
                self.finished.emit(False, "No se encontraron pinceles.")
                return

            output_dir = Path(self.output_dir)
            output_dir.mkdir(exist_ok=True)
            abr_name = Path(self.abr_path).stem

            gbr_files = []
            for i, brush_img in enumerate(brushes):
                safe_name = f"{abr_name}_{i:03d}"
                gbr_path = str(output_dir / f"{safe_name}.gbr")
                write_gbr(brush_img, gbr_path, safe_name)
                gbr_files.append(gbr_path)
                w, h = brush_img.size
                self.progress.emit(
                    f"  [{i + 1}/{len(brushes)}] {safe_name}.gbr ({w}x{h})"
                )

            bundle_path = str(output_dir / f"{abr_name}.bundle")
            create_bundle(gbr_files, bundle_path, abr_name)
            self.progress.emit(f"Bundle creado: {bundle_path}")

            self.finished.emit(
                True, f"Convertidos {len(gbr_files)} pinceles exitosamente."
            )
        except Exception as e:
            self.finished.emit(False, f"Error: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrushBridge")
        self.setMinimumSize(600, 450)
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Titulo
        title = QLabel("BrushBridge")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Conversor de pinceles ABR a Krita")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # Archivo de entrada
        input_group = QGroupBox("Archivo de entrada")
        input_layout = QHBoxLayout(input_group)
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Selecciona un archivo .abr...")
        self.input_path.setReadOnly(True)
        input_layout.addWidget(self.input_path)
        btn_browse = QPushButton("Examinar")
        btn_browse.clicked.connect(self._browse_input)
        input_layout.addWidget(btn_browse)
        layout.addWidget(input_group)

        # Directorio de salida
        output_group = QGroupBox("Directorio de salida")
        output_layout = QHBoxLayout(output_group)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Por defecto: ./output")
        output_layout.addWidget(self.output_path)
        btn_output = QPushButton("Examinar")
        btn_output.clicked.connect(self._browse_output)
        output_layout.addWidget(btn_output)
        layout.addWidget(output_group)

        # Boton convertir
        self.btn_convert = QPushButton("Convertir")
        self.btn_convert.setStyleSheet("font-size: 14px; padding: 8px;")
        self.btn_convert.clicked.connect(self._start_conversion)
        self.btn_convert.setEnabled(False)
        layout.addWidget(self.btn_convert)

        # Log de salida
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.log)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo ABR", "",
            "Archivos ABR (*.abr);;Todos los archivos (*)"
        )
        if path:
            self.input_path.setText(path)
            self.btn_convert.setEnabled(True)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de salida"
        )
        if path:
            self.output_path.setText(path)

    def _start_conversion(self):
        abr_path = self.input_path.text()
        if not abr_path:
            return

        output_dir = self.output_path.text() or "output"

        self.log.clear()
        self.btn_convert.setEnabled(False)

        self.worker = ConvertWorker(abr_path, output_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, msg):
        self.log.append(msg)

    def _on_finished(self, success, msg):
        status = "Listo" if success else "Fallo"
        self.log.append(f"\n{status}: {msg}")
        self.btn_convert.setEnabled(True)
        self.worker = None


def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
