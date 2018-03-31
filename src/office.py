import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

from . import abstract, parser_factory

class ArchiveBasedAbstractParser(abstract.AbstractParser):
    def _clean_zipinfo(self, zipinfo:zipfile.ZipInfo) -> zipfile.ZipInfo:
        zipinfo.compress_type = zipfile.ZIP_DEFLATED
        zipinfo.create_system = 3  # Linux
        zipinfo.comment = b''
        zipinfo.date_time = (1980, 1, 1, 0, 0, 0)
        return zipinfo

    def _clean_internal_file(self, item:zipfile.ZipInfo, temp_folder:str, zin:zipfile.ZipFile, zout:zipfile.ZipFile):
        zin.extract(member=item, path=temp_folder)
        tmp_parser = parser_factory.get_parser(os.path.join(temp_folder, item.filename))
        if tmp_parser is None:
            print("%s isn't supported" % item.filename)
            return
        tmp_parser.remove_all()
        zinfo = zipfile.ZipInfo(item.filename)
        item = self._clean_zipinfo(item)
        with open(tmp_parser.output_filename, 'rb') as f:
            zout.writestr(zinfo, f.read())

class MSOfficeParser(ArchiveBasedAbstractParser):
    mimetypes = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    files_to_keep = {'_rels/.rels', 'word/_rels/document.xml.rels'}

    def get_meta(self):
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        metadata = {}
        zipin = zipfile.ZipFile(self.filename)
        for item in zipin.namelist():
            if item.startswith('docProps/') and item.endswith('.xml'):
                content = zipin.read(item).decode('utf-8')
                for (key, value) in re.findall(r"<(.+)>(.+)</\1>", content, re.I):
                    metadata[key] = value
                if not metadata:  # better safe than sorry
                    metadata[item] = 'harmful content'
        zipin.close()
        return metadata


    def remove_all(self):
        zin = zipfile.ZipFile(self.filename, 'r')
        zout = zipfile.ZipFile(self.output_filename, 'w')
        temp_folder = tempfile.mkdtemp()

        for item in zin.infolist():
            if item.filename[-1] == '/':
                continue  # `is_dir` is added in Python3.6
            elif item.filename.startswith('docProps/'):
                if not item.filename.endswith('.rels'):
                    continue  # don't keep metadata files
            if item.filename in self.files_to_keep:
                item = self._clean_zipinfo(item)
                zout.writestr(item, zin.read(item))
                continue

            self._clean_internal_file(item, temp_folder, zin, zout)

        shutil.rmtree(temp_folder)
        zout.close()
        zin.close()
        return True



class LibreOfficeParser(ArchiveBasedAbstractParser):
    mimetypes = {
            'application/vnd.oasis.opendocument.text',
            'application/vnd.oasis.opendocument.spreadsheet',
            'application/vnd.oasis.opendocument.presentation',
            'application/vnd.oasis.opendocument.graphics',
            'application/vnd.oasis.opendocument.chart'
    }

    def get_meta(self):
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        metadata = {}
        zipin = zipfile.ZipFile(self.filename)
        for item in zipin.namelist():
            if item == 'meta.xml':
                content = zipin.read(item).decode('utf-8')
                for (key, value) in re.findall(r"<((?:meta|dc|cp).+?)>(.+)</\1>", content, re.I):
                    metadata[key] = value
                if not metadata:  # better safe than sorry
                    metadata[item] = 'harmful content'
        zipin.close()
        return metadata

    def remove_all(self):
        zin = zipfile.ZipFile(self.filename, 'r')
        zout = zipfile.ZipFile(self.output_filename, 'w')
        temp_folder = tempfile.mkdtemp()

        for item in zin.infolist():
            if item.filename[-1] == '/':
                continue  # `is_dir` is added in Python3.6
            elif item.filename == 'meta.xml':
                continue  # don't keep metadata files

            self._clean_internal_file(item, temp_folder, zin, zout)

        shutil.rmtree(temp_folder)
        zout.close()
        zin.close()
        return True
