import os
import time
import xml.etree.ElementTree as ET
import re
import subprocess
from os import fdopen, remove
from pathlib import Path

from shutil import copymode, move, copyfile
from tempfile import mkstemp

from constants import DISABLE_VERIFYTA_TERMINAL_OUTPUT
from uppaal import MODELS_PATH, OUTPUT_DIR_PATH, QUERIES_PATH, VERIFYTA_PATH


class UppaalStrategy:

    def __init__(self, strategy_name: str) -> None:
        super().__init__()
        self.path_to_strat_file = os.path.normpath(str(OUTPUT_DIR_PATH) + strategy_name)
        self.strategy_text = ""
        if not os.path.exists(self.path_to_strat_file):
            f = open(Path(self.path_to_strat_file), "x")
            f.close()
        with open(self.path_to_strat_file, 'r') as f:
            for line in f:
                self.strategy_text += line

        self.index_to_transition: {} = self._extract_transition_dict(self.strategy_text)
        self.statevar_to_index: {} = self._extract_statevars_to_index_dict(self.strategy_text)
        self.location_to_id: {} = self._extract_location_ids(self.strategy_text)
        self.regressors: [] = self._extract_regressors(self.strategy_text, self.statevar_to_index)

    def get_regressor_with_statevar_values(self, values: [int]):
        if len(values) != len(self.statevar_to_index.keys()):
            raise Exception("Cannot find regressor from statevar values since they have different lengths: "
                            "values_len={0}, state_var_len={1}".format(len(values), len(self.statevar_to_index)))

        for r in self.regressors:
            state_var_values = r.state_var_values
            correct = True
            for i in range(0, len(values)):
                if int(state_var_values[i]) != values[i]:
                    correct = False
            if correct:
                return r

    def _extract_location_ids(self, strategy: str):
        location_name_to_id = {}
        all_template_pattern = r'"locationnames":\{(.*)\},"r'
        all_templates = re.search(all_template_pattern, strategy, re.DOTALL).group(1)

        individual_template_pattern = r'"([^"]*)":\{([^\}]*)\}'
        template_and_mappings = re.findall(individual_template_pattern, all_templates)

        for (template_name, mappings) in template_and_mappings:
            self.add_location_mappings(location_name_to_id, template_name, mappings)

        return location_name_to_id

    @staticmethod
    def add_location_mappings(location_to_index, template_name, mappings):
        index_location_pattern = r'"([0-9]*)":"([^"]*)"'
        indices_and_locations = re.findall(index_location_pattern, mappings)

        for (index, location) in indices_and_locations:
            location_to_index[template_name + "." + location] = index

    @staticmethod
    def _extract_regressors(strat_string, state_vars_to_index_dict: {}):
        final_regressors = []
        # Get regressors part of strategy
        regre_text = re.search(r'"regressors":\{.*\}', strat_string, re.DOTALL)
        # Remove "regressors":{ and }
        regre_text = regre_text.group(0)[14:-1].strip()
        # Find each regressor
        regressors = regre_text.split('},')
        # Strip all elements from empty spaces
        regressors = [w.strip() for w in regressors]

        for reg in regressors:
            # Get statevars value like: "(2,0,1,0,1,0,-1,1,1,0,0,0,0,0)"
            statevars_vals = re.search(r'"\([-0-9,]*\)"', reg, re.DOTALL).group(0)
            statevars_vals = statevars_vals.replace("(", "").replace('"', "").replace(")", "")
            statevars_vals = statevars_vals.split(",")
            # Get pairs of transitions and values like ['2:89.09999999999999', '0:0']
            trans_val_text = re.search(r'"regressor":[\t\n]*\{[^}]*\}', reg, re.DOTALL)
            trans_val_text = trans_val_text.group(0)[13:-1].strip()
            trans_val_pairs = [w.strip().replace("\n", "").replace("\t", "").replace('"', '').replace('{', "") for w in
                               trans_val_text.split(',')]
            # The final list of pairs
            format_trans_val_pairs = []
            for pair in trans_val_pairs:
                cur_pair = pair.split(":")
                format_trans_val_pairs.append((int(cur_pair[0]), float(cur_pair[1])))

            new_regressor = Regressor(statevars_vals, format_trans_val_pairs, state_vars_to_index_dict)
            final_regressors.append(new_regressor)

        return final_regressors

    @staticmethod
    def _extract_transition_dict(strat_string):
        trans_dict = {}
        # Get actions part of strategy
        act_text = re.search(r'"actions":\{.*\},"s', strat_string, re.DOTALL)
        # Remove "actions":{ and },"s
        act_text = act_text.group(0)[11:-4].strip()
        # Create list by separating at commas
        act_lines = act_text.split('\n')
        # Strip all elements from empty spaces
        act_lines = [w.strip() for w in act_lines]

        for l in act_lines:
            matches = re.findall(r'"[^\"]*"', l, re.DOTALL)
            index = str(matches[0]).replace('"', "")
            value = str(matches[1]).replace('"', "")
            trans_dict[int(index)] = value

        return trans_dict

    @staticmethod
    def _extract_statevars_to_index_dict(strategy_string) -> {}:
        # Get statevars part of strategy
        statevars = re.search(r'"statevars":\[[^\]]*\]', strategy_string, re.DOTALL)
        # Remove "statevars":[ and ]
        statevars = statevars.group(0).split('[')[1].split(']')[0]
        # Create list by separating at commas
        statevars = statevars.split(',')
        # Strip all elements from empty spaces and quotes
        statevars = [w.strip()[1:-1] for w in statevars]

        statevar_name_to_index_dict = {}
        i = 0
        for statevar in statevars:
            statevar_name_to_index_dict[statevar] = i
            i += 1

        return statevar_name_to_index_dict


