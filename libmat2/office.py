import logging
import os
import re
import zipfile
from typing import Dict, Set, Pattern, Tuple, Any

import xml.etree.ElementTree as ET  # type: ignore

from .archive import ZipParser

# pylint: disable=line-too-long

# Make pyflakes happy
assert Set
assert Pattern

def _parse_xml(full_path: str) -> Tuple[ET.ElementTree, Dict[str, str]]:
    """ This function parses XML, with namespace support. """
    namespace_map = dict()
    for _, (key, value) in ET.iterparse(full_path, ("start-ns", )):
        # The ns[0-9]+ namespaces are reserved for internal usage, so
        # we have to use an other nomenclature.
        if re.match('^ns[0-9]+$', key, re.I):  # pragma: no cover
            key = 'mat' + key[2:]

        namespace_map[key] = value
        ET.register_namespace(key, value)

    return ET.parse(full_path), namespace_map


def _sort_xml_attributes(full_path: str) -> bool:
    """ Sort xml attributes lexicographically,
    because it's possible to fingerprint producers (MS Office, Libreoffice, …)
    since they are all using different orders.
    """
    tree = ET.parse(full_path)

    for c in tree.getroot():
        c[:] = sorted(c, key=lambda child: (child.tag, child.get('desc')))

    tree.write(full_path, xml_declaration=True)
    return True


