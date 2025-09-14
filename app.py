from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from io import StringIO, BytesIO
import csv
import random
import datetime
import os


def create_app() -> Flask:
    # Point Flask to React build folder (dist from Vite)
    app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "my-app/build"),
    static_url_path="/"
)

    

    # Allow CORS for API routes (useful in dev; not really needed once Flask serves frontend)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ---------------------------
    # API Endpoints
    # ---------------------------
    @app.get("/api")
    def api_index() -> tuple:
        return (
            jsonify(
                {
                    "message": "API root",
                    "endpoints": [
                        "GET /api/health",
                        "POST /api/assessment",
                        "GET /api/environmental-impact",
                        "GET /api/circularity-indicators",
                        "GET /api/flow-data",
                        "GET /api/pie-data",
                        "POST /api/reports/export",
                    ],
                }
            ),
            200,
        )

    @app.get("/api/health")
    def health() -> tuple:
        return jsonify({"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}), 200

    @app.post("/api/assessment")
    def run_assessment() -> tuple:
        payload = request.get_json(silent=True) or {}
        process_data = payload.get("processData", {})

        expected_fields = [
            "material",
            "production",
            "rawMaterial",
            "recycledContent",
            "energyUse",
            "transport",
            "endOfLife",
        ]
        missing_fields = [f for f in expected_fields if f not in process_data]

        recycled = float(process_data.get("recycledContent", 50) or 0)
        raw_material = float(process_data.get("rawMaterial", 50) or 0)
        energy_use = process_data.get("energyUse", "") or "medium"
        transport = process_data.get("transport", "") or "road"

        base_circularity = 50 + (recycled - raw_material) * 0.3
        if energy_use.lower() in ("low", "renewable"):
            base_circularity += 10
        if transport.lower() in ("rail", "sea"):
            base_circularity += 5
        base_circularity = max(0, min(100, round(base_circularity)))

        environmental_score = 60 + int((recycled * 0.2) - (raw_material * 0.1))
        environmental_score = max(0, min(100, environmental_score))

        random.seed((process_data.get("material") or "") + (process_data.get("production") or ""))
        recommendations = [
            "Increase recycled content to reduce virgin input dependency",
            "Optimize transport routes and prefer rail/sea logistics",
            "Adopt closed-loop water systems in processing",
            "Redesign product for easier disassembly and reuse",
        ]
        random.shuffle(recommendations)

        result = {
            "circularityScore": base_circularity,
            "environmentalScore": environmental_score,
            "recommendations": recommendations[:4],
            "missingParams": max(0, len(missing_fields)),
            "debug": {"missingFields": missing_fields},
        }

        return jsonify(result), 200

    @app.get("/api/environmental-impact")
    def get_environmental_impact() -> tuple:
        data = [
            {"name": "CO2 Emissions", "conventional": 850, "circular": 320},
            {"name": "Energy Use", "conventional": 1200, "circular": 680},
            {"name": "Water Use", "conventional": 400, "circular": 180},
            {"name": "Waste Gen.", "conventional": 200, "circular": 45},
        ]
        return jsonify(data), 200

    @app.get("/api/circularity-indicators")
    def get_circularity_indicators() -> tuple:
        data = [
            {"name": "Recycled Content", "value": 65, "target": 80},
            {"name": "Resource Efficiency", "value": 72, "target": 85},
            {"name": "Product Life Ext.", "value": 58, "target": 75},
            {"name": "Reuse Potential", "value": 43, "target": 60},
        ]
        return jsonify(data), 200

    @app.get("/api/flow-data")
    def get_flow_data() -> tuple:
        data = [
            {"stage": "Extraction", "material": 100, "recycled": 0},
            {"stage": "Processing", "material": 95, "recycled": 60},
            {"stage": "Manufacturing", "material": 90, "recycled": 85},
            {"stage": "Use", "material": 88, "recycled": 83},
            {"stage": "End-of-Life", "material": 25, "recycled": 75},
        ]
        return jsonify(data), 200

    @app.get("/api/pie-data")
    def get_pie_data() -> tuple:
        data = [
            {"name": "Recycled", "value": 45, "color": "#10b981"},
            {"name": "Virgin", "value": 35, "color": "#6366f1"},
            {"name": "Recovered", "value": 20, "color": "#f59e0b"},
        ]
        return jsonify(data), 200

    @app.post("/api/reports/export")
    def export_report_csv():
        rows = [
            ["Metric", "Conventional", "Circular"],
            ["CO2 Emissions", 850, 320],
            ["Energy Use", 1200, 680],
            ["Water Use", 400, 180],
            ["Waste Gen.", 200, 45],
        ]

        string_buffer = StringIO()
        writer = csv.writer(string_buffer)
        writer.writerows(rows)
        string_buffer.seek(0)

        byte_buffer = BytesIO(string_buffer.getvalue().encode("utf-8"))
        filename = f"circularmetals_report_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
        return send_file(
            byte_buffer,
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )

    # ---------------------------
    # Frontend serving routes
    # ---------------------------
    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, "index.html")

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(app.static_folder, "index.html")

    return app



app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
