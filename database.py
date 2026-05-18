import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "db_obra.sqlite")
_OVERRIDE_PATH = None


def set_db_path(path):
    global _OVERRIDE_PATH
    _OVERRIDE_PATH = path


def get_connection():
    path = _OVERRIDE_PATH if _OVERRIDE_PATH else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ── Old tables (preserved for legacy data) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            sector TEXT NOT NULL,
            clima TEXT NOT NULL,
            num_obreros INTEGER NOT NULL,
            horas_trabajadas REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            material TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            nota TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            fecha TEXT NOT NULL,
            sector TEXT,
            descripcion TEXT,
            ruta TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── New catalog tables ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sectores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materiales_catalogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            unidad TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcontratas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            responsable TEXT DEFAULT '',
            telefono TEXT DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT DEFAULT '',
            nombre TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            sector_id INTEGER REFERENCES sectores(id) ON DELETE SET NULL,
            unidad TEXT DEFAULT '',
            metrado_total REAL DEFAULT 0
        )
    """)

    # ── New transaction tables ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            clima TEXT NOT NULL DEFAULT 'Soleado',
            observaciones TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avance_partida (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registro_id INTEGER NOT NULL REFERENCES registro_diario(id) ON DELETE CASCADE,
            partida_id INTEGER NOT NULL REFERENCES partidas(id) ON DELETE CASCADE,
            subcontrata_id INTEGER REFERENCES subcontratas(id) ON DELETE SET NULL,
            sector_id INTEGER REFERENCES sectores(id) ON DELETE SET NULL,
            num_operarios INTEGER DEFAULT 0,
            num_oficiales INTEGER DEFAULT 0,
            num_peones INTEGER DEFAULT 0,
            horas_trabajadas REAL DEFAULT 0,
            cantidad_ejecutada REAL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Migrations for existing DBs ──
    for col in [("registro_diario", "sector_id"), ("avance_partida", "sector_id")]:
        try:
            cursor.execute(f"ALTER TABLE {col[0]} ADD COLUMN {col[1]} INTEGER")
        except Exception:
            pass

    # ── Config table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        ("responsable_nombre", "Ing. MANUEL MEJIA DIAZ"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        ("responsable_cargo", "INGENIERO DE PRODUCCION"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        ("residente_nombre", "Ing. WILFREDO PORTAL IDRUGO"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        ("residente_cargo", "RESIDENTE DE OBRA"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        ("proyecto_nombre", '"MEJORAMIENTO DE LOS SERVICIOS DE SALUD DEL CENTRO DE SALUD SANTO DOMINGO DE ACOBAMBA, DISTRITO DE SANTO DOMINGO DE ACOBAMBA, PROVINCIA DE HUANCAYO, JUNIN"'),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        ("cui", "2336443"),
    )

    # ── Seed default data ──
    seed_sectores(cursor)
    seed_materiales(cursor)
    seed_subcontratas(cursor)

    conn.commit()
    conn.close()


def seed_sectores(cursor):
    if cursor.execute("SELECT COUNT(*) FROM sectores").fetchone()[0] > 0:
        return
    default = [
        "Bloque A - Primer Nivel",
        "Bloque A - Segundo Nivel",
        "Bloque A - Tercer Nivel",
        "Bloque B - Cimentación",
        "Bloque B - Estructuras Elevadas",
        "Área de Acopio",
        "Taller de Carpintería",
        "Instalaciones Sanitarias",
        "Instalaciones Eléctricas",
        "Acabados Generales",
        "Exteriores",
    ]
    for s in default:
        cursor.execute("INSERT OR IGNORE INTO sectores (nombre) VALUES (?)", (s,))


def seed_materiales(cursor):
    if cursor.execute("SELECT COUNT(*) FROM materiales_catalogo").fetchone()[0] > 0:
        return
    default = [
        ("Cemento Portland Tipo I", "bolsas"),
        ("Acero Corrugado - 3/8", "varillas"),
        ("Acero Corrugado - 1/2", "varillas"),
        ("Acero Corrugado - 5/8", "varillas"),
        ("Acero Corrugado - 3/4", "varillas"),
        ("Piedra Chancada 1/2", "m3"),
        ("Piedra Chancada 3/4", "m3"),
        ("Arena Gruesa", "m3"),
        ("Arena Fina", "m3"),
        ("Ladrillo King Kong", "millar"),
        ("Ladrillo Pandereta", "millar"),
        ("Madera Tornillo", "pie2"),
        ("Triplay 4x8x4mm", "planchas"),
        ("Clavos", "kg"),
        ("Alambre N°8", "kg"),
        ("Yeso", "bolsas"),
    ]
    for nombre, unidad in default:
        cursor.execute(
            "INSERT OR IGNORE INTO materiales_catalogo (nombre, unidad) VALUES (?, ?)",
            (nombre, unidad),
        )


def seed_subcontratas(cursor):
    if cursor.execute("SELECT COUNT(*) FROM subcontratas").fetchone()[0] > 0:
        return
    default = [
        ("De la empresa (Directo)", "Administración", ""),
        ("De casa", "Propietario", ""),
    ]
    for nombre, resp, tel in default:
        cursor.execute(
            "INSERT OR IGNORE INTO subcontratas (nombre, responsable, telefono) VALUES (?, ?, ?)",
            (nombre, resp, tel),
        )


# ═══════════════════════════════════════════════
# SECTORES CRUD
# ═══════════════════════════════════════════════

def get_sectores():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sectores ORDER BY nombre").fetchall()
    conn.close()
    return rows


def save_sector(nombre):
    conn = get_connection()
    conn.execute("INSERT INTO sectores (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()


def update_sector(sid, nombre):
    conn = get_connection()
    conn.execute("UPDATE sectores SET nombre=? WHERE id=?", (nombre, sid))
    conn.commit()
    conn.close()


def delete_sector(sid):
    conn = get_connection()
    conn.execute("DELETE FROM sectores WHERE id=?", (sid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# MATERIALES CATALOGO CRUD
# ═══════════════════════════════════════════════

def get_materiales_catalogo():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM materiales_catalogo ORDER BY nombre").fetchall()
    conn.close()
    return rows


def save_material_catalogo(nombre, unidad):
    conn = get_connection()
    conn.execute(
        "INSERT INTO materiales_catalogo (nombre, unidad) VALUES (?, ?)",
        (nombre, unidad),
    )
    conn.commit()
    conn.close()


def update_material_catalogo(mid, nombre, unidad):
    conn = get_connection()
    conn.execute(
        "UPDATE materiales_catalogo SET nombre=?, unidad=? WHERE id=?",
        (nombre, unidad, mid),
    )
    conn.commit()
    conn.close()


def delete_material_catalogo(mid):
    conn = get_connection()
    conn.execute("DELETE FROM materiales_catalogo WHERE id=?", (mid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# SUBCONTRATAS CRUD
# ═══════════════════════════════════════════════

def get_subcontratas():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM subcontratas ORDER BY nombre").fetchall()
    conn.close()
    return rows


def save_subcontrata(nombre, responsable, telefono):
    conn = get_connection()
    conn.execute(
        "INSERT INTO subcontratas (nombre, responsable, telefono) VALUES (?, ?, ?)",
        (nombre, responsable, telefono),
    )
    conn.commit()
    conn.close()


def update_subcontrata(sid, nombre, responsable, telefono):
    conn = get_connection()
    conn.execute(
        "UPDATE subcontratas SET nombre=?, responsable=?, telefono=? WHERE id=?",
        (nombre, responsable, telefono, sid),
    )
    conn.commit()
    conn.close()


def delete_subcontrata(sid):
    conn = get_connection()
    conn.execute("DELETE FROM subcontratas WHERE id=?", (sid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# PARTIDAS CRUD
# ═══════════════════════════════════════════════

def get_partidas(sector_id=None):
    conn = get_connection()
    if sector_id:
        rows = conn.execute(
            "SELECT p.*, s.nombre as sector_nombre FROM partidas p LEFT JOIN sectores s ON p.sector_id=s.id WHERE p.sector_id=? ORDER BY p.codigo, p.nombre",
            (sector_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT p.*, s.nombre as sector_nombre FROM partidas p LEFT JOIN sectores s ON p.sector_id=s.id ORDER BY p.codigo, p.nombre"
        ).fetchall()
    conn.close()
    return rows


def save_partida(codigo, nombre, descripcion, sector_id, unidad, metrado_total):
    conn = get_connection()
    conn.execute(
        "INSERT INTO partidas (codigo, nombre, descripcion, sector_id, unidad, metrado_total) VALUES (?, ?, ?, ?, ?, ?)",
        (codigo, nombre, descripcion, sector_id, unidad, metrado_total),
    )
    conn.commit()
    conn.close()


def update_partida(pid, codigo, nombre, descripcion, sector_id, unidad, metrado_total):
    conn = get_connection()
    conn.execute(
        "UPDATE partidas SET codigo=?, nombre=?, descripcion=?, sector_id=?, unidad=?, metrado_total=? WHERE id=?",
        (codigo, nombre, descripcion, sector_id, unidad, metrado_total, pid),
    )
    conn.commit()
    conn.close()


def delete_partida(pid):
    conn = get_connection()
    conn.execute("DELETE FROM partidas WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# REGISTRO DIARIO + AVANCE PARTIDA
# ═══════════════════════════════════════════════

def save_registro_diario(fecha, clima, observaciones):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO registro_diario (fecha, clima, observaciones) VALUES (?, ?, ?)",
        (fecha, clima, observaciones),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_registro_diario(fecha):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM registro_diario WHERE fecha=? ORDER BY id DESC LIMIT 1",
        (fecha,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_or_create_registro_diario(fecha):
    registro = get_registro_diario(fecha)
    if registro:
        return registro["id"]
    return save_registro_diario(fecha, "Soleado", "")


def get_registros_fechas():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT fecha FROM registro_diario ORDER BY fecha DESC"
    ).fetchall()
    conn.close()
    return [r["fecha"] for r in rows]


# ── Avance Partida ──

def save_avance(registro_id, partida_id, subcontrata_id, sector_id, operarios, oficiales, peones, horas, cantidad_ejecutada, observaciones):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO avance_partida (registro_id, partida_id, subcontrata_id, sector_id, num_operarios, num_oficiales, num_peones, horas_trabajadas, cantidad_ejecutada, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (registro_id, partida_id, subcontrata_id, sector_id, operarios, oficiales, peones, horas, cantidad_ejecutada, observaciones),
    )
    aid = cur.lastrowid
    conn.commit()
    conn.close()
    return aid


def get_avances(registro_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT a.*, p.nombre as partida_nombre, p.codigo as partida_codigo,
               p.unidad as partida_unidad, p.metrado_total,
               s.nombre as subcontrata_nombre,
               sc.nombre as sector_nombre
        FROM avance_partida a
        JOIN partidas p ON a.partida_id = p.id
        LEFT JOIN subcontratas s ON a.subcontrata_id = s.id
        LEFT JOIN sectores sc ON a.sector_id = sc.id
        WHERE a.registro_id = ?
        ORDER BY sc.nombre, p.codigo, p.nombre
        """,
        (registro_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_avance(avance_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT a.*, p.nombre as partida_nombre, p.codigo as partida_codigo,
               p.unidad as partida_unidad, p.metrado_total,
               s.nombre as subcontrata_nombre,
               sc.nombre as sector_nombre
        FROM avance_partida a
        JOIN partidas p ON a.partida_id = p.id
        LEFT JOIN subcontratas s ON a.subcontrata_id = s.id
        LEFT JOIN sectores sc ON a.sector_id = sc.id
        WHERE a.id = ?
        """,
        (avance_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_avance(aid, subcontrata_id, sector_id, operarios, oficiales, peones, horas, cantidad_ejecutada, observaciones):
    conn = get_connection()
    conn.execute(
        "UPDATE avance_partida SET subcontrata_id=?, sector_id=?, num_operarios=?, num_oficiales=?, num_peones=?, horas_trabajadas=?, cantidad_ejecutada=?, observaciones=? WHERE id=?",
        (subcontrata_id, sector_id, operarios, oficiales, peones, horas, cantidad_ejecutada, observaciones, aid),
    )
    conn.commit()
    conn.close()


def delete_avance(aid):
    conn = get_connection()
    conn.execute("DELETE FROM avance_partida WHERE id=?", (aid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# LEGACY: Daily Registry (old table)
# ═══════════════════════════════════════════════

def save_daily_registry(fecha, sector, clima, num_obreros, horas_trabajadas):
    conn = get_connection()
    conn.execute(
        "INSERT INTO daily_registry (fecha, sector, clima, num_obreros, horas_trabajadas) VALUES (?, ?, ?, ?, ?)",
        (fecha, sector, clima, num_obreros, horas_trabajadas),
    )
    conn.commit()
    conn.close()


def get_daily_registries(fecha=None):
    conn = get_connection()
    if fecha:
        rows = conn.execute(
            "SELECT * FROM daily_registry WHERE fecha = ? ORDER BY id", (fecha,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM daily_registry ORDER BY fecha DESC, id").fetchall()
    conn.close()
    return rows


def update_daily_registry(rid, sector, clima, num_obreros, horas_trabajadas):
    conn = get_connection()
    conn.execute(
        "UPDATE daily_registry SET sector=?, clima=?, num_obreros=?, horas_trabajadas=? WHERE id=?",
        (sector, clima, num_obreros, horas_trabajadas, rid),
    )
    conn.commit()
    conn.close()


def delete_daily_registry(rid):
    conn = get_connection()
    conn.execute("DELETE FROM daily_registry WHERE id=?", (rid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# LEGACY: Materials (old table)
# ═══════════════════════════════════════════════

def save_material(fecha, material, cantidad, unidad):
    conn = get_connection()
    conn.execute(
        "INSERT INTO materials (fecha, material, cantidad, unidad) VALUES (?, ?, ?, ?)",
        (fecha, material, cantidad, unidad),
    )
    conn.commit()
    conn.close()


def get_materials(fecha=None):
    conn = get_connection()
    if fecha:
        rows = conn.execute(
            "SELECT * FROM materials WHERE fecha = ? ORDER BY id", (fecha,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM materials ORDER BY fecha DESC, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_material(mid, material, cantidad, unidad):
    conn = get_connection()
    conn.execute(
        "UPDATE materials SET material=?, cantidad=?, unidad=? WHERE id=?",
        (material, cantidad, unidad, mid),
    )
    conn.commit()
    conn.close()


def delete_material(mid):
    conn = get_connection()
    conn.execute("DELETE FROM materials WHERE id=?", (mid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# LEGACY: Field Notes
# ═══════════════════════════════════════════════

def save_field_note(fecha, nota):
    conn = get_connection()
    conn.execute(
        "INSERT INTO field_notes (fecha, nota) VALUES (?, ?)",
        (fecha, nota),
    )
    conn.commit()
    conn.close()


def get_field_notes(fecha=None):
    conn = get_connection()
    if fecha:
        rows = conn.execute(
            "SELECT * FROM field_notes WHERE fecha = ? ORDER BY id", (fecha,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM field_notes ORDER BY fecha DESC, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_field_note(nid, nota):
    conn = get_connection()
    conn.execute(
        "UPDATE field_notes SET nota=? WHERE id=?",
        (nota, nid),
    )
    conn.commit()
    conn.close()


def delete_field_note(nid):
    conn = get_connection()
    conn.execute("DELETE FROM field_notes WHERE id=?", (nid,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════
# LEGACY: Photos
# ═══════════════════════════════════════════════

def save_photo(filename, fecha, sector, descripcion, ruta):
    conn = get_connection()
    conn.execute(
        "INSERT INTO photos (filename, fecha, sector, descripcion, ruta) VALUES (?, ?, ?, ?, ?)",
        (filename, fecha, sector, descripcion, ruta),
    )
    conn.commit()
    conn.close()


def get_photos(fecha=None):
    conn = get_connection()
    if fecha:
        rows = conn.execute(
            "SELECT * FROM photos WHERE fecha = ? ORDER BY id", (fecha,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM photos ORDER BY fecha DESC, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_photo(pid, sector, descripcion):
    conn = get_connection()
    conn.execute(
        "UPDATE photos SET sector=?, descripcion=? WHERE id=?",
        (sector, descripcion, pid),
    )
    conn.commit()
    conn.close()


def delete_photo(pid):
    conn = get_connection()
    conn.execute("DELETE FROM photos WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def get_all_fechas():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT fecha FROM daily_registry ORDER BY fecha DESC"
    ).fetchall()
    conn.close()
    return [r["fecha"] for r in rows]


# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════

def get_config(key, default=""):
    conn = get_connection()
    row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def set_config(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_all_config():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM config ORDER BY key").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ═══════════════════════════════════════════════
# AVANCES POR RANGO DE FECHAS
# ═══════════════════════════════════════════════

def get_avances_por_rango(fecha_inicio, fecha_fin):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT a.*, r.fecha, r.clima, p.nombre as partida_nombre, p.codigo as partida_codigo,
               p.unidad as partida_unidad, p.metrado_total,
               s.nombre as subcontrata_nombre,
               sc.nombre as sector_nombre
        FROM avance_partida a
        JOIN registro_diario r ON a.registro_id = r.id
        JOIN partidas p ON a.partida_id = p.id
        LEFT JOIN subcontratas s ON a.subcontrata_id = s.id
        LEFT JOIN sectores sc ON a.sector_id = sc.id
        WHERE r.fecha >= ? AND r.fecha <= ?
        ORDER BY r.fecha, sc.nombre, p.codigo, p.nombre
        """,
        (fecha_inicio, fecha_fin),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_registros_por_rango(fecha_inicio, fecha_fin):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM registro_diario WHERE fecha >= ? AND fecha <= ? ORDER BY fecha",
        (fecha_inicio, fecha_fin),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_materials_por_rango(fecha_inicio, fecha_fin):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM materials WHERE fecha >= ? AND fecha <= ? ORDER BY fecha",
        (fecha_inicio, fecha_fin),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_all_materiales_catalogo():
    conn = get_connection()
    conn.execute("DELETE FROM materiales_catalogo")
    conn.commit()
    conn.close()


def delete_all_partidas():
    conn = get_connection()
    conn.execute("DELETE FROM partidas")
    conn.commit()
    conn.close()


def get_field_notes_por_rango(fecha_inicio, fecha_fin):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM field_notes WHERE fecha >= ? AND fecha <= ? ORDER BY fecha",
        (fecha_inicio, fecha_fin),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
