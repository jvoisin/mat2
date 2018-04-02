from . import abstract

class HarmlessParser(abstract.AbstractParser):
    """ This is the parser for filetypes that do not contain metadata. """
    mimetypes = {'application/xml', 'text/plain', 'application/rdf+xml'}

    def __init__(self, filename: str):
        self.filename = filename
        self.output_filename = filename

    def get_meta(self):
        return dict()

    def remove_all(self):
        return True
