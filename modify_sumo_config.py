import xml.etree.ElementTree as ET
import os

def modify_sumo_config(file_path):
  tree = ET.parse(file_path)
  root = tree.getroot()

  # Define a mapping for unknown vehicle classes
  class_mapping = {
    'container': 'truck',
    'cable_car': 'rail',
    'subway': 'rail',
    'aircraft': 'ignoring',
    'wheelchair': 'pedestrian',
    'scooter': 'bicycle',
    'drone': 'ignoring'
  }

  # Modify vehicle classes in the configuration
  for vtype in root.findall(".//vType"):
    vclass = vtype.get('vClass')
    if vclass in class_mapping:
      vtype.set('vClass', class_mapping[vclass])

  # Write the modified XML back to the file
  tree.write(file_path)

# Path to your SUMO configuration file
sumo_config_path = os.path.join('osm', 'berlin_sim.sumocfg')

if os.path.exists(sumo_config_path):
  modify_sumo_config(sumo_config_path)
  print(f"Modified SUMO configuration: {sumo_config_path}")
else:
  print(f"SUMO configuration file not found: {sumo_config_path}")

# Modify any additional XML files in the osm directory
for filename in os.listdir('osm'):
  if filename.endswith('.xml'):
    file_path = os.path.join('osm', filename)
    modify_sumo_config(file_path)
    print(f"Modified XML file: {file_path}")
