from flask import Blueprint, request, jsonify, current_app
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from services.weather_service import get_geolocation, get_forecast_data
from datetime import datetime
import time

weather_bp = Blueprint('weather', __name__)

# === Prometheus Metrics ===
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'Request latency (seconds)',
    ['endpoint']
)

@weather_bp.before_app_request
def before_request():
    request.start_time = time.time()

@weather_bp.after_app_request
def after_request(response):
    if hasattr(request, 'start_time'):
        latency = time.time() - request.start_time
        REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.path).observe(latency)
    return response

# === ROUTES ===

@weather_bp.route("/")
def home():
    return jsonify({"message": "Weather API is running"}), 200

@weather_bp.route("/search", methods=["GET"])
def search():
    city = request.args.get("city")
    country = request.args.get("country")

    if not city or not country:
        return jsonify({"error": "Missing city or country input."}), 400

    try:
        # 1. Получаем координаты
        coords, error = get_geolocation(city, country)
        if error:
            return jsonify({"error": error}), 400

        # 2. Получаем данные о погоде (это LIST словарей)
        forecast = get_forecast_data(coords["lat"], coords["lon"])
        
        if not forecast:
            return jsonify({"error": "No forecast data found"}), 404

        # === ИСПРАВЛЕННАЯ ЛОГИКА MONGODB ===
        db = current_app.config.get('db')
        if db is not None:
            # Так как forecast — это СПИСОК, берем первый элемент (сегодняшний день)
            today = forecast[0] 
            
            search_record = {
                "city": city,
                "country": country,
                "temp_max": today.get("temp_max"), # Ключи из вашего weather_service.py
                "temp_min": today.get("temp_min"),
                "description": today.get("description"),
                "icon": today.get("icon"),
                "timestamp": datetime.utcnow()
            }
            db.search_history.insert_one(search_record)
        # ===================================

        return jsonify({
            "city": city,
            "country": country,
            "forecast": forecast
        }), 200

    except Exception as e:
        # Логируем ошибку в консоль для отладки
        print(f"Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@weather_bp.route("/history", methods=["GET"])
def get_history():
    try:
        db = current_app.config.get('db')
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        # Получаем последние 10 записей, убирая _id (который не конвертируется в JSON)
        history = list(db.search_history.find({}, {"_id": 0}).sort("timestamp", -1).limit(10))
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@weather_bp.route("/health")
def health():
    return jsonify({"status": "OK"}), 200

@weather_bp.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}