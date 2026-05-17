import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]


def _fmt_fecha(fecha_str):
    try:
        d = datetime.strptime(fecha_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return fecha_str


def _fmt_fecha_larga(fecha_str):
    try:
        d = datetime.strptime(fecha_str, "%Y-%m-%d")
        return f"{d.day:02d} de {MESES[d.month]} del {d.year}"
    except (ValueError, TypeError):
        return fecha_str


def _add_title(ws, title):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=10)
    cell = ws.cell(row=1, column=1, value=title)
    cell.font = Font(bold=True, size=14, underline="single")
    cell.alignment = Alignment(horizontal="center", vertical="center")


def _add_field(ws, row, label, value_lines):
    ws.cell(row=row, column=1, value=f"{label}:").font = Font(bold=True, size=10)
    for i, line in enumerate(value_lines):
        ws.cell(row=row + i, column=2, value=line).font = Font(size=10)
    return row + max(len(value_lines), 1)


def _add_section_title(ws, row, title):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=10)
    cell = ws.cell(row=row, column=1, value=title)
    cell.font = Font(bold=True, size=11, color="FFCC00")
    return row + 1


def _add_table(ws, row, headers, data_rows):
    thin = Side(style="thin", color="000000")
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, size=9, color="FFFFFF")
    data_font = Font(size=9)

    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    row += 1

    for data in data_rows:
        for c, v in enumerate(data, 1):
            cell = ws.cell(row=row, column=c, value=str(v))
            cell.font = data_font
            cell.border = border
            cell.alignment = Alignment(wrap_text=True)
        row += 1

    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = max(12, ws.column_dimensions[get_column_letter(c)].width or 12)

    return row + 1


def _build_workbook(doc_title, fecha_label, sections_data,
                    residente_nombre, residente_cargo,
                    responsable_nombre, responsable_cargo,
                    asunto, proyecto_nombre, cui, clima, observaciones,
                    show_fecha_col):
    wb = Workbook()
    ws = wb.active
    ws.title = doc_title[:31]
    ws.sheet_properties.pageSetUpPr = None

    row = 1
    _add_title(ws, doc_title)
    row += 2

    if residente_nombre:
        lines = [residente_nombre]
        if residente_cargo:
            lines.append(residente_cargo)
        row = _add_field(ws, row, "A", lines)
        row += 1

    if responsable_nombre:
        lines = [responsable_nombre]
        if responsable_cargo:
            lines.append(responsable_cargo)
        row = _add_field(ws, row, "DE", lines)
        row += 1

    if asunto:
        row = _add_field(ws, row, "ASUNTO", [asunto])
        row += 1

    row = _add_field(ws, row, "FECHA", [f"Santo Domingo de Acobamba, {fecha_label}"])
    row += 2

    img_path = os.path.join(os.path.dirname(__file__), "ENCABEZADO.png")
    if os.path.exists(img_path):
        try:
            from openpyxl.drawing.image import Image as XLImage
            img = XLImage(img_path)
            img.width = 400
            img.height = 80
            ws.add_image(img, "A1")
        except Exception:
            pass

    row = _add_section_title(ws, row, "DATOS GENERALES")
    row = _add_field(ws, row, "NOMBRE DEL PROYECTO", [proyecto_nombre])
    row = _add_field(ws, row, "CUI", [cui])
    if clima:
        row = _add_field(ws, row, "CLIMA", [clima])
    if observaciones:
        row = _add_field(ws, row, "OBSERVACIONES", [observaciones])
    row += 1

    for section in sections_data:
        s_type = section.get("type")
        if s_type == "partidas":
            row = _add_section_title(ws, row, section["title"])
            avances = section["data"]
            if avances:
                hdrs = ["Sector", "Código", "Partida", "Ejecutado por", "Operarios", "Oficiales", "Peones", "Horas", "Cant. Ejec."]
                if show_fecha_col:
                    hdrs = ["Fecha"] + hdrs
                data_rows = []
                for a in avances:
                    vals = []
                    if show_fecha_col:
                        vals.append(a.get("fecha", ""))
                    vals += [
                        a.get("sector_nombre") or "",
                        a.get("partida_codigo") or "",
                        a["partida_nombre"],
                        a.get("subcontrata_nombre") or "Empresa",
                        str(a.get("num_operarios", 0)),
                        str(a.get("num_oficiales", 0)),
                        str(a.get("num_peones", 0)),
                        f'{a.get("horas_trabajadas", 0):.1f}',
                        f'{a.get("cantidad_ejecutada", 0):.2f}',
                    ]
                    data_rows.append(vals)
                row = _add_table(ws, row, hdrs, data_rows)

        elif s_type == "materiales":
            row = _add_section_title(ws, row, section["title"])
            materiales = section["data"]
            if materiales:
                hdrs = ["Material", "Cantidad", "Unidad", "Fecha"]
                data_rows = [[m["material"], str(m["cantidad"]), m["unidad"], m["fecha"]] for m in materiales]
                row = _add_table(ws, row, hdrs, data_rows)

        elif s_type == "notas":
            row = _add_section_title(ws, row, section["title"])
            for nota in section["data"]:
                ws.cell(row=row, column=1, value=f"- {nota['nota']}").font = Font(size=10)
                row += 1
            row += 1

        elif s_type == "fotos":
            row = _add_section_title(ws, row, section["title"])
            for idx, foto in enumerate(section["data"], 1):
                ws.cell(row=row, column=1, value=f"FOTOGRAFIA N° {idx}").font = Font(bold=True, size=10)
                row += 1
                if os.path.exists(foto["ruta"]):
                    try:
                        from openpyxl.drawing.image import Image as XLImage
                        ws.add_image(XLImage(foto["ruta"]), f"A{row}")
                        row += 15
                    except Exception:
                        ws.cell(row=row, column=1, value="[No se pudo insertar la imagen]").font = Font(size=9)
                        row += 1
                if foto["descripcion"]:
                    ws.cell(row=row, column=1, value=f"Descripcion: {foto['descripcion']}").font = Font(size=10)
                    row += 1
            row += 1

    row += 1
    ws.cell(row=row, column=2, value="_________________________________").font = Font(size=10)
    row += 1
    ws.cell(row=row, column=2, value=responsable_nombre).font = Font(bold=True, size=10)
    row += 1
    ws.cell(row=row, column=2, value=responsable_cargo).font = Font(size=10)

    return wb


