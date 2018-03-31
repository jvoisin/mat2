import re
import subprocess
import json
import zipfile
import tempfile
import shutil
import os

from . import abstract, parser_factory

class LibreOfficeParser(abstract.AbstractParser):
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
                for (key, value) in re.findall(r"<((?:meta|dc).+?)>(.+)</\1>", content, re.I):
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

            zin.extract(member=item, path=temp_folder)
            tmp_parser = parser_factory.get_parser(os.path.join(temp_folder, item.filename))
            if tmp_parser is None:
                print("%s isn't supported" % item.filename)
                continue
            tmp_parser.remove_all()
            zout.write(tmp_parser.output_filename, item.filename)
        shutil.rmtree(temp_folder)
        zout.close()
        zin.close()
        return True
