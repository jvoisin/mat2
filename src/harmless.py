from . import abstract

class HarmlessParser(abstract.AbstractParser):
    mimetypes = {'application/xml', 'text/plain'}

    def __init__(self, filename: str):
        self.filename = filename
        self.output_filename = filename

    def get_meta(self):
        return dict()

    def remove_all(self):
        return True
