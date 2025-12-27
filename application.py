import os
from flask import Flask
from flask_cors import CORS
from routes.weather_routes import weather_bp
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv # Не забудьте: pip install python-dotenv

# Загружаем переменные из файла .env (только для локальной разработки)
load_dotenv()

app = Flask(__name__)

# --- КОНФИГУРАЦИЯ ИЗ ОБЛАКА/ОКРУЖЕНИЯ ---

# ТЕПЕРЬ ТУТ НЕТ ПАРОЛЯ. Только имя переменной.
uri = os.getenv("MONGO_URI")
allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")

# Проверка: если URI не найден, мы не запускаем приложение
if not uri:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения MONGO_URI не установлена!")
    print("Проверьте файл .env или настройки окружения.")
    exit(1)

# Подключение к MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("✅ Успешное подключение к MongoDB Atlas!")
    app.config['db'] = client.get_database("weather_db") 
except Exception as e:
    print(f"❌ Ошибка подключения к базе: {e}")
    # В продакшене тут можно тоже сделать exit(1)

# Настройка CORS
CORS(app, origins=[allowed_origin])

# Регистрация роутов
app.register_blueprint(weather_bp)

if __name__ == "__main__":
    # Порт тоже лучше брать из окружения (для EKS/Heroku/Render)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)