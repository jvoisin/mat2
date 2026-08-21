from __future__ import annotations

__lazy_modules__ = ['mutagen']

import mimetypes
import os
import shutil
import tempfile

import mutagen
import mutagen.apev2
import mutagen.id3

from . import abstract, parser_factory, video


class MutagenParser(abstract.AbstractParser):
    def __init__(self, filename):
        super().__init__(filename)
        try:
            if mutagen.File(self.filename) is None:
                raise ValueError
        except mutagen.MutagenError as e:
            raise ValueError(e)

    def get_meta(self) -> dict[str, str | dict]:
        f = mutagen.File(self.filename)
        if f.tags:
            return {k: ', '.join(map(str, v)) for k, v in f.tags.items()}
        return {}

    def _remove_appended_tags(self) -> None:
        """ mutagen.File() only binds the container's primary tag, so an APEv2
        or ID3 block glued to the file is left untouched by delete(). """
        for module in (mutagen.apev2, mutagen.id3):
            try:
                module.delete(self.output_filename)
            except mutagen.MutagenError as e:
                raise ValueError(e)

    def remove_all(self) -> bool:
        shutil.copy(self.filename, self.output_filename)
        try:
            f = mutagen.File(self.output_filename)
            f.delete()
            f.save()
            self._remove_appended_tags()
        except (mutagen.MutagenError, ValueError) as e:
            os.remove(self.output_filename)
            raise ValueError(e)
        return True


class MP3Parser(MutagenParser):
    mimetypes = {'audio/mpeg', }

    def get_meta(self) -> dict[str, str | dict]:
        metadata: dict[str, str | dict] = dict()
        meta = mutagen.File(self.filename).tags
        if not meta:
            return metadata
        for key in meta:
            if isinstance(key, tuple):
                metadata[key[0]] = key[1]
                continue
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
        try:
            f = mutagen.File(self.output_filename)
            f.clear_pictures()
            f.delete()
            f.save(deleteid3=True)
            self._remove_appended_tags()
        except (mutagen.MutagenError, ValueError) as e:
            os.remove(self.output_filename)
            raise ValueError(e)
        return True

    def get_meta(self) -> dict[str, str | dict]:
        meta = super().get_meta()
        for num, picture in enumerate(mutagen.File(self.filename).pictures):
            name = picture.desc if picture.desc else 'Cover %d' % num
            extension = mimetypes.guess_extension(picture.mime)
            if extension is None: #  pragma: no cover
                meta[name] = 'harmful data'
                continue

            _, fname = tempfile.mkstemp()
            fname = fname + extension
            with open(fname, 'wb') as f:
                f.write(picture.data)
            p, _ = parser_factory.get_parser(fname)  # type: ignore
            if p is None:
                raise ValueError
            # Mypy chokes on ternaries :/
            meta[name] = p.get_meta() if p else 'harmful data'  # type: ignore
            os.remove(fname)
        return meta


class WAVParser(video.AbstractFFmpegParser):
    mimetypes = {'audio/x-wav', }
    meta_allowlist = {'AvgBytesPerSec', 'BitsPerSample', 'Directory',
                      'Duration', 'Encoding', 'ExifToolVersion',
                      'FileAccessDate', 'FileInodeChangeDate',
                      'FileModifyDate', 'FileName', 'FilePermissions',
                      'FileSize', 'FileType', 'FileTypeExtension',
                      'MIMEType', 'NumChannels', 'SampleRate', 'SourceFile',
                     }


class AIFFParser(video.AbstractFFmpegParser):
    mimetypes = {'audio/aiff', 'audio/x-aiff'}
    meta_allowlist = {'AvgBytesPerSec', 'BitsPerSample', 'Directory',
                      'Duration', 'Encoding', 'ExifToolVersion',
                      'FileAccessDate', 'FileInodeChangeDate',
                      'FileModifyDate', 'FileName', 'FilePermissions',
                      'FileSize', 'FileType', 'FileTypeExtension',
                      'MIMEType', 'NumChannels', 'SampleRate', 'SourceFile',
                      'NumSampleFrames', 'SampleSize',
                     }
