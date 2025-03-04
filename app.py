#!/usr/bin/env python3

import os
import subprocess
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
import logging
import datetime
import shutil
import tempfile


# Настройка логирования
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат вывода
)


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

PASSWORD = os.getenv("APP_PASSWORD", "default_password")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        if file:
            if request.form.get("password") != PASSWORD:
                app.logger.error(f"Bad bassword: {request.form.get('password')}")
                return "Invalid password"
            if "file" not in request.files:
                return "No file part"

            # Получаем текущее время в нужном формате
            timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

            filename = secure_filename(file.filename)
            save_filename = f"{timestamp}-{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)
            file.save(filepath)
            app.logger.info(f"Uploaded file: {filepath}")

            temp_dir = tempfile.mkdtemp()
            app.logger.info(f"Temporary dir: {temp_dir}")

            shutil.copy(filepath, os.path.join(temp_dir, filename))

            tex_filename = os.path.splitext(filename)[0] + ".tex"
            tex_path = os.path.join(temp_dir, tex_filename)
            pdf_filename = os.path.splitext(filename)[0] + ".pdf"
            pdf_path = os.path.join(temp_dir, pdf_filename)

            try:
                # Конвертируем в TeX
                subprocess.run([
                    "jupyter", "nbconvert", "--to", "latex", filename, "--output", tex_filename
                ], cwd=temp_dir, check=True)

                # Добавляем поддержку русского языка в TeX
                with open(tex_path, "r", encoding="utf-8") as tex_file:
                    tex_content = tex_file.readlines()

                for i, line in enumerate(tex_content):
                    if "\\documentclass" in line:
                        #tex_content.insert(i + 1, "\\usepackage[utf8]{inputenc}\n")
                        tex_content.insert(i + 1, "\\usepackage[russian]{babel}\n")
                        break

                with open(tex_path, "w", encoding="utf-8") as tex_file:
                    tex_file.writelines(tex_content)

                # Компилируем TeX в PDF
                subprocess.run(["pdflatex", tex_filename], cwd=temp_dir, check=True)
                return send_file(pdf_path, as_attachment=True)
            except subprocess.CalledProcessError:
                return "Error converting file."
            finally:
                # Удаляем содержимое временной папки и саму папку после отправки
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)  # Удаление папки и её содержимого
                        else:
                            os.remove(file_path)  # Удаление файла
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}")
                os.rmdir(temp_dir)

    return render_template("upload.html")


if __name__ == "__main__":
    app.run(debug=True)