class MSOfficeParser(ZipParser):
    mimetypes = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    content_types_to_keep = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml',  # /word/endnotes.xml
        'application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml',  # /word/footnotes.xml
        'application/vnd.openxmlformats-officedocument.extended-properties+xml',  # /docProps/app.xml
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',  # /word/document.xml
        'application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml',  # /word/fontTable.xml
        'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml',  # /word/footer.xml
        'application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml',  # /word/header.xml
        'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml',  # /word/styles.xml
        'application/vnd.openxmlformats-package.core-properties+xml',  # /docProps/core.xml

        # Do we want to keep the following ones?
        'application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml',

        # See https://0xacab.org/jvoisin/mat2/issues/71
        'application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml',  # /word/numbering.xml
    }


    def __init__(self, filename):
        super().__init__(filename)

        self.files_to_keep = set(map(re.compile, {  # type: ignore
            r'^\[Content_Types\]\.xml$',
            r'^_rels/\.rels$',
            r'^word/_rels/document\.xml\.rels$',
            r'^word/_rels/footer[0-9]*\.xml\.rels$',
            r'^word/_rels/header[0-9]*\.xml\.rels$',

            # https://msdn.microsoft.com/en-us/library/dd908153(v=office.12).aspx
            r'^word/stylesWithEffects\.xml$',
        }))
        self.files_to_omit = set(map(re.compile, {  # type: ignore
            r'^customXml/',
            r'webSettings\.xml$',
            r'^docProps/custom\.xml$',
            r'^word/printerSettings/',
            r'^word/theme',
            r'^word/people\.xml$',

            # we have an allowlist in self.files_to_keep,
            # so we can trash everything else
            r'^word/_rels/',
        }))

        if self.__fill_files_to_keep_via_content_types() is False:
            raise ValueError

    def __fill_files_to_keep_via_content_types(self) -> bool:
        """ There is a suer-handy `[Content_Types].xml` file
        in MS Office archives, describing what each other file contains.
        The self.content_types_to_keep member contains a type allowlist,
        so we're using it to fill the self.files_to_keep one.
        """
        with zipfile.ZipFile(self.filename) as zin:
            if '[Content_Types].xml' not in zin.namelist():
                return False
            xml_data = zin.read('[Content_Types].xml')

        self.content_types = dict()  # type: Dict[str, str]
        try:
            tree = ET.fromstring(xml_data)
        except ET.ParseError:
            return False
        for c in tree:
            if 'PartName' not in c.attrib or 'ContentType' not in c.attrib:
                continue
            elif c.attrib['ContentType'] in self.content_types_to_keep:
                fname = c.attrib['PartName'][1:]  # remove leading `/`
                re_fname = re.compile('^' + re.escape(fname) + '$')
                self.files_to_keep.add(re_fname)  # type: ignore
        return True

    @staticmethod
    def __remove_rsid(full_path: str) -> bool:
        """ The method will remove "revision session ID".  We're '}rsid'
        instead of proper parsing, since rsid can have multiple forms, like
        `rsidRDefault`, `rsidR`, `rsids`, …

        We're removing rsid tags in two times, because we can't modify
        the xml while we're iterating on it.

        For more details, see
        - https://msdn.microsoft.com/en-us/library/office/documentformat.openxml.wordprocessing.previoussectionproperties.rsidrpr.aspx
        - https://blogs.msdn.microsoft.com/brian_jones/2006/12/11/whats-up-with-all-those-rsids/
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError:
            return False

        # rsid, tags or attributes, are always under the `w` namespace
        if 'w' not in namespace.keys():
            return True

        parent_map = {c:p for p in tree.iter() for c in p}

        elements_to_remove = list()
        for item in tree.iterfind('.//', namespace):
            if '}rsid' in item.tag.strip().lower():  # rsid as tag
                elements_to_remove.append(item)
                continue
            for key in list(item.attrib.keys()):  # rsid as attribute
                if '}rsid' in key.lower():
                    del item.attrib[key]

        for element in elements_to_remove:
            parent_map[element].remove(element)

        tree.write(full_path, xml_declaration=True)
        return True

    @staticmethod
    def __remove_revisions(full_path: str) -> bool:
        """ In this function, we're changing the XML document in several
        different times, since we don't want to change the tree we're currently
        iterating on.
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        # Revisions are either deletions (`w:del`) or
        # insertions (`w:ins`)
        del_presence = tree.find('.//w:del', namespace)
        ins_presence = tree.find('.//w:ins', namespace)
        if del_presence is None and ins_presence is None:
            return True  # No revisions are present

        parent_map = {c:p for p in tree.iter() for c in p}

        elements_del = list()
        for element in tree.iterfind('.//w:del', namespace):
            elements_del.append(element)
        for element in elements_del:
            parent_map[element].remove(element)

        elements_ins = list()
        for element in tree.iterfind('.//w:ins', namespace):
            for position, item in enumerate(tree.iter()):  # pragma: no cover
                if item == element:
                    for children in element.iterfind('./*'):
                        elements_ins.append((element, position, children))
                    break
        for (element, position, children) in elements_ins:
            parent_map[element].insert(position, children)
            parent_map[element].remove(element)

        tree.write(full_path, xml_declaration=True)
        return True

    def __remove_content_type_members(self, full_path: str) -> bool:
        """ The method will remove the dangling references
        form the [Content_Types].xml file, since MS office doesn't like them
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError:  # pragma: no cover
            return False

        if len(namespace.items()) != 1:
            return False  # there should be only one namespace for Types

        removed_fnames = set()
        with zipfile.ZipFile(self.filename) as zin:
            for fname in [item.filename for item in zin.infolist()]:
                for file_to_omit in self.files_to_omit:
                    if file_to_omit.search(fname):
                        matches = map(lambda r: r.search(fname), self.files_to_keep)
                        if any(matches):  # the file is in the allowlist
                            continue
                        removed_fnames.add(fname)
                        break

        root = tree.getroot()
        for item in root.findall('{%s}Override' % namespace['']):
            name = item.attrib['PartName'][1:]  # remove the leading '/'
            if name in removed_fnames:
                root.remove(item)

        tree.write(full_path, xml_declaration=True)
        return True

    def _specific_cleanup(self, full_path: str) -> bool:
        # pylint: disable=too-many-return-statements
        if os.stat(full_path).st_size == 0:  # Don't process empty files
            return True

        if not full_path.endswith('.xml'):
            return True

        if full_path.endswith('/[Content_Types].xml'):
            # this file contains references to files that we might
            # remove, and MS Office doesn't like dangling references
            if self.__remove_content_type_members(full_path) is False:
                return False
        elif full_path.endswith('/word/document.xml'):
            # this file contains the revisions
            if self.__remove_revisions(full_path) is False:
                return False
        elif full_path.endswith('/docProps/app.xml'):
            # This file must be present and valid,
            # so we're removing as much as we can.
            with open(full_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
                f.write(b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">')
                f.write(b'</Properties>')
        elif full_path.endswith('/docProps/core.xml'):
            # This file must be present and valid,
            # so we're removing as much as we can.
            with open(full_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
                f.write(b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties">')
                f.write(b'</cp:coreProperties>')

        if self.__remove_rsid(full_path) is False:
            return False

        try:
            _sort_xml_attributes(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        # This is awful, I'm sorry.
        #
        # Microsoft Office isn't happy when we have the `mc:Ignorable`
        # tag containing namespaces that aren't present in the xml file,
        # so instead of trying to remove this specific tag with etree,
        # we're removing it, with a regexp.
        #
        # Since we're the ones producing this file, via the call to
        # _sort_xml_attributes, there won't be any "funny tricks".
        # Worst case, the tag isn't present, and everything is fine.
        #
        # see: https://docs.microsoft.com/en-us/dotnet/framework/wpf/advanced/mc-ignorable-attribute
        with open(full_path, 'rb') as f:
            text = f.read()
            out = re.sub(b'mc:Ignorable="[^"]*"', b'', text, 1)
        with open(full_path, 'wb') as f:
            f.write(out)

        return True

    def _specific_get_meta(self, full_path: str, file_path: str) -> Dict[str, Any]:
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        if not file_path.startswith('docProps/') or not file_path.endswith('.xml'):
            return {}

        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<(.+)>(.+)</\1>", f.read(), re.I|re.M)
                return {k:v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):
                # We didn't manage to parse the xml file
                return {file_path: 'harmful content', }


class LibreOfficeParser(ZipParser):
    mimetypes = {
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet',
        'application/vnd.oasis.opendocument.presentation',
        'application/vnd.oasis.opendocument.graphics',
        'application/vnd.oasis.opendocument.chart',
        'application/vnd.oasis.opendocument.formula',
        'application/vnd.oasis.opendocument.image',
    }


    def __init__(self, filename):
        super().__init__(filename)

        self.files_to_keep = set(map(re.compile, {  # type: ignore
            r'^META-INF/manifest\.xml$',
            r'^content\.xml$',
            r'^manifest\.rdf$',
            r'^mimetype$',
            r'^settings\.xml$',
            r'^styles\.xml$',
        }))
        self.files_to_omit = set(map(re.compile, {  # type: ignore
            r'^meta\.xml$',
            r'^Configurations2/',
            r'^Thumbnails/',
        }))

    @staticmethod
    def __remove_revisions(full_path: str) -> bool:
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        if 'office' not in namespace.keys():  # no revisions in the current file
            return True

        for text in tree.getroot().iterfind('.//office:text', namespace):
            for changes in text.iterfind('.//text:tracked-changes', namespace):
                text.remove(changes)

        tree.write(full_path, xml_declaration=True)
        return True

    def _specific_cleanup(self, full_path: str) -> bool:
        if os.stat(full_path).st_size == 0:  # Don't process empty files
            return True

        if os.path.basename(full_path).endswith('.xml'):
            if os.path.basename(full_path) == 'content.xml':
                if self.__remove_revisions(full_path) is False:
                    return False

            try:
                _sort_xml_attributes(full_path)
            except ET.ParseError as e:
                logging.error("Unable to parse %s: %s", full_path, e)
                return False
        return True

    def _specific_get_meta(self, full_path: str, file_path: str) -> Dict[str, Any]:
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        if file_path != 'meta.xml':
            return {}
        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<((?:meta|dc|cp).+?)[^>]*>(.+)</\1>", f.read(), re.I|re.M)
                return {k:v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):  # We didn't manage to parse the xml file
                # We didn't manage to parse the xml file
                return {file_path: 'harmful content', }
