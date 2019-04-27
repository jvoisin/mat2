import logging
import re
import uuid
import xml.etree.ElementTree as ET  # type: ignore

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
            }))
        self.uniqid = uuid.uuid4()

    def _specific_get_meta(self, full_path, file_path):
        if file_path != 'OEBPS/content.opf':
            return {}

        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<((?:meta|dc|cp).+?)[^>]*>(.+)</\1>",
                                     f.read(), re.I|re.M)
                return {k:v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):
                return {file_path: 'harmful content', }

    def _specific_cleanup(self, full_path: str):
        if full_path.endswith('OEBPS/content.opf'):
            return self.__handle_contentopf(full_path)
        elif full_path.endswith('OEBPS/toc.ncx'):
            return self.__handle_tocncx(full_path)
        return True

    def __handle_tocncx(self, full_path: str):
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

    def __handle_contentopf(self, full_path: str):
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
                for name in {'language', 'title'}:
                    uniqid = ET.Element(self.metadata_namespace + name)
                    item.append(uniqid)
                break  # there is only a single <metadata> block
        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True
