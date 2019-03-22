import mimetypes
import os
import shutil
import tempfile
from typing import Dict, Union

import mutagen

from . import abstract, parser_factory


class MutagenParser(abstract.AbstractParser):
    def __init__(self, filename):
        super().__init__(filename)
        try:
            mutagen.File(self.filename)
        except mutagen.MutagenError:
            raise ValueError

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        f = mutagen.File(self.filename)
        if f.tags:
            return {k:', '.join(v) for k, v in f.tags.items()}
        return {}

    def remove_all(self) -> bool:
        shutil.copy(self.filename, self.output_filename)
        f = mutagen.File(self.output_filename)
        f.delete()
        f.save()
        return True


class MP3Parser(MutagenParser):
    mimetypes = {'audio/mpeg', }

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        metadata = {}  # type: Dict[str, Union[str, dict]]
        meta = mutagen.File(self.filename).tags
        for key in meta:
            if not hasattr(meta[key], 'text'):  # pragma: no cover
                continue
            metadata[key.rstrip(' \t\r\n\0')] = ', '.join(map(str, meta[key].text))
        return metadata


class OGGParser(MutagenParser):
    mimetypes = {'audio/ogg', }


class FLACParser(MutagenParser):
    mimetypes = {'audio/flac', 'audio/x-flac'}

    def remove_all(self) -> bool:
        shutil.copy(self.filename, self.output_filename)
        f = mutagen.File(self.output_filename)
        f.clear_pictures()
        f.delete()
        f.save(deleteid3=True)
        return True

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        meta = super().get_meta()
        for num, picture in enumerate(mutagen.File(self.filename).pictures):
            name = picture.desc if picture.desc else 'Cover %d' % num
            extension = mimetypes.guess_extension(picture.mime)
            if extension is None:  #  pragma: no cover
                meta[name] = 'harmful data'
                continue

            _, fname = tempfile.mkstemp()
            fname = fname + extension
            with open(fname, 'wb') as f:
                f.write(picture.data)
            p, _ = parser_factory.get_parser(fname)  # type: ignore
            # Mypy chokes on ternaries :/
            meta[name] = p.get_meta() if p else 'harmful data'  # type: ignore
            os.remove(fname)
        return meta
