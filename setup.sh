#!/bin/bash
# setup.sh – установка зависимостей и подготовка окружения

# Проверка наличия python3
if ! command -v python3 &> /dev/null
then
    echo "Python3 не найден. Установите Python3 и повторите попытку."
    exit 1
fi

# Если требуется, создаем виртуальное окружение (пример для python-venv)
if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем pip и устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

echo "Окружение подготовлено. Теперь можно запускать генератор проекта через терминал."
