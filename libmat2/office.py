import os
import re
import zipfile
from typing import Dict, Set, Pattern

import xml.etree.ElementTree as ET  # type: ignore

from .archive import ArchiveBasedAbstractParser

# Make pyflakes happy
assert Set
assert Pattern

def _parse_xml(full_path: str):
    """ This function parse XML, with namespace support. """

    namespace_map = dict()
    for _, (key, value) in ET.iterparse(full_path, ("start-ns", )):
        namespace_map[key] = value
        ET.register_namespace(key, value)

    return ET.parse(full_path), namespace_map


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

    @staticmethod
    def __remove_revisions(full_path: str) -> bool:
        """ In this function, we're changing the XML document in several
        different times, since we don't want to change the tree we're currently
        iterating on.
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError:
            return False

        # Revisions are either deletions (`w:del`) or
        # insertions (`w:ins`)
        del_presence = tree.find('.//w:del', namespace)
        ins_presence = tree.find('.//w:ins', namespace)
        if del_presence is None and ins_presence is None:
            return True  # No revisions are present

        parent_map = {c:p for p in tree.iter() for c in p}

        elements = list()
        for element in tree.iterfind('.//w:del', namespace):
            elements.append(element)
        for element in elements:
            parent_map[element].remove(element)

        elements = list()
        for element in tree.iterfind('.//w:ins', namespace):
            for position, item in enumerate(tree.iter()):  #pragma: no cover
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
            # this file contains the revisions
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
                try:
                    content = zipin.read(item).decode('utf-8')
                    results = re.findall(r"<(.+)>(.+)</\1>", content, re.I|re.M)
                    for (key, value) in results:
                        metadata[key] = value
                except (TypeError, UnicodeDecodeError):  # We didn't manage to parse the xml file
                    metadata[item.filename] = 'harmful content'
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


    @staticmethod
    def __remove_revisions(full_path: str) -> bool:
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError:
            return False

        if 'office' not in namespace.keys():  # no revisions in the current file
            return True

        for text in tree.getroot().iterfind('.//office:text', namespace):
            for changes in text.iterfind('.//text:tracked-changes', namespace):
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
                try:
                    content = zipin.read(item).decode('utf-8')
                    results = re.findall(r"<((?:meta|dc|cp).+?)>(.+)</\1>", content, re.I|re.M)
                    for (key, value) in results:
                        metadata[key] = value
                except (TypeError, UnicodeDecodeError):  # We didn't manage to parse the xml file
                    metadata[item.filename] = 'harmful content'
            for key, value in self._get_zipinfo_meta(item).items():
                metadata[key] = value
        zipin.close()
        return metadata
