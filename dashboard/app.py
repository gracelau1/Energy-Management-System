from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta, date
import json
import sys
import os
import threading
import time
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation_runner import SmartLightingController, room_config

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

controller = SmartLightingController(room_config)

# Global flags
simulation_paused = True
simulation_running = False
csv_uploaded = False
config_uploaded = False


def background_simulation():
    global simulation_paused, simulation_running
    while True:
        if simulation_running and not simulation_paused:
            controller.advance_simulation_time(10)
        time.sleep(1)


threading.Thread(target=background_simulation, daemon=True).start()


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/data")
def api_data():
    return jsonify({
        "sim_time": controller.simulation_time.strftime("%H:%M:%S"),
        "states": controller.get_states(),
        "log": controller.get_log(),
        "room_energy": controller.get_energy_per_room(),
        "room_energy_no_ems": controller.get_energy_per_room_no_ems(),
        "room_energy_saved": controller.get_energy_per_room_saved(),
        "energy": controller.get_energy_totals(),
        "csv_uploaded": csv_uploaded,
        "config_uploaded": config_uploaded
    })


@app.route("/upload", methods=["POST"])
def upload_csv():
    global csv_uploaded
    if 'csv_file' not in request.files:
        return redirect(url_for('dashboard'))
    file = request.files['csv_file']
    if file.filename.endswith(".csv"):
        path = "uploaded.csv"
        file.save(path)
        controller.process_csv(path)
        csv_uploaded = True
    return redirect(url_for('dashboard'))


@app.route("/upload_config", methods=["POST"])
def upload_config():
    global config_uploaded, controller
    if 'config_file' not in request.files:
        return redirect(url_for('dashboard'))
    
    file = request.files['config_file']
    if file.filename.endswith((".json", ".txt")):
        content = file.read().decode('utf-8')

        # Wrap it in curly braces if user forgot
        if not content.strip().startswith("{"):
            content = "{" + content + "}"

        try:
            new_config = json.loads(content)
            if isinstance(new_config, dict):
                controller = SmartLightingController(new_config)
                config_uploaded = True
                return redirect(url_for('dashboard'))
        except Exception as e:
            print("Config upload error:", e)
    
    return redirect(url_for('dashboard'))


@app.route("/api/start", methods=["POST"])
def api_start():
    global simulation_paused, simulation_running, csv_uploaded, config_uploaded
    if csv_uploaded and config_uploaded:
        simulation_paused = False
        simulation_running = True
        return jsonify({"message": "Simulation started"}), 200
    else:
        return jsonify({"error": "Upload CSV movement and config first"}), 400


@app.route("/api/pause", methods=["POST"])
def api_pause():
    global simulation_paused
    simulation_paused = True
    return jsonify({"message": "Simulation paused"}), 200


@app.route("/api/resume", methods=["POST"])
def api_resume():
    global simulation_paused
    simulation_paused = False
    return jsonify({"message": "Simulation resumed"}), 200


@app.route("/api/set_time", methods=["POST"])
def api_set_time():
    data = request.get_json()
    time_str = data.get("time")
    if not time_str:
        return jsonify({"error": "No time provided"}), 400
    try:
        parsed_time = datetime.strptime(time_str, "%H:%M")
    except ValueError:
        try:
            parsed_time = datetime.strptime(time_str, "%H:%M:%S")
        except ValueError:
            return jsonify({"error": "Invalid time format"}), 400
    controller.simulation_time = controller.simulation_time.replace(
        hour=parsed_time.hour,
        minute=parsed_time.minute,
        second=getattr(parsed_time, 'second', 0),
        microsecond=0
    )
    controller.last_energy_calc_time = None
    return jsonify({"message": f"Simulation time set to {time_str}"}), 200


@app.route("/api/fastforward", methods=["POST"])
def api_fastforward():
    global simulation_paused, simulation_running

    if not simulation_running:
        return jsonify({"error": "Simulation is not running"}), 400

    try:
        next_day = controller.simulation_time + timedelta(days=1)
        target_time = next_day.replace(hour=8, minute=0, second=0, microsecond=0)

        while controller.simulation_time < target_time:
            controller.advance_simulation_time(10)

        return jsonify({
            "message": "Simulation fast-forwarded to next day 8AM",
            "final_time": controller.simulation_time.strftime("%H:%M:%S"),
            "energy": controller.get_energy_totals()
        }), 200

    except Exception as e:
        print(f"Error during fastforward: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/skip_to_9pm", methods=["POST"])
def api_skip_to_9pm():
    global simulation_paused, simulation_running

    if not simulation_running:
        return jsonify({"error": "Simulation is not running"}), 400

    try:
        today_9pm = controller.simulation_time.replace(hour=21, minute=0, second=0, microsecond=0)
        if controller.simulation_time >= today_9pm:
            return jsonify({"message": "Already past 9PM", "energy": controller.get_energy_totals()}), 200

        while controller.simulation_time < today_9pm:
            controller.advance_simulation_time(10)

        return jsonify({
            "message": "Simulation skipped to 9PM",
            "final_time": controller.simulation_time.strftime("%H:%M:%S"),
            "energy": controller.get_energy_totals()
        }), 200

    except Exception as e:
        print(f"Error during skip to 9PM: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
