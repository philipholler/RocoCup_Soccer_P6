import subprocess
import time

from player.player import WorldView
from uppaal.uppaal_model import UPPAAL_MODEL
from uppaal import VERIFYTA_MODELS_PATH, VERIFYTA_OUTPUT_DIR_PATH, VERIFYTA_QUERIES_PATH, VERIFYTA_PATH


def generate_strategy(wv: WorldView, xml_file_name: str, queries_file_name: str):
    # Create model
    model = UPPAAL_MODEL(xml_file_name)
    # Update model according to world view
    update_xml_file(wv, model)

    # Generate strategy command
    # verifyta_path --print-strategies outputdir xml_path queries_dir learning-method?
    command = "{0} --print-strategies {1} {2} {3}".format(VERIFYTA_PATH, VERIFYTA_OUTPUT_DIR_PATH
                                                          , VERIFYTA_MODELS_PATH / xml_file_name
                                                          , VERIFYTA_QUERIES_PATH / queries_file_name)
    print(command)
    # Run uppaal with the arguments given
    verifyta = subprocess.Popen(command, shell=True)

    # Wait for uppaal to finish generating and printing strategy
    while verifyta.poll() is None:
        time.sleep(0.001)

    # 3. Input strategy to coach
    # todo return strategy??
    return


def update_xml_file(wv, model: UPPAAL_MODEL):
    pass

generate_strategy(WorldView(0), 'MV_mini_projekt_2.xml', 'SimplePassingModel.q')