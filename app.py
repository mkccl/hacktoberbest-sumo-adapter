from appwrite.query import Query
from flask import Flask, jsonify
import threading
import traci
import traci.constants as tc
from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.services.databases import Databases
import os
import logging
from sumolib import checkBinary

app = Flask(__name__)

# Initialize Appwrite client
client = Client()
client.set_endpoint('https://cloud.appwrite.io/v1')
client.set_project('tasktrek')
client.set_key('standard_02cc31e4bdc8021a5fbaa7672017313ec50a64f3c5506f089eac4df36ec128f522dea3623dbeb3ce47f6a0296b3840e6798c42cab9570c8588d2fe4a13590862a0ca1811111c0d772357f9b41ced403fd0739493c833a84eec5473b06c2b39977c9b27c50bdd21fb72e9cac91fd066b56777e5f57625f1c13310a6d7a05073ab')

databaseId = 'tasktrek-db'
collectionId = 'vehicles'

databases = Databases(client)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

simulation_thread = None
simulation_running = False

def clear_database():
  # Clear the database
  try:
    # Retrieve all documents in the collection
    documents = databases.list_documents(
      database_id=databaseId,
      collection_id=collectionId,
      queries=[Query.limit(100), Query.equal('simulator', True)]  # Adjust limit as needed
    )

    # Delete each document
    for document in documents['documents']:
      databases.delete_document(
        database_id=databaseId,
        collection_id=collectionId,
        document_id=document['$id']
      )
    # Return success response
    return jsonify({'message': 'Database cleared successfully'}), 200
  except AppwriteException as e:
    print(f"Error clearing database: {e}")
    return jsonify({'message': 'Failed to clear database'}), 500

import logging
import traci
from appwrite.exception import AppwriteException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

          data = {
            'vehicle_id': vehicle_id,
            'timestamp': timestamp,
            'latitude': lat,
            'longitude': lon,
            'speed': speed,
            'simulator': True,
            'name': vehicle_id,
            'status': 'ON_THE_WAY'
          }

          document_id = vehicle_id

          try:
            logger.info(f"Vehicle {vehicle_id} at {lat}, {lon} with speed {speed} saved")
            # Update existing document
            databases.update_document(
              database_id=databaseId,
              collection_id=collectionId,
              document_id=document_id,
              data=data
            )
          except AppwriteException as e:
            logger.info(f"AppwriteException")

            if e.code == 404:
              # Document doesn't exist, create it
              databases.create_document(
                database_id=databaseId,
                collection_id=collectionId,
                document_id=document_id,
                data=data
              )
            else:
              print(f"Error handling document for vehicle {vehicle_id}: {e}")
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