class Regressor:
    def __init__(self, state_var_values: [], trans_val_pairs: [], state_vars_to_index_dict: {}) -> None:
        self.state_var_values = state_var_values
        # Tuples of (transition, value)
        self.trans_val_pairs = trans_val_pairs
        self.state_vars_to_index_dict = state_vars_to_index_dict
        super().__init__()

    def get_lowest_val_trans(self):
        lowest = None
        for pair in self.trans_val_pairs:
            if lowest is None:
                lowest = pair
            elif lowest[1] > pair[1]:
                lowest = pair
        return lowest

    def get_highest_val_trans(self):
        highest = None
        for pair in self.trans_val_pairs:
            if highest is None:
                highest = pair
            elif highest[1] < pair[1]:
                highest = pair
        return highest

    def get_value(self, state_var_name):
        return self.state_var_values[self.state_vars_to_index_dict[state_var_name]]

    def __repr__(self) -> str:
        return "(State_var_values: {0}, trans_val_pairs {1})".format(self.state_var_values, self.trans_val_pairs)

    def __str__(self) -> str:
        return "(State_var_values: {0}, trans_val_pairs {1})".format(self.state_var_values, self.trans_val_pairs)



class GlobalDeclaration:
    # Must be called type and ident to avoid shadowing of python keywords type and id
    def __init__(self, typ, ident, val) -> None:
        super().__init__()
        self.typ = typ
        self.ident = ident
        self.val = val
        self.is_ident_only = False

    def get_uppaal_string(self) -> str:
        if self.is_ident_only:
            return self.ident  # See function_decl method
        if self.val is not None:
            if self.typ in ["clock", "double", "hybrid clock"]:
                return "{0} {1} = {2};".format(self.typ, self.ident, str("%.1f" % float(self.val)))
            return "{0} {1} = {2};".format(self.typ, self.ident, self.val)
        else:
            return "{0} {1};".format(self.typ, self.ident)

    @classmethod
    def function_decl(cls, function_string):
        instance = cls(None, function_string, None)  # Set ident to contain entire function
        instance.is_ident_only = True
        return instance

    @classmethod
    def single_string_decl(cls, string):
        instance = cls(None, string, None)  # Set ident to contain entire function
        instance.is_ident_only = True
        return instance


# Example: SeqGirl(const girl_id_t id) = Girl(id, true, false, false);
class SystemDeclaration(object):
    def __init__(self, ident, typ, arguments: []):
        self.ident = ident
        self.typ = typ
        self.arguments = arguments
        self.numb_of_args = len(arguments)

    def __str__(self) -> str:
        return "(Sys_decl: ident: {0}, type: {1}, arguments: {2})".format(self.ident, self.typ, self.arguments)

    def __repr__(self):
        return "(Sys_decl: ident: {0}, type: {1}, arguments: {2})".format(self.ident, self.typ, self.arguments)

    def get_uppaal_string(self):
        arg_com_sep = ','.join(map(str, self.arguments))
        return "{0} = {1}({2});".format(self.ident, self.typ, arg_com_sep)