def generar_informe(fecha, avances, materiales, notas, fotos, registro,
                    responsable_nombre, responsable_cargo,
                    residente_nombre=None, residente_cargo=None,
                    asunto="", proyecto_nombre="", cui=""):
    fecha_label = _fmt_fecha_larga(fecha)
    sections = []
    if avances:
        sections.append({"type": "partidas", "title": "AVANCE DE PARTIDAS", "data": avances})
    if materiales:
        sections.append({"type": "materiales", "title": "CONTROL DE MATERIALES", "data": materiales})
    if notas:
        sections.append({"type": "notas", "title": "NOTAS DE CAMPO", "data": notas})
    if fotos:
        sections.append({"type": "fotos", "title": "REGISTRO FOTOGRAFICO", "data": fotos})

    clima = registro.get("clima", "") if registro else ""
    observaciones = registro.get("observaciones", "") if registro else ""

    return _build_workbook("REPORTE DIARIO DE OBRA", fecha_label, sections,
                           residente_nombre, residente_cargo,
                           responsable_nombre, responsable_cargo,
                           asunto, proyecto_nombre, cui, clima, observaciones,
                           show_fecha_col=False)


def generar_informe_semanal(fecha_ini, fecha_fin, registros, avances, materiales, notas,
                            responsable_nombre, responsable_cargo,
                            residente_nombre=None, residente_cargo=None,
                            asunto="", proyecto_nombre="", cui=""):
    fecha_label = f"Del {_fmt_fecha(fecha_ini)} al {_fmt_fecha(fecha_fin)}"
    sections = []

    clima = "Varios (ver detalle)"
    observaciones = ""

    if registros:
        lineas = []
        for r in registros:
            lineas.append(f"Dia {_fmt_fecha(r['fecha'])}: Clima {r['clima']}")
        observaciones = f"Dias registrados: {len(registros)}\n" + "\n".join(lineas)

    if avances:
        sections.append({"type": "partidas", "title": "AVANCE DE PARTIDAS", "data": avances})
    if materiales:
        sections.append({"type": "materiales", "title": "CONTROL DE MATERIALES", "data": materiales})
    if notas:
        sections.append({"type": "notas", "title": "NOTAS DE CAMPO", "data": notas})

    return _build_workbook("REPORTE SEMANAL DE OBRA", fecha_label, sections,
                           residente_nombre, residente_cargo,
                           responsable_nombre, responsable_cargo,
                           asunto, proyecto_nombre, cui, clima, observaciones,
                           show_fecha_col=True)
