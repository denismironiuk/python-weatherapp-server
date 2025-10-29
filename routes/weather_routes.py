from flask import Blueprint, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from services.weather_service import get_geolocation, get_forecast_data
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
    # Record request start time
    request.start_time = time.time()


@weather_bp.after_app_request
def after_request(response):
    # Calculate latency and update metrics
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.path).observe(latency)
    return response


# === ROUTES ===

@weather_bp.route("/")
def home():
    # Simple message for API root
    return jsonify({"message": "Weather API is running"}), 200


@weather_bp.route("/search", methods=["GET"])
def search():
    city = request.args.get("city")
    country = request.args.get("country")

    if not city or not country:
        return jsonify({"error": "Missing city or country input."}), 400

    try:
        coords, error = get_geolocation(city, country)
        if error:
            return jsonify({"error": error}), 400

        forecast = get_forecast_data(coords["lat"], coords["lon"])
        return jsonify({
            "city": city,
            "country": country,
            "forecast": forecast
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@weather_bp.route("/health")
def health():
    return jsonify({"status": "OK"}), 200


@weather_bp.route("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
