import os
import re
import shutil
import tempfile
import datetime
import zipfile
import logging
from typing import Dict, Set, Pattern

try:  # protect against DoS
    from defusedxml import ElementTree as ET  # type: ignore
except ImportError:
    import xml.etree.ElementTree as ET  # type: ignore


from . import abstract, parser_factory

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


class ArchiveBasedAbstractParser(abstract.AbstractParser):
    """ Office files (.docx, .odt, …) are zipped files. """
    # Those are the files that have a format that _isn't_
    # supported by MAT2, but that we want to keep anyway.
    files_to_keep = set()  # type: Set[str]

    # Those are the files that we _do not_ want to keep,
    # no matter if they are supported or not.
    files_to_omit = set() # type: Set[Pattern]

    # what should the parser do if it encounters an unknown file in
    # the archive?  valid policies are 'abort', 'omit', 'keep'
    unknown_member_policy = 'abort' # type: str

    def __init__(self, filename):
        super().__init__(filename)
        try:  # better fail here than later
            zipfile.ZipFile(self.filename)
        except zipfile.BadZipFile:
            raise ValueError

    def _specific_cleanup(self, full_path: str) -> bool:
        """ This method can be used to apply specific treatment
        to files present in the archive."""
        # pylint: disable=unused-argument,no-self-use
        return True  # pragma: no cover

    @staticmethod
    def _clean_zipinfo(zipinfo: zipfile.ZipInfo) -> zipfile.ZipInfo:
        zipinfo.create_system = 3  # Linux
        zipinfo.comment = b''
        zipinfo.date_time = (1980, 1, 1, 0, 0, 0)  # this is as early as a zipfile can be
        return zipinfo

    @staticmethod
    def _get_zipinfo_meta(zipinfo: zipfile.ZipInfo) -> Dict[str, str]:
        metadata = {}
        if zipinfo.create_system == 3:  # this is Linux
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
        # pylint: disable=too-many-branches

        if self.unknown_member_policy not in ['omit', 'keep', 'abort']:
            logging.error("The policy %s is invalid.", self.unknown_member_policy)
            raise ValueError

        with zipfile.ZipFile(self.filename) as zin,\
             zipfile.ZipFile(self.output_filename, 'w') as zout:

            temp_folder = tempfile.mkdtemp()
            abort = False

            for item in zin.infolist():
                if item.filename[-1] == '/':  # `is_dir` is added in Python3.6
                    continue  # don't keep empty folders

                zin.extract(member=item, path=temp_folder)
                full_path = os.path.join(temp_folder, item.filename)

                if self._specific_cleanup(full_path) is False:
                    logging.warning("Something went wrong during deep cleaning of %s",
                                    item.filename)
                    abort = True
                    continue

                if item.filename in self.files_to_keep:
                    # those files aren't supported, but we want to add them anyway
                    pass
                elif any(map(lambda r: r.search(item.filename), self.files_to_omit)):
                    continue
                else:
                    # supported files that we want to clean then add
                    tmp_parser, mtype = parser_factory.get_parser(full_path)  # type: ignore
                    if not tmp_parser:
                        if self.unknown_member_policy == 'omit':
                            logging.warning("In file %s, omitting unknown element %s (format: %s)",
                                            self.filename, item.filename, mtype)
                            continue
                        elif self.unknown_member_policy == 'keep':
                            logging.warning("In file %s, keeping unknown element %s (format: %s)",
                                            self.filename, item.filename, mtype)
                        else:
                            logging.error("In file %s, element %s's format (%s) " +
                                          "isn't supported",
                                          self.filename, item.filename, mtype)
                            abort = True
                            continue
                    if tmp_parser:
                        tmp_parser.remove_all()
                        os.rename(tmp_parser.output_filename, full_path)

                zinfo = zipfile.ZipInfo(item.filename)  # type: ignore
                clean_zinfo = self._clean_zipinfo(zinfo)
                with open(full_path, 'rb') as f:
                    zout.writestr(clean_zinfo, f.read())

        shutil.rmtree(temp_folder)
        if abort:
            os.remove(self.output_filename)
            return False
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
