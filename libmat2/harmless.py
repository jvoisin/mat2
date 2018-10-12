import shutil
from typing import Dict, Union
from . import abstract


class HarmlessParser(abstract.AbstractParser):
    """ This is the parser for filetypes that can not contain metadata. """
    mimetypes = {'text/plain', 'image/x-ms-bmp'}

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        return dict()

    def remove_all(self) -> bool:
        shutil.copy(self.filename, self.output_filename)
        return True
