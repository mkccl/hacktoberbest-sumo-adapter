from flask import Flask, jsonify
import threading
import traci
import traci.constants as tc
from supabase import create_client
import os
import logging
from sumolib import checkBinary
from typing import Dict, Any

app = Flask(__name__)

# Initialize Supabase client
SUPABASE_URL = "https://supabase.ccl-dev.com"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

simulation_thread = None
simulation_running = False

def clear_database():
    try:
        # Delete all simulator-generated vehicles
        response = supabase.table('vehicles').delete().eq('simulator', True).execute()
        return jsonify({'message': 'Database cleared successfully'}), 200
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return jsonify({'message': 'Failed to clear database'}), 500

def run_simulation():
    global simulation_running
    sumo_config_path = os.path.join(os.getcwd(), "osm", "berlin_sim.sumocfg")

    if not os.path.exists(sumo_config_path):
        logger.error(f"SUMO configuration file not found at {sumo_config_path}")
        return

    sumoCmd = [checkBinary('sumo'), "-c", sumo_config_path]

    logger.info(f"Starting SUMO simulation with command: {' '.join(sumoCmd)}")
    logger.info(f"SUMO_HOME: {os.environ.get('SUMO_HOME')}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Contents of osm directory: {os.listdir('osm')}")

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            logger.info("Starting SUMO simulation")
            traci.start(sumoCmd)

            while simulation_running and traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                vehicle_ids = traci.vehicle.getIDList()

                for vehicle_id in vehicle_ids:
                    position = traci.vehicle.getPosition(vehicle_id)
                    lon, lat = traci.simulation.convertGeo(position[0], position[1])
                    speed = traci.vehicle.getSpeed(vehicle_id)
                    timestamp = traci.simulation.getTime()

                    vehicle_data = {
                        'name': vehicle_id,
                        'description': f'Simulated vehicle {vehicle_id}',
                        'timestamp': timestamp,
                        'latitude': lat,
                        'longitude': lon,
                        'speed': speed,
                        'simulator': True,
                        'status': 'ON_THE_WAY'
                    }

                    try:
                        # Check if vehicle exists
                        existing_vehicle = supabase.table('vehicles')\
                            .select('id')\
                            .eq('name', vehicle_id)\
                            .execute()

                        if existing_vehicle.data:
                            # Update existing vehicle
                            logger.info(f"Updating vehicle {vehicle_id} at {lat}, {lon} with speed {speed}")
                            supabase.table('vehicles')\
                                .update(vehicle_data)\
                                .eq('name', vehicle_id)\
                                .execute()
                        else:
                            # Create new vehicle
                            logger.info(f"Creating new vehicle {vehicle_id} at {lat}, {lon} with speed {speed}")
                            supabase.table('vehicles')\
                                .insert(vehicle_data)\
                                .execute()

                    except Exception as e:
                        logger.error(f"Error handling vehicle {vehicle_id}: {e}")

            logger.info("Simulation completed successfully")
            break  # Exit the retry loop if simulation completes

        except traci.exceptions.FatalTraCIError as e:
            logger.error(f"TraCI error occurred: {e}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"Retrying simulation (attempt {retry_count + 1})")
            else:
                logger.error("Max retries reached. Stopping simulation.")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            break
        finally:
            try:
                traci.close()
            except:
                pass
            simulation_running = False

@app.route('/start', methods=['POST'])
def start_simulation():
    global simulation_thread, simulation_running
    if simulation_running:
        return jsonify({'message': 'Simulation already running'}), 400

    simulation_running = True
    simulation_thread = threading.Thread(target=run_simulation)
    simulation_thread.start()
    return jsonify({'message': 'Simulation started'}), 200

@app.route('/stop', methods=['POST'])
def stop_simulation():
    global simulation_running, simulation_thread
    if not simulation_running:
        return jsonify({'message': 'Simulation is not running'}), 400

    simulation_running = False
    # Wait for the simulation thread to finish
    simulation_thread.join()
    # Clear the database
    return clear_database()

@app.route('/status', methods=['GET'])
def simulation_status():
    status = 'running' if simulation_running else 'stopped'
    return jsonify({'simulation_status': status}), 200

@app.route('/clear', methods=['POST'])
def clear_database_request():
    return clear_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)