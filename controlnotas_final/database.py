import mysql.connector
import pandas as pd

def conectar():
    conexion = mysql.connector.connect(
        host="mysql-johanseba.alwaysdata.net",
        user="johanseba_admin",
        password="Joseb2006.19",
        database="johanseba_notas2026"
    )
    return conexion

# obtener usuarios
def obtenerusuarios(username):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE username=%s", (username,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

# obtener los estudiantes
def obtenerestudiantes():
    conn = conectar()
    query = "SELECT * FROM estudiantes"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# PUNTO 1: verificar si un estudiante ya existe (por nombre + carrera)
def estudiante_existe(nombre, carrera):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM estudiantes WHERE Nombre=%s AND Carrera=%s",
        (nombre, carrera)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# registrar estudiante con validacion de duplicado
def insertar_estudiante(nombre, edad, carrera, nota1, nota2, nota3, promedio, desempeno):
    if estudiante_existe(nombre, carrera):
        return False  # ya existe, no insertar
    conn = conectar()
    cursor = conn.cursor()
    query = """INSERT INTO estudiantes(Nombre,Edad,Carrera,nota1,nota2,nota3,Promedio,Desempeño)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""
    cursor.execute(query, (nombre, edad, carrera, nota1, nota2, nota3, promedio, desempeno))
    conn.commit()
    conn.close()
    return True




if __name__ == "__main__":
    conn = conectar()
    print("Conexion exitosa")
    conn.close()
