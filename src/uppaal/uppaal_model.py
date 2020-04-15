import xml.etree.ElementTree as ET
import re

from pathlib import Path

from uppaal import VERIFYTA_MODELS_PATH


class UppaalStrategy:

    def __init__(self) -> None:
        super().__init__()



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
    def __init__(self, xml_model_file) -> None:
        self.tree = ET.parse(VERIFYTA_MODELS_PATH / xml_model_file)
        self.root = self.tree.getroot()

        self.system_decls: [SystemDeclaration]
        self.system_decls, self.system_line = self._extract_system_decl(self.root)

        super().__init__()

    def save_xml_file(self, file_name_xml):
        global_decl_zone = self.root.find("./system")

        # Create system declarations string and fill out
        sys_decl_string = ""
        for sd in self.system_decls:
            sys_decl_string = sys_decl_string + sd.get_uppaal_string() + "\n"
        sys_decl_string = sys_decl_string + self.system_line + ";"

        # Set text inside the xml file
        global_decl_zone.text = sys_decl_string

        with open(VERIFYTA_MODELS_PATH / file_name_xml, 'wb') as f:
            # Include header to let UPPAAL know, the xml file is a UPPAAL file
            f.write(
                '<?xml version="1.0" encoding="utf-8"?><!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.1//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_2.dtd\'>'.encode(
                    'utf8'))
            ET.ElementTree(self.root).write(f, 'utf-8')

    def set_arguments(self, ident: str, arguments: [str]):
        for sys_decl in self.system_decls:
            if sys_decl.ident == ident:
                if sys_decl.numb_of_args != len(arguments):
                    raise Exception("Wrong number of arguments parsed for system declaration {0}. Expected {1}, got {2} ".format(ident, sys_decl.numb_of_args, len(arguments)))
                sys_decl.arguments = arguments
                return
        raise Exception("{0} not found in system declarations".format(ident))

    def _extract_template_string(self, xml_file_string):
        pass

    def _extract_global_decl(self, root: ET):
        global_decl_zone = root.find("./declaration")

        lines = str(global_decl_zone.text).split("\n")
        for s in lines:
            s = s.strip()

        # Extract all declarations from the lines
        decls = []
        for l in lines:
            if not l.startswith("//"):
                ds = l.split(";")
                for d in ds:
                    d.replace(' ', "")
                    if not d == "":
                        decls.append(d)

        for decl in decls:
            self._parse_decl(decl)

        return []

    def _extract_system_decl(self, root):
        system_line = ""
        system_decls: [SystemDeclaration] = []
        global_decl_zone = root.find("./system")

        # Text from the system declarations part of the UPPAAL file
        global_decl_text = global_decl_zone.text
        comment_pat = re.compile('(?://[^\n]*|/\*(?:(?!\*/).)*\*/)', re.DOTALL)

        # Remove all comments
        if comment_pat.findall(global_decl_text):
            comments = comment_pat.findall(global_decl_text)
            for c in comments:
                global_decl_text = global_decl_text.replace(c, "")

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


class Declaration:
    # Must be called typ and ident to avoid shadowing of python keywords type and id
    def __init__(self, typ, ident, val) -> None:
        super().__init__()
        self.type = typ
        self.ident = ident
        self.val = val

    def __repr__(self) -> str:
        return "(Declaration: type: {0}, ident: {1}, val: {2})".format(self.type, self.ident, self.val)

# model = UPPAAL_MODEL(xml_model_file="MV_mini_projekt_2.xml")
# model.set_arguments("SeqGirl(const girl_id_t id)", ["id", "true", "true", "true"])
# model.save_xml_file("newFile.xml")
