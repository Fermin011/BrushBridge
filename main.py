import sys
from pathlib import Path

from src.parsers.abr_parser import read_abr
from src.exporters.gbr_writer import write_gbr
from src.exporters.krita_bundle import create_bundle


def convert(abr_path, output_dir=None):
    # Convierte un archivo ABR a GBR + bundle Krita
    abr_path = Path(abr_path)
    if not abr_path.is_file():
        print(f"Error: no se encontro '{abr_path}'")
        return False

    if output_dir is None:
        output_dir = Path("output")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    abr_name = abr_path.stem

    print(f"Leyendo '{abr_path}'...")
    brushes = read_abr(str(abr_path))
    print(f"Se encontraron {len(brushes)} pinceles.")

    if not brushes:
        print("No se encontraron pinceles.")
        return False

    # Generar archivos GBR
    gbr_files = []
    for i, brush_img in enumerate(brushes):
        safe_name = f"{abr_name}_{i:03d}"
        gbr_path = str(output_dir / f"{safe_name}.gbr")
        write_gbr(brush_img, gbr_path, safe_name)
        gbr_files.append(gbr_path)
        w, h = brush_img.size
        print(f"  [{i + 1}/{len(brushes)}] {safe_name}.gbr ({w}x{h})")

    # Crear bundle
    bundle_path = str(output_dir / f"{abr_name}.bundle")
    create_bundle(gbr_files, bundle_path, abr_name)

    print(f"\nBundle creado: {bundle_path}")
    print(f"Pinceles convertidos: {len(gbr_files)}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Sin argumentos: abrir interfaz grafica
        from src.gui.main_window import run_gui
        run_gui()
    else:
        success = convert(sys.argv[1])
        if not success:
            sys.exit(1)
