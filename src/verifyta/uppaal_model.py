from verifyta.verifyta import VERIFYTA_MODELS_PATH


class UPPAAL_MODEL:
    def __init__(self, xml_model_file) -> None:
        s = VERIFYTA_MODELS_PATH / xml_model_file
        print(s)
        with open(VERIFYTA_MODELS_PATH / xml_model_file, 'r') as file:
            data = file.read()
            print(data)

        global_decls: [] = extract_global_decl(xml_model_file)

        # Get each template as string
        templates: [Template] = extract_template_string(xml_model_file)


        super().__init__()



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

def extract_template_string(xml_model_file):
    pass

def extract_global_decl(xml_model_file):
    return []


template = Template("myTemp")
template.declarations.append(Declaration('int', 'i', 0))
template.declarations.append(Declaration('int', 'f', 0))
print(template)
print(template.get_decl('i'))