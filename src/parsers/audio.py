import subprocess
import shutil
import json

import mutagen

from . import abstract

class MutagenParser(abstract.AbstractParser):
    def get_meta(self):
        f = mutagen.File(self.filename)
        if f.tags:
            return f.tags
        return {}

    def remove_all(self):
        shutil.copy(self.filename, self.output_filename)
        f = mutagen.File(self.output_filename)
        f.delete()
        f.save()
        return True

class MP3Parser(MutagenParser):
    mimetypes = {'audio/mpeg', }

    def get_meta(self):
        meta = super().get_meta()
        metadata = {}
        for key in meta:
            metadata[key] = meta[key].text
        return metadata

class OGGParser(MutagenParser):
    mimetypes = {'audio/ogg', }

class FLACParser(MutagenParser):
    mimetypes = {'audio/flac', }
