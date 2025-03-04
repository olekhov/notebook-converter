# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем необходимые системные зависимости для pdflatex и русского языка
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-plain-generic \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-cyrillic \
    texlive-xetex \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости
COPY Pipfile Pipfile.lock ./

# Устанавливаем зависимости
RUN pip install pipenv
RUN pipenv install --system --deploy

# Копируем исходный код приложения
COPY . .

# Указываем порт, который будет использовать приложение
EXPOSE 5000

# Команда для запуска приложения
# DEBUG
# CMD ["flask", "run", "--host=0.0.0.0"]

# PRODUCTION
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