class UppaalModel:
    def __init__(self, strategy_name) -> None:
        self.strategy_name = strategy_name
        self.xml_file_name = strategy_name + ".xml"
        self.queries_path = os.path.normpath(str(QUERIES_PATH) + strategy_name + ".q")
        self.path = os.path.normpath(str(MODELS_PATH) + self.xml_file_name)
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()

        self.system_decls: [SystemDeclaration]
        self.system_decls, self.system_line = self._extract_system_decl(self.root)

        self.global_decls: [GlobalDeclaration]
        self.global_decls = self._extract_global_decl(self.root)

        super().__init__()

    def save_xml_file(self):
        system_decl_zone = self.root.find("./system")

        # Create system declarations string and fill out
        sys_decl_string = ""
        for sd in self.system_decls:
            sys_decl_string = sys_decl_string + sd.get_uppaal_string() + "\n"
        sys_decl_string = sys_decl_string + self.system_line + ";"

        # Set text inside the xml file
        system_decl_zone.text = sys_decl_string

        global_decl_zone = self.root.find("./declaration")
        global_decl_string = ""
        for gd in self.global_decls:
            global_decl_string += gd.get_uppaal_string() + "\n"
        global_decl_zone.text = global_decl_string

        with open(self.path, 'wb') as f:
            # Include header to let UPPAAL know, the xml file is a UPPAAL file
            f.write(
                '<?xml version="1.0" encoding="utf-8"?><!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.1//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_2.dtd\'>'.encode(
                    'utf8'))
            ET.ElementTree(self.root).write(f, 'utf-8')

    def set_global_declaration_value(self, decl_name, new_value):
        for decl in self.global_decls:
            if decl.ident == decl_name:
                decl.val = new_value
                return
        raise NameError(decl_name)

    def set_system_decl_arguments(self, identity: str, arguments: [str]):
        for sys_decl in self.system_decls:
            if sys_decl.ident == identity:
                if sys_decl.numb_of_args != len(arguments):
                    raise Exception("Wrong number of arguments parsed for system declaration {0}. Expected {1}, got {2} ".format(identity, sys_decl.numb_of_args, len(arguments)))
                sys_decl.arguments = arguments
                return
        raise Exception("{0} not found in system declarations".format(identity))

    def _extract_template_string(self, xml_file_string):
        pass


    def _extract_global_decl(self, root: ET):
        global_decl_zone = root.find("./declaration")

        all_lines = str(self.remove_comments(global_decl_zone.text)).split("\n")
        code_lines = []
        for line in all_lines:
            # Filter out empty spaces and system main system declaration
            if not line.isspace() and line:
                code_lines.append(line)

        # Extract all declarations from the lines
        decls = []
        i = 0

        while i < len(code_lines):
            line = code_lines[i]
            if line.endswith("{"): # extract function string
                function_string = line
                opened_brackets = 0
                next_line = code_lines[i+1]
                while ("}" not in next_line) or opened_brackets > 0:
                    if "{" in next_line:
                        opened_brackets += 1
                    if "}" in next_line:
                        opened_brackets -= 1
                    i += 1
                    line = code_lines[i]
                    function_string += "\n" + line
                    next_line = code_lines[i + 1]
                function_string += "\n}"
                i += 1
                decls.append(GlobalDeclaration.single_string_decl(function_string))
            elif "typedef" in line:
                decls.append(GlobalDeclaration.single_string_decl(line))
            elif "=" in line:
                matches = re.match(r'\s*((?:(?:const|hybrid) )?[^ ]*) ([^ ]*(?:\[.*\])?) = (.*);', line)
                decls.append(GlobalDeclaration(matches.group(1), matches.group(2), matches.group(3)))
            else:
                matches = re.match(r'([^ ]*) ([^ ]*(?:\[.*\])?);', line)
                decls.append(GlobalDeclaration(matches.group(1), matches.group(2), None))

            i += 1
        return decls

    def remove_comments(self, text):
        comment_pat = re.compile('(?://[^\n]*|/\*(?:(?!\*/).)*\*/)', re.DOTALL)

        # Remove all comments
        if comment_pat.findall(text):
            comments = comment_pat.findall(text)
            for c in comments:
                text = text.replace(c, "")

        return text

    def _extract_system_decl(self, root):
        system_line = ""
        system_decls: [SystemDeclaration] = []
        global_decl_zone = root.find("./system")

        # Text from the system declarations part of the UPPAAL file
        global_decl_text = global_decl_zone.text
        global_decl_text = self.remove_comments(global_decl_text)

        # Strip trailing or preceding whitespaces and or tabs
        lines = str(global_decl_text).split("\n")
        lines = map(str.strip, lines)

        # Extract all declarations from the lines
        decls = []
        for l in lines:
            # Split into declarations
            ds = l.split(";")
            for d in ds:
                # Filter out empty spaces and system main system declaration
                if not d.isspace() and d and not d.startswith("system"):
                    decls.append(d)
                if d.startswith("system"):
                    system_line = d

        # parse declarations into SystemDeclarations objects
        for decl in decls:
            d = self._parse_system_decl(decl)
            system_decls.append(d)
        return system_decls, system_line

    def _parse_system_decl(self, decl: str) -> SystemDeclaration:
        # ident, type, arguments: []
        ident = decl.split("=")[0][0:-1]
        typ = decl.split("=")[1].replace(" ", "").split("(")[0]
        # Take last part after =, remove white spaces, split after firs (, remove )'s and split by ',' to get args.
        arguments = decl.split("=")[1].replace(" ", "").split("(")[1].replace(")", "").split(",")
        return SystemDeclaration(ident, typ, arguments)

    def _parse_decl(self, decl: str):

        pass

    def _print_tree(self, root):
        print(ET.tostring(root, encoding='utf8').decode('utf8'))


