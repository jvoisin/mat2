import logging
import re
import xml.etree.ElementTree as ET  # type: ignore

from . import archive, office

class EPUBParser(archive.ArchiveBasedAbstractParser):
    mimetypes = {'application/epub+zip', }

    def __init__(self, filename):
        super().__init__(filename)
        self.files_to_keep = set(map(re.compile, {  # type: ignore
            'META-INF/container.xml',
            'mimetype',
            'OEBPS/content.opf',
            }))

    def _specific_get_meta(self, full_path, file_path):
        if file_path != 'OEBPS/content.opf':
            return {}

        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<((?:meta|dc|cp).+?)[^>]*>(.+)</\1>",
                                     f.read(), re.I|re.M)
                return {k:v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):
                # We didn't manage to parse the xml file
                return {file_path: 'harmful content', }

    def _specific_cleanup(self, full_path: str):
        if not full_path.endswith('OEBPS/content.opf'):
            return True

        try:
            tree, namespace = office._parse_xml(full_path)
        except ET.ParseError:
            logging.error("Unable to parse %s in %s.", full_path, self.filename)
            return False
        parent_map = {c:p for p in tree.iter() for c in p}

        for item in tree.iterfind('.//', namespace):
            if item.tag.strip().lower().endswith('metadata'):
                parent_map[item].remove(item)
                break  # there is only a single <metadata> block
        tree.write(full_path, xml_declaration=True)
        return True
