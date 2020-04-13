import subprocess
import time
import re
from os import fdopen, remove

from pathlib import Path
from shutil import copymode, move
from tempfile import mkstemp

from player.player import WorldView
from uppaal.uppaal_model import UPPAAL_MODEL
from uppaal import VERIFYTA_MODELS_PATH, VERIFYTA_OUTPUT_DIR_PATH, VERIFYTA_QUERIES_PATH, VERIFYTA_PATH


def generate_strategy(wv: WorldView, xml_file_name: str, queries_file_name: str):
    # Create model
    model = UPPAAL_MODEL(xml_file_name)
    # Update model according to world view
    update_xml_file(wv, model)

    # Update queries files with the right path
    update_queries_write_path(str(VERIFYTA_QUERIES_PATH / queries_file_name))

    # Generate strategy command
    # verifyta_path --print-strategies outputdir xml_path queries_dir learning-method?
    command = "{0} {1} {2}".format(VERIFYTA_PATH, VERIFYTA_MODELS_PATH / xml_file_name
                                   , VERIFYTA_QUERIES_PATH / queries_file_name)

    # Run uppaal with the arguments given
    verifyta = subprocess.Popen(command, shell=True)

    # Wait for uppaal to finish generating and printing strategy
    while verifyta.poll() is None:
        time.sleep(0.001)
    # 3. Input strategy to coach
    # todo return strategy??
    return


def update_queries_write_path(query_path):
    with open(query_path, 'r') as f:
        for l in f:
            stripped_line = l.strip()
            if stripped_line.startswith("saveStrategy"):
                strat = re.search(',.*\)',stripped_line)
                strat_name = strat.group(0)[1:-1]
                new_strat_file_name = re.search('/[^/]*"', stripped_line)
                strat_file_name = new_strat_file_name.group(0)[1:-1]
                _replace(query_path, l, 'saveStrategy("' + str(VERIFYTA_OUTPUT_DIR_PATH / strat_file_name) + '",' + strat_name + ')')

    return


def _replace(file_path, pattern, subst):
    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    #Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)

def update_xml_file(wv, model: UPPAAL_MODEL):
    pass


# generate_strategy(WorldView(0), 'SimplePassingModel.xml', 'SimplePassingModel.q')
