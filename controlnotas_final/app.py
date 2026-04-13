from flask import Flask, render_template, request, redirect, session, send_file, flash
from database import conectar, obtenerusuarios, insertar_estudiante, estudiante_existe
from dashprincipal import creartablero
import pandas as pd
import unicodedata
import io
import os

app = Flask(__name__)
app.secret_key = "40414732"

server = app  

# crear dashboard
creartablero(app)

# evitar cache en paginas protegidas
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# LOGIN / LOGOUT

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usuario = obtenerusuarios(username)
        if usuario:
            if usuario["password"] == password:
                session["username"] = usuario["username"]
                session["rol"] = usuario["rol"]
                return redirect("/dashprincipal")
            else:
                return render_template("login.html", error="Contraseña incorrecta")
        else:
            return render_template("login.html", error="Usuario no existe")
    return render_template("login.html")

@app.route("/dashprincipal")
def dashprinci():
    if "username" not in session:
        return redirect("/")
    return render_template("dashprinci.html", usuario=session["username"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# UTILIDADES

def quitar_acentos(texto):
    """Quita tildes y caracteres especiales."""
    if pd.isna(texto):
        return texto
    texto = str(texto)
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def calculardesempeño(prom):
    if prom >= 4.5:
        return "Excelente"
    elif prom >= 4:
        return "Bueno"
    elif prom >= 3:
        return "Regular"
    else:
        return "Bajo"


# REGISTRO MANUAL CON VALIDACION DUPLICADO

@app.route("/registro_estudiante", methods=["GET", "POST"])
def registroestudiante():
    if "username" not in session:
        return redirect("/")

    if request.method == "POST":
        nombre  = quitar_acentos(request.form["txtnombre"].strip()).title()
        edad    = int(request.form["txtedad"])
        carrera = quitar_acentos(request.form["txtcarrera"].strip()).title()
        nota1   = float(request.form["txtnota1"])
        nota2   = float(request.form["txtnota2"])
        nota3   = float(request.form["txtnota3"])

        # Validaciones básicas
        if edad < 0:
            return render_template("registro_estudiante.html",
                                   error="La edad no puede ser negativa.")
        if not all(0 <= n <= 5 for n in [nota1, nota2, nota3]):
            return render_template("registro_estudiante.html",
                                   error="Las notas deben estar entre 0 y 5.")

        promedio  = round((nota1 + nota2 + nota3) / 3, 2)
        desempeno = calculardesempeño(promedio)

        # insertar_estudiante devuelve False si ya existe
        insertado = insertar_estudiante(nombre, edad, carrera, nota1, nota2, nota3,
                                        promedio, desempeno)
        if not insertado:
            return render_template("registro_estudiante.html",
                                   error=f"⚠️ El estudiante '{nombre}' ya está registrado en '{carrera}'.")

        return redirect("/dashprincipal")

    return render_template("registro_estudiante.html")


# CARGA MASIVA

@app.route("/cargamasiva", methods=["GET", "POST"])
def carga_masiva():
    if "username" not in session:
        return redirect("/")

    if request.method == "POST":
        archivo = request.files["txtarchivo"]
        df_original = pd.read_excel(archivo)

        rechazados = []   
        insertados  = 0
        duplicados  = 0

        for _, row in df_original.iterrows():
            motivo = []

            #  Verificar datos faltantes 
            campos = ["Nombre", "Carrera", "Edad", "Nota1", "Nota2", "Nota3"]
            faltantes = [c for c in campos if pd.isna(row.get(c))]
            if faltantes:
                motivo.append(f"Datos faltantes: {', '.join(faltantes)}")

            if motivo:
                fila = row.to_dict()
                fila["Motivo_Rechazo"] = " | ".join(motivo)
                rechazados.append(fila)
                continue

            # Limpiar texto 
            nombre  = quitar_acentos(str(row["Nombre"]).strip()).title()
            carrera = quitar_acentos(str(row["Carrera"]).strip()).title()
            edad    = row["Edad"]
            nota1   = row["Nota1"]
            nota2   = row["Nota2"]
            nota3   = row["Nota3"]

            # Validar edad negativa 
            if edad < 0:
                motivo.append("Edad negativa")

            # Validar notas 
            for etiqueta, nota in [("Nota1", nota1), ("Nota2", nota2), ("Nota3", nota3)]:
                if nota < 0 or nota > 5:
                    motivo.append(f"{etiqueta} inválida ({nota})")

            if motivo:
                fila = row.to_dict()
                fila["Nombre"]  = nombre
                fila["Carrera"] = carrera
                fila["Motivo_Rechazo"] = " | ".join(motivo)
                rechazados.append(fila)
                continue

            # Calcular promedio y desempeño 
            promedio  = round((nota1 + nota2 + nota3) / 3, 2)
            desempeno = calculardesempeño(promedio)

            #  verificar duplicado contra la BD 
            if estudiante_existe(nombre, carrera):
                fila = row.to_dict()
                fila["Nombre"]  = nombre
                fila["Carrera"] = carrera
                fila["Motivo_Rechazo"] = "Estudiante duplicado (ya existe en la BD)"
                rechazados.append(fila)
                duplicados += 1
                continue

            # Insertar en BD 
            conn   = conectar()
            cursor = conn.cursor()
            query  = """INSERT INTO estudiantes(Nombre,Edad,Carrera,nota1,nota2,nota3,Promedio,Desempeño)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(query, (nombre, edad, carrera, nota1, nota2, nota3,
                                   promedio, desempeno))
            conn.commit()
            conn.close()
            insertados += 1

        total_rechazados = len(rechazados)

        # generar Excel de rechazados 
        ruta_rechazados = None
        if rechazados:
            df_rechazados = pd.DataFrame(rechazados)
            ruta_rechazados = os.path.join("static", "rechazados.xlsx")
            os.makedirs("static", exist_ok=True)
            df_rechazados.to_excel(ruta_rechazados, index=False)

        #  pasar estadísticas a la plantilla
        #  redirige al dashboard con flag para limpiar filtros
        return render_template(
            "resultado_carga.html",
            insertados=insertados,
            rechazados=total_rechazados,
            duplicados=duplicados,
            tiene_rechazados=ruta_rechazados is not None
        )

    return render_template("carga_masiva.html")

# Descarga del archivo de rechazados 
@app.route("/descargar_rechazados")
def descargar_rechazados():
    
    ruta = os.path.join("static", "rechazados.xlsx")
    if os.path.exists(ruta): 

        return send_file(ruta, as_attachment=True, download_name="rechazados.xlsx")
    return "No hay archivo disponible", 404

print("HOST:", os.getenv("MYSQLHOST"))
print("PORT:", os.getenv("MYSQLPORT"))
print("USER:", os.getenv("MYSQLUSER"))
print("PASSWORD:", os.getenv("MYSQLPASSWORD"))
print("DATABASE:", os.getenv("MYSQLDATABASE"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# if __name__ == "__main__":
#     app.run(debug=True)
