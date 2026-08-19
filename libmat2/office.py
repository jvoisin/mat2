from __future__ import annotations

import random
import uuid
import logging
import os
import posixpath
import re
import zipfile
from typing import Any

import xml.etree.ElementTree as ET  # type: ignore

from .archive import ZipParser

# pylint: disable=line-too-long


def _parse_xml(full_path: str) -> tuple[ET.ElementTree, dict[str, str]]:
    """ This function parses XML, with namespace support. """
    namespace_map = dict()
    for _, (key, value) in ET.iterparse(full_path, ("start-ns", )):
        # The ns[0-9]+ namespaces are reserved for internal usage, so
        # we have to use an other nomenclature.
        if re.match('^ns[0-9]+$', key, re.IGNORECASE):  # pragma: no cover
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

    for element in tree.iter():
        if len(element.attrib) < 2:
            continue
        attributes = sorted(element.attrib.items())
        element.attrib.clear()
        element.attrib.update(attributes)

    tree.write(full_path, xml_declaration=True, encoding='utf-8')
    return True


class MSOfficeParser(ZipParser):
    """
    The methods modifying XML documents are usually doing so in two loops:
        1. finding the tag/attributes to remove;
        2. actually editing the document
    since it's tricky to modify the XML while iterating on it.
    """
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
        'application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml',  # /word/numbering.xml (used for bullet point formatting)
        'application/vnd.openxmlformats-officedocument.theme+xml',  # /word/theme/theme[0-9].xml (used for font and background coloring, etc.)
        'application/vnd.openxmlformats-package.core-properties+xml',  # /docProps/core.xml

        # for more complicated powerpoints
        'application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml',
        'application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml',
        'application/vnd.openxmlformats-officedocument.presentationml.handoutMaster+xml',
        'application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml',
        'application/vnd.openxmlformats-officedocument.drawingml.diagramLayout+xml',
        'application/vnd.openxmlformats-officedocument.drawingml.diagramStyle+xml',
        'application/vnd.openxmlformats-officedocument.drawingml.diagramColors+xml',
        'application/vnd.ms-office.drawingml.diagramDrawing+xml',

        # Do we want to keep the following ones?
        'application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml',
    }

    def __init__(self, filename):
        super().__init__(filename)

        # MSOffice documents are using various counters for cross-references,
        # we collect them all, to make sure that they're effectively counters,
        # and not unique id used for fingerprinting.
        self.__counters = {
            'cNvPr': set(),
            'rid': set(),
            }
        self.__members_to_remove: set[str] | None = None
        self.__rels_members: dict[str, bytes] | None = None

        self.files_to_keep = set(map(re.compile, {  # type: ignore
            r'^\[Content_Types\]\.xml$',
            r'^_rels/\.rels$',
            r'^xl/sharedStrings\.xml$',  # https://docs.microsoft.com/en-us/office/open-xml/working-with-the-shared-string-table
            r'^xl/calcChain\.xml$',
            r'^(?:word|ppt|xl)/_rels/(document|workbook|presentation)\.xml\.rels$',
            r'^(?:word|ppt|xl)/_rels/footer[0-9]*\.xml\.rels$',
            r'^(?:word|ppt|xl)/_rels/header[0-9]*\.xml\.rels$',
            r'^(?:word|ppt|xl)/charts/_rels/chart[0-9]+\.xml\.rels$',
            r'^(?:word|ppt|xl)/charts/colors[0-9]+\.xml$',
            r'^(?:word|ppt|xl)/charts/style[0-9]+\.xml$',
            r'^(?:word|ppt|xl)/drawings/_rels/drawing[0-9]+\.xml\.rels$',
            r'^(?:word|ppt|xl)/styles\.xml$',
            # TODO: randomize axId ( https://docs.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/089f849f-fcd6-4fa0-a281-35aa6a432a16 )
            r'^(?:word|ppt|xl)/charts/chart[0-9]*\.xml$',
            r'^xl/workbook\.xml$',
            r'^xl/worksheets/sheet[0-9]+\.xml$',
            r'^ppt/slideLayouts/_rels/slideLayout[0-9]+\.xml\.rels$',
            r'^ppt/slideLayouts/slideLayout[0-9]+\.xml$',
            r'^(?:word|ppt|xl)/tableStyles\.xml$',
            r'^(?:word|ppt|xl)/tables/table[0-9]+\.xml$',
            r'^ppt/slides/_rels/slide[0-9]*\.xml\.rels$',
            r'^ppt/slides/slide[0-9]*\.xml$',
            # https://msdn.microsoft.com/en-us/library/dd908153(v=office.12).aspx
            r'^(?:word|ppt|xl)/stylesWithEffects\.xml$',
            r'^ppt/presentation\.xml$',
            # TODO: check if p:bgRef can be randomized
            r'^ppt/slideMasters/slideMaster[0-9]+\.xml',
            r'^ppt/slideMasters/_rels/slideMaster[0-9]+\.xml\.rels',
            r'^xl/worksheets/_rels/sheet[0-9]+\.xml\.rels',
            r'^(?:word|ppt|xl)/drawings/vmlDrawing[0-9]+\.vml',
            r'^(?:word|ppt|xl)/drawings/drawing[0-9]+\.xml',
            r'^(?:word|ppt|xl)/embeddings/Microsoft_Excel_Worksheet[0-9]+\.xlsx',
            # rels for complicated powerpoints
            r'^ppt/notesSlides/_rels/notesSlide[0-9]+\.xml\.rels',
            r'^ppt/notesMasters/_rels/notesMaster[0-9]+\.xml\.rels',
            r'^ppt/handoutMasters/_rels/handoutMaster[0-9]+\.xml\.rels',
        }))
        self.files_to_omit = set(map(re.compile, {  # type: ignore
            r'^\[trash\]/',
            r'^customXml/',
            r'webSettings\.xml$',
            r'^docProps/custom\.xml$',
            r'^docProps/thumbnail.wmf$',
            r'^(?:word|ppt|xl)/printerSettings/',
            r'^(?:word|ppt|xl)/theme',
            r'^(?:word|ppt|xl)/people\.xml$',
            r'^(?:word|ppt|xl)/persons/person\.xml$',
            r'^(?:word|ppt|xl)/numbering\.xml$',
            r'^(?:word|ppt|xl)/tags/',
            r'^(?:word|ppt|xl)/glossary/',
            # View properties like view mode, last viewed slide etc
            r'^(?:word|ppt|xl)/viewProps\.xml$',
            # Additional presentation-wide properties like printing properties,
            # presentation show properties etc.
            r'^(?:word|ppt|xl)/presProps\.xml$',
            r'^(?:word|ppt|xl)/comments[0-9]*\.xml$',
            r'^(?:word|ppt|xl)/threadedComments/threadedComment[0-9]*\.xml$',
            r'^(?:word|ppt|xl)/commentsExtended\.xml$',
            r'^(?:word|ppt|xl)/commentsExtensible\.xml$',
            r'^(?:word|ppt|xl)/commentsIds\.xml$',
            # we have an allowlist in self.files_to_keep,
            # so we can trash everything else
            r'^(?:word|ppt|xl)/_rels/',
            r'docMetadata/LabelInfo\.xml$'
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

        self.content_types: dict[str, str] = dict()
        try:
            tree = ET.fromstring(xml_data)
        except ET.ParseError:
            return False
        for c in tree:
            if 'PartName' not in c.attrib or 'ContentType' not in c.attrib:  # pragma: no cover
                continue
            elif c.attrib['ContentType'] in self.content_types_to_keep:
                fname = c.attrib['PartName'][1:]  # remove leading `/`
                re_fname = re.compile('^' + re.escape(fname) + '$')
                self.files_to_keep.add(re_fname)  # type: ignore
        return True

    @staticmethod
    def __remove_rsid(full_path: str) -> bool:
        """ The method will remove "revision session ID".  We're using '}rsid'
        instead of proper parsing, since rsid can have multiple forms, like
        `rsidRDefault`, `rsidR`, `rsids`, …

        For more details, see
        - https://msdn.microsoft.com/en-us/library/office/documentformat.openxml.wordprocessing.previoussectionproperties.rsidrpr.aspx
        - https://blogs.msdn.microsoft.com/brian_jones/2006/12/11/whats-up-with-all-those-rsids/
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        # rsid, tags or attributes, are always under the `w` namespace
        if 'w' not in namespace:
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

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    @staticmethod
    def __remove_nsid(full_path: str) -> bool:
        """
        nsid are random identifiers that can be used to ease the merging of
        some components of a document.  They can also be used for
        fingerprinting.

        See the spec for more details: https://docs.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.nsid?view=openxml-2.8.1
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        # The nsid tag is always under the `w` namespace
        if 'w' not in namespace:
            return True

        parent_map = {c: p for p in tree.iter() for c in p}

        elements_to_remove = list()
        for element in tree.iterfind('.//w:nsid', namespace):
            elements_to_remove.append(element)
        for element in elements_to_remove:
            parent_map[element].remove(element)

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    @staticmethod
    def __remove_revisions(full_path: str) -> bool:
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        # Revisions are deletions (`w:del`), insertions (`w:ins`), or moves,
        # which are a `w:moveFrom`/`w:moveTo` pair plus their range markers.
        revisions =('w:del', 'w:ins', 'w:moveFrom', 'w:moveTo',
                     'w:moveFromRangeStart', 'w:moveFromRangeEnd',
                     'w:moveToRangeStart', 'w:moveToRangeEnd')
        if all(tree.find('.//' + r, namespace) is None for r in revisions):
            return True  # No revisions are present

        parent_map = {c:p for p in tree.iter() for c in p}

        elements_del = list()
        for tag in ('w:del', 'w:moveFrom', 'w:moveFromRangeStart',
                    'w:moveFromRangeEnd', 'w:moveToRangeStart',
                    'w:moveToRangeEnd'):
            for element in tree.iterfind('.//' + tag, namespace):
                elements_del.append(element)
        for element in elements_del:
            parent_map[element].remove(element)

        elements_ins = list()
        for tag in ('w:ins', 'w:moveTo'):
            for element in tree.iterfind('.//' + tag, namespace):
                elements_ins.append(element)

        # Keep the children where the wrapper was. The index has to be the
        # element's position among its own siblings, not its position in a
        # walk of the whole tree, or the content lands at the end of the
        # paragraph and the sentence comes out reordered.
        for element in elements_ins:
            parent = parent_map[element]
            position = list(parent).index(element)
            for offset, children in enumerate(list(element)):
                parent.insert(position + offset, children)
            if element in parent:
                parent.remove(element)

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    @staticmethod
    def __remove_document_comment_meta(full_path: str) -> bool:
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        # search the docs to see if we can bail early
        range_start = tree.find('.//w:commentRangeStart', namespace)
        range_end = tree.find('.//w:commentRangeEnd', namespace)
        references = tree.find('.//w:commentReference', namespace)
        if range_start is None and range_end is None and references is None:
            return True  # No comment meta tags are present

        parent_map = {c:p for p in tree.iter() for c in p}

        # iterate over the elements and add them to list
        elements_del = list()
        for element in tree.iterfind('.//w:commentRangeStart', namespace):
            elements_del.append(element)
        for element in tree.iterfind('.//w:commentRangeEnd', namespace):
            elements_del.append(element)
        for element in tree.iterfind('.//w:commentReference', namespace):
            elements_del.append(element)

        # remove the elements
        for element in elements_del:
            parent_map[element].remove(element)

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    def __get_members_to_remove(self) -> set[str]:
        """ The set of members that `remove_all` will drop from the archive. """
        if self.__members_to_remove is not None:
            return self.__members_to_remove

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
        self.__members_to_remove = removed_fnames
        return removed_fnames

    def __get_rels_members(self) -> dict[str, bytes]:
        """ The content of every `.rels` member, read in a single pass over
        the archive. """
        if self.__rels_members is None:
            with zipfile.ZipFile(self.filename) as zin:
                self.__rels_members = {name: zin.read(name)
                                       for name in zin.namelist()
                                       if name.endswith('.rels')}
        return self.__rels_members

    @staticmethod
    def __resolve_rel_target(base: str, target: str) -> str:
        """ Resolve a relationship `Target` (`../customXml/item1.xml`,
        `/word/styles.xml`, `media/image1.png`, `#_Toc42`, …) against `base`
        into a zip member name. Returns an empty string when the target is
        only a bookmark, not a part.

        Zip member names use forward slashes on every platform, hence
        posixpath rather than os.path.
        """
        target = target.partition('#')[0]  # `styles.xml#anchor` -> `styles.xml`
        if not target:
            return ''
        if target.startswith('/'):  # already relative to the package root
            return target.removeprefix('/')
        return posixpath.normpath(posixpath.join(base, target))

    def __dead_rel_ids(self, member_name: str) -> set[str]:
        """ The relationship ids of `member_name` that point at a part
        `remove_all` drops. """
        rels_name = posixpath.join(posixpath.dirname(member_name), '_rels',
                                   posixpath.basename(member_name) + '.rels')
        base = posixpath.dirname(member_name)
        dead: set[str] = set()
        content = self.__get_rels_members().get(rels_name)
        if content is None:
            return dead
        try:
            root = ET.fromstring(content)
        except ET.ParseError:  # pragma: no cover
            return dead
        members_to_remove = self.__get_members_to_remove()
        for item in root:
            if item.attrib.get('TargetMode') == 'External':
                continue
            name = self.__resolve_rel_target(base, item.attrib.get('Target', ''))
            if not name:
                continue
            if name in members_to_remove:
                dead.add(item.attrib['Id'])
        return dead

    def __remove_dead_rel_references(self, full_path: str, member_name: str) -> bool:
        """ Drop the `r:id`/`r:embed`/… attributes pointing at relationships
        that `__remove_rels_members` takes away, so that the part doesn't
        reference a relationship that no longer exists. """
        dead = self.__dead_rel_ids(member_name)
        if not dead:
            return True

        try:
            tree, _ = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        namespace = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
        changed = False
        for element in tree.iter():
            for key in [k for k, v in element.attrib.items()
                        if k.startswith(namespace) and v in dead]:
                del element.attrib[key]
                changed = True

        if changed:
            tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    def __remove_rels_members(self, full_path: str, member_name: str) -> bool:
        """ Remove the dangling references from a `.rels` file, since MS Office
        doesn't like them.

        Relationship targets are resolved against the folder holding the
        `_rels` directory, so `word/_rels/document.xml.rels` pointing at
        `../customXml/item1.xml` refers to `customXml/item1.xml`.
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        if len(namespace.items()) != 1:  # pragma: no cover
            logging.getLogger(__name__).debug("Got several namespaces for Types: %s", namespace.items())

        members_to_remove = self.__get_members_to_remove()
        # the base is `word` for `word/_rels/document.xml.rels`,
        # and the package root for `_rels/.rels`
        base = posixpath.dirname(posixpath.dirname(member_name))

        root = tree.getroot()
        for item in root.findall('{%s}Relationship' % namespace['']):
            if item.attrib.get('TargetMode') == 'External':
                continue
            name = self.__resolve_rel_target(base, item.attrib['Target'])
            if not name:  # a link to a bookmark, not to a part
                continue
            if name in members_to_remove:
                root.remove(item)

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    def __remove_content_type_members(self, full_path: str) -> bool:
        """ The method will remove the dangling references
        form the [Content_Types].xml file, since MS office doesn't like them
        """
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        if len(namespace.items()) != 1:  # pragma: no cover
            logging.getLogger(__name__).debug("Got several namespaces for Types: %s", namespace.items())

        members_to_remove = self.__get_members_to_remove()

        root = tree.getroot()
        for item in root.findall('{%s}Override' % namespace['']):
            name = item.attrib['PartName'][1:]  # remove the leading '/'
            if name in members_to_remove:
                root.remove(item)

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    def _final_checks(self) -> bool:
        for k, v in self.__counters.items():
            if v and len(v) != max(v):
                # TODO: make this an error and return False
                # once the ability to correct the counters is implemented
                logging.warning("%s contains invalid %s: %s", self.filename, k, v)
                return True
        return True

    def __collect_counters(self, full_path: str):
        with open(full_path, encoding='utf-8') as f:
            content = f.read()
            # "relationship Id"
            for i in re.findall(r'(?:\s|r:)[iI][dD]="rId([0-9]+)"(?:\s|/)', content):
                self.__counters['rid'].add(int(i))
            # "connector for Non-visual property"
            for i in re.findall(r'<p:cNvPr id="([0-9]+)"', content):
                self.__counters['cNvPr'].add(int(i))

    @staticmethod
    def __randomize_creationId(full_path: str) -> bool:
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        if 'p14' not in namespace:
            return True  # pragma: no cover

        for item in tree.iterfind('.//p14:creationId', namespace):
            item.set('val', '%s' % random.randint(0, 2**32))
        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    @staticmethod
    def __randomize_sldMasterId(full_path: str) -> bool:
        try:
            tree, namespace = _parse_xml(full_path)
        except ET.ParseError as e:  # pragma: no cover
            logging.error("Unable to parse %s: %s", full_path, e)
            return False

        if 'p' not in namespace:
            return True  # pragma: no cover

        for item in tree.iterfind('.//p:sldMasterId', namespace):
            item.set('id', '%s' % random.randint(0, 2**32))
        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    def _specific_cleanup(self, full_path: str, member_name: str = '') -> bool:
        # pylint: disable=too-many-return-statements,too-many-branches
        if os.stat(full_path).st_size == 0:  # Don't process empty files
            return True

        if not full_path.endswith(('.xml', '.rels')):
            return True

        if self.__randomize_creationId(full_path) is False:
            return False

        self.__collect_counters(full_path)

        if not member_name.endswith('.rels'):
            # the part might point at relationships that are about to go away
            if self.__remove_dead_rel_references(full_path, member_name) is False:  # pragma: no cover
                return False

        if full_path.endswith('/[Content_Types].xml'):
            # this file contains references to files that we might
            # remove, and MS Office doesn't like dangling references
            if self.__remove_content_type_members(full_path) is False:  # pragma: no cover
                return False
        elif full_path.endswith('/word/document.xml'):
            # this file contains the revisions
            if self.__remove_revisions(full_path) is False:
                return False  # pragma: no cover
            # remove comment references and ranges
            if self.__remove_document_comment_meta(full_path) is False:
                return False  # pragma: no cover
        elif member_name.endswith('.rels'):
            # similar to the above, but for the relationship files
            if self.__remove_rels_members(full_path, member_name) is False:  # pragma: no cover
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
        elif full_path.endswith('/ppt/tableStyles.xml'):  # pragma: no cover
            # This file must be present and valid,
            # so we're removing as much as we can.
            with open(full_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
                uid = str(uuid.uuid4()).encode('utf-8')
                f.write(b'<a:tblStyleLst def="{%s}" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>' % uid)
        elif full_path.endswith('ppt/presentation.xml'):
            if self.__randomize_sldMasterId(full_path) is False:
                return False  # pragma: no cover

        if self.__remove_rsid(full_path) is False:
            return False  # pragma: no cover

        if self.__remove_nsid(full_path) is False:
            return False  # pragma: no cover

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
            out = re.sub(b'mc:Ignorable="[^"]*"', b'', text, count=1)
        with open(full_path, 'wb') as f:
            f.write(out)

        return True

    def _specific_get_meta(self, full_path: str, file_path: str) -> dict[str, Any]:
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        if not file_path.startswith('docProps/') or not file_path.endswith('.xml'):
            return {}

        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<(.+)>(.+)</\1>", f.read(), re.IGNORECASE | re.MULTILINE)
                return {k: v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):
                # We didn't manage to parse the xml file
                return {file_path: 'harmful content', }


class LibreOfficeParser(ZipParser):
    mimetypes = {
        'application/vnd.oasis.opendocument.chart',
        'application/vnd.oasis.opendocument.formula',
        'application/vnd.oasis.opendocument.graphics',
        'application/vnd.oasis.opendocument.image',
        'application/vnd.oasis.opendocument.presentation',
        'application/vnd.oasis.opendocument.spreadsheet',
        'application/vnd.oasis.opendocument.text',
    }

    def __init__(self, filename):
        super().__init__(filename)

        self.files_to_keep = set(map(re.compile, {  # type: ignore
            r'^META-INF/manifest\.xml$',
            r'^(?:Object\s\d+/)?content\.xml$',
            r'^manifest\.rdf$',
            r'^mimetype$',
            r'^settings\.xml$',
            r'^(?:Object\s\d+/)?styles\.xml$',
        }))
        self.files_to_omit = set(map(re.compile, {  # type: ignore
            r'^ObjectReplacements/',
            r'meta\.xml$',
            r'^layout-cache$',
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

        if 'office' not in namespace:  # no revisions in the current file
            return True

        for text in tree.getroot().iterfind('.//office:text', namespace):
            for changes in text.iterfind('.//text:tracked-changes', namespace):
                text.remove(changes)

        tree.write(full_path, xml_declaration=True, encoding='utf-8')
        return True

    def _specific_cleanup(self, full_path: str, member_name: str = '') -> bool:
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

    def _specific_get_meta(self, full_path: str, file_path: str) -> dict[str, Any]:
        """
        Yes, I know that parsing xml with regexp ain't pretty,
        be my guest and fix it if you want.
        """
        if file_path != 'meta.xml':
            return {}
        with open(full_path, encoding='utf-8') as f:
            try:
                results = re.findall(r"<((?:meta|dc|cp).+?)[^>]*>(.+)</\1>", f.read(), re.IGNORECASE|re.MULTILINE)
                return {k:v for (k, v) in results}
            except (TypeError, UnicodeDecodeError):  # We didn't manage to parse the xml file
                # We didn't manage to parse the xml file
                return {file_path: 'harmful content', }
