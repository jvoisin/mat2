import shutil
from typing import Dict
from . import abstract


class HarmlessParser(abstract.AbstractParser):
    """ This is the parser for filetypes that do not contain metadata. """
    mimetypes = {'text/plain', }

    def get_meta(self) -> Dict[str, str]:
        return dict()

    def remove_all(self) -> bool:
        shutil.copy(self.filename, self.output_filename)
        return True
