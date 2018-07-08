import os
import re
import shutil
import tempfile
import datetime
import zipfile
from typing import Dict, Set, Pattern
try:  # protect against DoS
    from defusedxml import ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


from . import abstract, parser_factory

# Make pyflakes happy
assert Set
assert Pattern

def _parse_xml(full_path: str):
    """ This function parse XML with namespace support. """
    def parse_map(f):  # etree support for ns is a bit rough
        ns_map = dict()
        for event, (k, v) in ET.iterparse(f, ("start-ns", )):
            if event == "start-ns":
                ns_map[k] = v
        return ns_map

    ns = parse_map(full_path)

    # Register the namespaces
    for k, v in ns.items():
        ET.register_namespace(k, v)

    return ET.parse(full_path), ns


class ArchiveBasedAbstractParser(abstract.AbstractParser):
    # Those are the files that have a format that _isn't_
    # supported by MAT2, but that we want to keep anyway.
    files_to_keep = set()  # type: Set[str]

    # Those are the files that we _do not_ want to keep,
    # no matter if they are supported or not.
    files_to_omit = set() # type: Set[Pattern]

    def __init__(self, filename):
        super().__init__(filename)
        try:  # better fail here than later
            zipfile.ZipFile(self.filename)
        except zipfile.BadZipFile:
            raise ValueError

    def _specific_cleanup(self, full_path: str) -> bool:
        """ This method can be used to apply specific treatment
        to files present in the archive."""
        return True  # pragma: no cover

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

    def remove_all(self) -> bool:
        with zipfile.ZipFile(self.filename) as zin,\
             zipfile.ZipFile(self.output_filename, 'w') as zout:

            temp_folder = tempfile.mkdtemp()

            for item in zin.infolist():
                if item.filename[-1] == '/':  # `is_dir` is added in Python3.6
                    continue  # don't keep empty folders

                zin.extract(member=item, path=temp_folder)
                full_path = os.path.join(temp_folder, item.filename)

                if self._specific_cleanup(full_path) is False:
                    shutil.rmtree(temp_folder)
                    os.remove(self.output_filename)
                    print("Something went wrong during deep cleaning of %s" % item.filename)
                    return False

                if item.filename in self.files_to_keep:
                    # those files aren't supported, but we want to add them anyway
                    pass
                elif any(map(lambda r: r.search(item.filename), self.files_to_omit)):
                    continue
                else:
                    # supported files that we want to clean then add
                    tmp_parser, mtype = parser_factory.get_parser(full_path)  # type: ignore
                    if not tmp_parser:
                        shutil.rmtree(temp_folder)
                        os.remove(self.output_filename)
                        print("%s's format (%s) isn't supported" % (item.filename, mtype))
                        return False
                    tmp_parser.remove_all()
                    os.rename(tmp_parser.output_filename, full_path)

                zinfo = zipfile.ZipInfo(item.filename)  # type: ignore
                clean_zinfo = self._clean_zipinfo(zinfo)
                with open(full_path, 'rb') as f:
                    zout.writestr(clean_zinfo, f.read())

        shutil.rmtree(temp_folder)
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

    def __remove_revisions(self, full_path: str) -> bool:
        """ In this function, we're changing the XML
        document in two times, since we don't want
        to change the tree we're iterating on."""
        tree, ns = _parse_xml(full_path)

        # No revisions are present
        del_presence = tree.find('.//w:del', ns)
        ins_presence = tree.find('.//w:ins', ns)
        if del_presence is None and ins_presence is None:
            return True

        parent_map = {c:p for p in tree.iter() for c in p}

        elements = list([element for element in tree.iterfind('.//w:del', ns)])
        for element in elements:
            parent_map[element].remove(element)

        elements = list()
        for element in tree.iterfind('.//w:ins', ns):
            for position, item in enumerate(tree.iter()):
                if item == element:
                    for children in element.iterfind('./*'):
                        elements.append((element, position, children))
                    break

        for (element, position, children) in elements:
            parent_map[element].insert(position, children)
            parent_map[element].remove(element)

        tree.write(full_path, xml_declaration=True)

        return True

    def _specific_cleanup(self, full_path: str) -> bool:
        if full_path.endswith('/word/document.xml'):
            return self.__remove_revisions(full_path)
        return True

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
        r'^meta\.xml$',
        '^Configurations2/',
        '^Thumbnails/',
    }))


    def __remove_revisions(self, full_path: str) -> bool:
        tree, ns = _parse_xml(full_path)

        if 'office' not in ns.keys():  # no revisions in the current file
            return True

        for text in tree.getroot().iterfind('.//office:text', ns):
            for changes in text.iterfind('.//text:tracked-changes', ns):
                text.remove(changes)

        tree.write(full_path, xml_declaration=True)

        return True

    def _specific_cleanup(self, full_path: str) -> bool:
        if os.path.basename(full_path) == 'content.xml':
            return self.__remove_revisions(full_path)
        return True

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