class Template:
    def __init__(self, ident) -> None:
        super().__init__()
        self.ident = ident
        self.declarations = []

    def get_decl(self, ident):
        for decl in self.declarations:
            if decl.ident == ident:
                return decl

    def __repr__(self) -> str:
        return "(Template: ident: {0}, declarations: {1})".format(self.ident, self.declarations)


def _update_queries_write_path(model: UppaalModel):
    query_path = model.queries_path
    query_dirs = Path(query_path).parent

    if not query_dirs.exists():
        os.makedirs(query_dirs)

    if "possession" in query_path:
        orig_query = Path(query_dirs).parent / "PassOrDribbleModel.q"
        if not Path(query_path).exists():
            f = open(Path(query_path), "x")
            copyfile(orig_query, query_path)
            f.close()
    with open(query_path, 'r', encoding='utf8') as f:
        for l in f:
            stripped_line = l.strip()
            if stripped_line.startswith("saveStrategy"):
                strat = re.search(',.*\)', stripped_line)
                strat_name = strat.group(0)[1:-1]
                strat_file_name = model.strategy_name
                newline = 'saveStrategy("' + os.path.normpath(str(OUTPUT_DIR_PATH) + strat_file_name) + '",' + strat_name + ')' + '\n'
                _replace_in_file(query_path, l, newline)
                # This does not work for more than one saveStrategy call
                break

    return str(OUTPUT_DIR_PATH / strat_file_name)


def _replace_in_file(file_path, pattern, subst):
    # Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w', encoding='utf8') as new_file:
        with open(file_path, encoding='utf8') as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    # Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    # Remove original file
    remove(file_path)
    # Move new file
    move(abs_path, file_path)


def execute_verifyta(model: UppaalModel):
    model.save_xml_file()
    _update_queries_write_path(model)
    # verifyta_path --print-strategies outputdir xml_path queries_dir learning-method?
    command = "{0} {1} {2}".format(VERIFYTA_PATH, model.path
                                   , model.queries_path)

    try:  # Get DEVNULL value to hide verifyta terminal output
        from subprocess import DEVNULL
    except ImportError:
        import os
        DEVNULL = open(os.devnull, 'wb')

    # Run uppaal verifyta command line tool
    if DISABLE_VERIFYTA_TERMINAL_OUTPUT:
        verifyta = subprocess.Popen(command, shell=True, stdout=DEVNULL)
    else:
        verifyta = subprocess.Popen(command, shell=True)
    # Wait for uppaal to finish generating and printing strategy
    while verifyta.poll() is None:
        time.sleep(0.001)


def execute_verifyta_and_poll(model: UppaalModel):
    model.save_xml_file()
    _update_queries_write_path(model)
    # verifyta_path --print-strategies outputdir xml_path queries_dir learning-method?
    command = "{0} {1} {2}".format(VERIFYTA_PATH, model.path
                                   , model.queries_path)

    # Run uppaal verifyta command line tool
    verifyta = subprocess.Popen(command, shell=True)

    # Wait for uppaal to finish generating and printing strategy
    while verifyta.poll() is None:
        time.sleep(0.001)