import os
import zipfile
import xml.etree.ElementTree as ET


def create_bundle(gbr_files, bundle_path, bundle_name):
    # Crea un bundle de Krita (.bundle) como ZIP con los .gbr
    meta_xml = _generate_meta_xml(bundle_name, len(gbr_files))

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("mimetype", "application/x-krita-resourcebundle")
        zf.writestr("meta.xml", meta_xml)

        for gbr_path in gbr_files:
            arcname = "brushes/" + os.path.basename(gbr_path)
            zf.write(gbr_path, arcname)


def _generate_meta_xml(bundle_name, brush_count):
    # Genera meta.xml para el bundle
    root = ET.Element("package")
    root.set("xmlns", "http://www.idpf.org/2007/opf")
    root.set("version", "1.0")
    root.set("unique-identifier", bundle_name)

    metadata = ET.SubElement(root, "metadata")

    name_el = ET.SubElement(metadata, "name")
    name_el.text = bundle_name

    desc_el = ET.SubElement(metadata, "description")
    desc_el.text = f"Bundle con {brush_count} pinceles convertidos desde ABR"

    author_el = ET.SubElement(metadata, "author")
    author_el.text = "BrushBridge"

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
