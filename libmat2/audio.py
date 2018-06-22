import shutil

import mutagen

from . import abstract


class MutagenParser(abstract.AbstractParser):
    def __init__(self, filename):
        super().__init__(filename)
        try:
            mutagen.File(self.filename)
        except mutagen.flac.MutagenError:
            raise ValueError
        except mutagen.mp3.MutagenError:
            raise ValueError
        except mutagen.ogg.MutagenError:
            raise ValueError

    def get_meta(self):
        f = mutagen.File(self.filename)
        if f.tags:
            return {k:', '.join(v) for k, v in f.tags.items()}
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
        metadata = {}
        meta = mutagen.File(self.filename).tags
        for key in meta:
            metadata[key.rstrip(' \t\r\n\0')] = ', '.join(map(str, meta[key].text))
        return metadata


class OGGParser(MutagenParser):
    mimetypes = {'audio/ogg', }


class FLACParser(MutagenParser):
    mimetypes = {'audio/flac', 'audio/x-flac' }
