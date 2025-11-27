# Dockerfile
# IL 3.1: Usar una imagen base segura y ligera
FROM python:3.11-slim

# Crea y establece el directorio de trabajo
WORKDIR /usr/src/app

# Copia el archivo de dependencias
COPY requirements.txt ./

# IL 3.3: Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
# Esto copiará vunerable_app.py, create_db.py, y la database.db local (que no debe usarse)
COPY . .

# CORRECCIÓN DE ERROR: Eliminar la base de datos local copiada para forzar la creación limpia dentro del contenedor
RUN rm -f database.db

# IL 3.1: Crea la base de datos limpia DENTRO de la imagen
# Esto garantiza que el entorno de despliegue sea fresco y consistente.
RUN python create_db.py

# Expone el puerto que usa Flask
EXPOSE 8080

# Comando para correr la aplicación
CMD [ "python", "vulnerable_app.py" ]