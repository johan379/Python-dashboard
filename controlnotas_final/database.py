import mysql.connector
import pandas as pd

# ─────────────────────────────────────────
# CONEXIÓN
# ─────────────────────────────────────────
def conectar():
    return mysql.connector.connect(
        host="mysql-johanseba.alwaysdata.net",
        user="johanseba_admin",
        password="Joseb2006.19",
        database="johanseba_notas2026",
        port=3306
    )

# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
def obtenerusuarios(username):
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM usuarios WHERE username=%s",
            (username,)
        )

        usuario = cursor.fetchone()
        conn.close()
        return usuario

    except Exception as e:
        print("❌ ERROR LOGIN:", e)
        return None


# ─────────────────────────────────────────
# OBTENER ESTUDIANTES (PARA DASH)
# ─────────────────────────────────────────
def obtenerestudiantes():
    try:
        conn = conectar()
        query = "SELECT * FROM estudiantes"
        df = pd.read_sql(query, conn)

        # 🔴 LIMPIAR NOMBRES DE COLUMNAS
        df.columns = df.columns.str.strip().str.lower()

        # 🔁 NORMALIZAR NOMBRES
        df = df.rename(columns={
            "nombre": "Nombre",
            "edad": "Edad",
            "carrera": "Carrera",
            "nota1": "Nota1",
            "nota2": "Nota2",
            "nota3": "Nota3",
            "promedio": "Promedio",
            "desempeno": "Desempeño",
            "desempeño": "Desempeño"
        })

        # 🔴 ASEGURAR TIPOS NUMÉRICOS
        if "Edad" in df.columns:
            df["Edad"] = pd.to_numeric(df["Edad"], errors="coerce")

        if "Promedio" in df.columns:
            df["Promedio"] = pd.to_numeric(df["Promedio"], errors="coerce")

        # eliminar datos dañados
        df = df.dropna(subset=["Edad", "Promedio"])

        print("✅ Datos cargados:", len(df))
        print(df.head())

        conn.close()
        return df

    except Exception as e:
        print("❌ ERROR AL CARGAR ESTUDIANTES:", e)
        return pd.DataFrame()


# ─────────────────────────────────────────
# VALIDAR SI YA EXISTE
# ─────────────────────────────────────────
def estudiante_existe(nombre, carrera):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM estudiantes WHERE Nombre=%s AND Carrera=%s",
            (nombre, carrera)
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    except Exception as e:
        print("❌ ERROR VALIDANDO:", e)
        return False


# ─────────────────────────────────────────
# INSERTAR ESTUDIANTE
# ─────────────────────────────────────────
def insertar_estudiante(nombre, edad, carrera, nota1, nota2, nota3, promedio, desempeno):
    try:
        # validar duplicado
        if estudiante_existe(nombre, carrera):
            print("⚠️ Estudiante ya existe")
            return False

        conn = conectar()
        cursor = conn.cursor()

        query = """
        INSERT INTO estudiantes
        (Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(query, (
            nombre,
            edad,
            carrera,
            nota1,
            nota2,
            nota3,
            promedio,
            desempeno
        ))

        conn.commit()
        conn.close()

        print("✅ Estudiante insertado correctamente")
        return True

    except Exception as e:
        print("❌ ERROR AL INSERTAR:", e)
        return False


# ─────────────────────────────────────────
# TEST DE CONEXIÓN
# ─────────────────────────────────────────
if __name__ == "__main__":
    try:
        conn = conectar()
        print("✅ Conexión exitosa")
        conn.close()
    except Exception as e:
        print("❌ ERROR DE CONEXIÓN:", e)