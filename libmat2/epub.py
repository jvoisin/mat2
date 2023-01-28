import logging
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET  # type: ignore
from typing import Any, Dict

from . import archive, office


class EPUBParser(archive.ZipParser):
    mimetypes = {'application/epub+zip', }
    metadata_namespace = '{http://purl.org/dc/elements/1.1/}'

    def __init__(self, filename):
        super().__init__(filename)
        self.files_to_keep = set(map(re.compile, {  # type: ignore
            'META-INF/container.xml',
            'mimetype',
            'OEBPS/content.opf',
            'content.opf',
            'hmh.opf',
            'OPS/.+.xml'
            }))
        self.files_to_omit = set(map(re.compile, {  # type: ignore
            'iTunesMetadata.plist',
            'META-INF/calibre_bookmarks.txt',
            'OEBPS/package.opf',
             }))
        self.uniqid = uuid.uuid4()

    def is_archive_valid(self):
        super().is_archive_valid()
        with zipfile.ZipFile(self.filename) as zin:
            for item in self._get_all_members(zin):
                member_name = self._get_member_name(item)
                if member_name.endswith('META-INF/encryption.xml'):
                    raise ValueError('the file contains encrypted fonts')

    def _specific_get_meta(self, full_path, file_path) -> Dict[str, Any]:
        if not file_path.endswith('.opf'):
            return {}

        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<((?:meta|dc|cp).+?)[^>]*>(.+)</\1>",
                                     f.read(), re.I|re.M)
                return {k:v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):
                return {file_path: 'harmful content', }

    def _specific_cleanup(self, full_path: str) -> bool:
        if full_path.endswith('hmh.opf') or full_path.endswith('content.opf'):
            return self.__handle_contentopf(full_path)
        elif full_path.endswith('OEBPS/toc.ncx'):
            return self.__handle_tocncx(full_path)
        elif re.search('/OPS/[^/]+.xml$', full_path):
            return self.__handle_ops_xml(full_path)
        return True

    def __handle_ops_xml(self, full_path: str) -> bool:
        try:
            tree, namespace = office._parse_xml(full_path)
        except ET.ParseError:  # pragma: nocover
            logging.error("Unable to parse %s in %s.", full_path, self.filename)
            return False

        for item in tree.iterfind('.//', namespace):  # pragma: nocover
            if item.tag.strip().lower().endswith('head'):
                item.clear()
                break
        tree.write(full_path, xml_declaration=True, encoding='utf-8',
                   short_empty_elements=False)
        return True

    def __handle_tocncx(self, full_path: str) -> bool:
        try:
            tree, namespace = office._parse_xml(full_path)
        except ET.ParseError:  # pragma: nocover
            logging.error("Unable to parse %s in %s.", full_path, self.filename)
            return False

        for item in tree.iterfind('.//', namespace):  # pragma: nocover
            if item.tag.strip().lower().endswith('head'):
                item.clear()
                ET.SubElement(item, 'meta', attrib={'name': '', 'content': ''})
                break
        tree.write(full_path, xml_declaration=True, encoding='utf-8',
                   short_empty_elements=False)
        return True

    def __handle_contentopf(self, full_path: str) -> bool:
        try:
            tree, namespace = office._parse_xml(full_path)
        except ET.ParseError:
            logging.error("Unable to parse %s in %s.", full_path, self.filename)
            return False

        for item in tree.iterfind('.//', namespace):  # pragma: nocover
            if item.tag.strip().lower().endswith('metadata'):
                item.clear()

                # item with mandatory content
                uniqid = ET.Element(self.metadata_namespace + 'identifier')
                uniqid.text = str(self.uniqid)
                uniqid.set('id', 'id')
                item.append(uniqid)

                # items without mandatory content
                for name in ['language', 'title']:
                    uniqid = ET.Element(self.metadata_namespace + name)
                    item.append(uniqid)
                break  # there is only a single <metadata> block
        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True
