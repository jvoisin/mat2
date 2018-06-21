import os
import re
import shutil
import tempfile
import datetime
import zipfile
from typing import Dict, Set, Pattern

from . import abstract, parser_factory

# Make pyflakes happy
assert Set
assert Pattern

class ArchiveBasedAbstractParser(abstract.AbstractParser):
    files_to_keep = set()  # type: Set[str] 
    files_to_omit = set() # type: Set[Pattern] 

    def _clean_zipinfo(self, zipinfo: zipfile.ZipInfo) -> zipfile.ZipInfo:
        zipinfo.create_system = 3  # Linux
        zipinfo.comment = b''
        zipinfo.date_time = (1980, 1, 1, 0, 0, 0)
        return zipinfo

    def _get_zipinfo_meta(self, zipinfo: zipfile.ZipInfo) -> Dict[str, str]:
        metadata = {}
        if zipinfo.create_system == 3:
            #metadata['create_system'] = 'Linux'
            pass
        elif zipinfo.create_system == 2:
            metadata['create_system'] = 'Windows'
        else:
            metadata['create_system'] = 'Weird'

        if zipinfo.comment:
            metadata['comment'] = zipinfo.comment  # type: ignore

        if zipinfo.date_time != (1980, 1, 1, 0, 0, 0):
            metadata['date_time'] = str(datetime.datetime(*zipinfo.date_time))

        return metadata


    def _clean_internal_file(self, item: zipfile.ZipInfo, temp_folder: str,
                             zin: zipfile.ZipFile, zout: zipfile.ZipFile) -> bool:
        zin.extract(member=item, path=temp_folder)
        full_path = os.path.join(temp_folder, item.filename)
        tmp_parser, mtype = parser_factory.get_parser(full_path)  # type: ignore
        if not tmp_parser:
            zout.close()
            os.remove(self.output_filename)
            print("%s's format (%s) isn't supported" % (item.filename, mtype))
            return False
        tmp_parser.remove_all()

        zinfo = zipfile.ZipInfo(item.filename)  # type: ignore
        clean_zinfo = self._clean_zipinfo(zinfo)
        with open(tmp_parser.output_filename, 'rb') as f:
            zout.writestr(clean_zinfo, f.read())
        return True

    def remove_all(self) -> bool:
        zin = zipfile.ZipFile(self.filename, 'r')
        zout = zipfile.ZipFile(self.output_filename, 'w')
        temp_folder = tempfile.mkdtemp()

        for item in zin.infolist():
            if item.filename[-1] == '/':  # `is_dir` is added in Python3.6
                continue  # don't keep empty folders
            elif item.filename in self.files_to_keep:
                item = self._clean_zipinfo(item)
                zout.writestr(item, zin.read(item))
                continue
            elif any(map(lambda r: r.search(item.filename), self.files_to_omit)):
                continue
            elif not self._clean_internal_file(item, temp_folder, zin, zout):
                return False

        shutil.rmtree(temp_folder)
        zout.close()
        zin.close()
        return True


class MSOfficeParser(ArchiveBasedAbstractParser):
    mimetypes = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    files_to_keep = {
            '[Content_Types].xml',
            '_rels/.rels',
            'word/_rels/document.xml.rels',
            'word/document.xml',
            'word/fontTable.xml',
            'word/settings.xml',
            'word/styles.xml',
    }
    files_to_omit = set(map(re.compile, {  # type: ignore
            '^docProps/',
    }))

    def get_meta(self) -> Dict[str, str]:
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        metadata = {}
        zipin = zipfile.ZipFile(self.filename)
        for item in zipin.infolist():
            if item.filename.startswith('docProps/') and item.filename.endswith('.xml'):
                content = zipin.read(item).decode('utf-8')
                try:
                    results = re.findall(r"<(.+)>(.+)</\1>", content, re.I|re.M)
                    for (key, value) in results:
                        metadata[key] = value
                except TypeError:  # We didn't manage to parse the xml file
                    pass
                if not metadata:  # better safe than sorry
                    metadata[item] = 'harmful content'
            for key, value in self._get_zipinfo_meta(item).items():
                metadata[key] = value
        zipin.close()
        return metadata


class LibreOfficeParser(ArchiveBasedAbstractParser):
    mimetypes = {
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet',
        'application/vnd.oasis.opendocument.presentation',
        'application/vnd.oasis.opendocument.graphics',
        'application/vnd.oasis.opendocument.chart',
        'application/vnd.oasis.opendocument.formula',
        'application/vnd.oasis.opendocument.image',
    }
    files_to_keep = {
            'META-INF/manifest.xml',
            'content.xml',
            'manifest.rdf',
            'mimetype',
            'settings.xml',
            'styles.xml',
    }
    files_to_omit = set(map(re.compile, {  # type: ignore
            '^meta\.xml$',
            '^Configurations2/',
    }))

    def get_meta(self) -> Dict[str, str]:
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        metadata = {}
        zipin = zipfile.ZipFile(self.filename)
        for item in zipin.infolist():
            if item.filename == 'meta.xml':
                content = zipin.read(item).decode('utf-8')
                try:
                    results = re.findall(r"<((?:meta|dc|cp).+?)>(.+)</\1>", content, re.I|re.M)
                    for (key, value) in results:
                        metadata[key] = value
                except TypeError:  # We didn't manage to parse the xml file
                    pass
                if not metadata:  # better safe than sorry
                    metadata[item] = 'harmful content'
            for key, value in self._get_zipinfo_meta(item).items():
                metadata[key] = value
        zipin.close()
        return metadata

