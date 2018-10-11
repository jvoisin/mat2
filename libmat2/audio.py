import mimetypes
import os
import shutil
import tempfile

import mutagen

from . import abstract, parser_factory


class MutagenParser(abstract.AbstractParser):
    def __init__(self, filename):
        super().__init__(filename)
        try:
            mutagen.File(self.filename)
        except mutagen.MutagenError:
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
    mimetypes = {'audio/flac', 'audio/x-flac'}

    def remove_all(self):
        shutil.copy(self.filename, self.output_filename)
        f = mutagen.File(self.output_filename)
        f.clear_pictures()
        f.delete()
        f.save(deleteid3=True)
        return True

    def get_meta(self):
        meta = super().get_meta()
        for num, picture in enumerate(mutagen.File(self.filename).pictures):
            name = picture.desc if picture.desc else 'Cover %d' % num
            _, fname = tempfile.mkstemp()
            with open(fname, 'wb') as f:
                f.write(picture.data)
            extension = mimetypes.guess_extension(picture.mime)
            shutil.move(fname, fname + extension)
            p, _ = parser_factory.get_parser(fname+extension)
            meta[name] = p.get_meta() if p else 'harmful data'
            os.remove(fname + extension)
        return meta
