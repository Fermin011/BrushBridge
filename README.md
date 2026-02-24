# BrushBridge

Conversor de pinceles ABR (Adobe Photoshop) a formatos compatibles con Krita.

Lee archivos `.abr` de distintas versiones de Photoshop, extrae cada pincel y genera:

- Archivos `.gbr` individuales (compatibles con GIMP y Krita)
- Un `.bundle` listo para importar en Krita

Soporta ABR v1, v2, v6, v7 y v10 con descompresión RLE/PackBits automática.

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/Fermin011/BrushBridge.git
cd BrushBridge
```

Crear entorno virtual e instalar dependencias:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

## Uso

### Interfaz gráfica

```bash
python main.py
```

Se abre una ventana donde podés seleccionar el archivo `.abr`, elegir el directorio de salida y convertir.

### Línea de comandos

```bash
python main.py <archivo.abr>
```

Los archivos convertidos se guardan en la carpeta `output/`.

## Estructura

```
BrushBridge/
├── main.py
├── requirements.txt
└── src/
    ├── compression.py          # PackBits/RLE
    ├── image_utils.py          # Conversión de píxeles a imagen
    ├── parsers/
    │   └── abr_parser.py       # Parser ABR
    ├── exporters/
    │   ├── gbr_writer.py       # Exportador GBR
    │   └── krita_bundle.py     # Generador de bundles Krita
    └── gui/
        └── main_window.py      # Interfaz PyQt6
```
