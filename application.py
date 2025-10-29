import os
from flask import Flask
from flask_cors import CORS
from routes.weather_routes import weather_bp

app = Flask(__name__)

# читаем домен из переменной окружения, которую задаёт Kubernetes
allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")  # * — по умолчанию, если не указано

# включаем CORS динамически
CORS(app, origins=[allowed_origin])

# регистрируем маршруты (blueprint)
app.register_blueprint(weather_bp)



if __name__ == "__main__":
    # запускаем приложение
    app.run(host="0.0.0.0", port=5000, debug=True)
