import abc
import stat
import zipfile
import datetime
import tarfile
import tempfile
import os
import logging
import shutil
from typing import Dict, Set, Pattern, Union, Any, List

from . import abstract, UnknownMemberPolicy, parser_factory

# Make pyflakes happy
assert Set
assert Pattern

# pylint: disable=not-callable,assignment-from-no-return,too-many-branches

# An ArchiveClass is a class representing an archive,
# while an ArchiveMember is a class representing an element
# (usually a file) of an archive.
ArchiveClass = Union[zipfile.ZipFile, tarfile.TarFile]
ArchiveMember = Union[zipfile.ZipInfo, tarfile.TarInfo]


class ArchiveBasedAbstractParser(abstract.AbstractParser):
    """Base class for all archive-based formats.

    Welcome to a world of frustrating complexity and tediouness:
        - A lot of file formats (docx, odt, epubs, …) are archive-based,
          so we need to add callbacks erverywhere to allow their respective
          parsers to apply specific cleanup to the required files.
        - Python has two different modules to deal with .tar and .zip files,
          with similar-but-yet-o-so-different API, so we need to write
          a ghetto-wrapper to avoid duplicating everything
        - The combination of @staticmethod and @abstractstaticmethod is
          required because for now, mypy doesn't know that
          @abstractstaticmethod is, indeed, a static method.
        - Mypy is too dumb (yet) to realise that a type A is valid under
          the Union[A, B] constrain, hence the weird `#  type: ignore`
          annotations.
    """
    # Tarfiles can optionally support compression
    # https://docs.python.org/3/library/tarfile.html#tarfile.open
    compression = ''

    def __init__(self, filename):
        super().__init__(filename)
        self.archive_class = None  #  type: Optional[ArchiveClass]
        self.member_class = None  #  type: Optional[ArchiveMember]

        # Those are the files that have a format that _isn't_
        # supported by MAT2, but that we want to keep anyway.
        self.files_to_keep = set()  # type: Set[Pattern]

        # Those are the files that we _do not_ want to keep,
        # no matter if they are supported or not.
        self.files_to_omit = set()  # type: Set[Pattern]

        # what should the parser do if it encounters an unknown file in
        # the archive?
        self.unknown_member_policy = UnknownMemberPolicy.ABORT  # type: UnknownMemberPolicy

        self.is_archive_valid()

    def is_archive_valid(self):
        """Raise a ValueError is the current archive isn't a valid one."""

    def _specific_cleanup(self, full_path: str) -> bool:
        """ This method can be used to apply specific treatment
        to files present in the archive."""
        # pylint: disable=unused-argument,no-self-use
        return True  # pragma: no cover

    def _specific_get_meta(self, full_path: str, file_path: str) -> Dict[str, Any]:
        """ This method can be used to extract specific metadata
        from files present in the archive."""
        # pylint: disable=unused-argument,no-self-use
        return {}  # pragma: no cover

    @staticmethod
    @abc.abstractstaticmethod
    def _get_all_members(archive: ArchiveClass) -> List[ArchiveMember]:
        """Return all the members of the archive."""

    @staticmethod
    @abc.abstractstaticmethod
    def _clean_member(member: ArchiveMember) -> ArchiveMember:
        """Remove all the metadata for a given member."""

    @staticmethod
    @abc.abstractstaticmethod
    def _get_member_meta(member: ArchiveMember) -> Dict[str, str]:
        """Return all the metadata of a given member."""

    @staticmethod
    @abc.abstractstaticmethod
    def _get_member_name(member: ArchiveMember) -> str:
        """Return the name of the given member."""

    @staticmethod
    @abc.abstractstaticmethod
    def _add_file_to_archive(archive: ArchiveClass, member: ArchiveMember,
                             full_path: str):
        """Add the file at full_path to the archive, via the given member."""

    @staticmethod
    def _set_member_permissions(member: ArchiveMember, permissions: int) -> ArchiveMember:
        """Set the permission of the archive member."""
        # pylint: disable=unused-argument
        return member

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        meta = dict()  # type: Dict[str, Union[str, dict]]

        with self.archive_class(self.filename) as zin:
            temp_folder = tempfile.mkdtemp()

            for item in self._get_all_members(zin):
                local_meta = self._get_member_meta(item)
                member_name = self._get_member_name(item)

                if member_name[-1] == '/':  # pragma: no cover
                    # `is_dir` is added in Python3.6
                    continue  # don't keep empty folders

                zin.extract(member=item, path=temp_folder)
                full_path = os.path.join(temp_folder, member_name)
                os.chmod(full_path, stat.S_IRUSR)

                specific_meta = self._specific_get_meta(full_path, member_name)
                local_meta = {**local_meta, **specific_meta}

                member_parser, _ = parser_factory.get_parser(full_path)  # type: ignore
                if member_parser:
                    local_meta = {**local_meta, **member_parser.get_meta()}

                if local_meta:
                    meta[member_name] = local_meta

        shutil.rmtree(temp_folder)
        return meta

    def remove_all(self) -> bool:
        # pylint: disable=too-many-branches

        with self.archive_class(self.filename) as zin,\
             self.archive_class(self.output_filename, 'w' + self.compression) as zout:

            temp_folder = tempfile.mkdtemp()
            abort = False

            # Sort the items to process, to reduce fingerprinting,
            # and keep them in the `items` variable.
            items = list()  # type: List[ArchiveMember]
            for item in sorted(self._get_all_members(zin), key=self._get_member_name):
                # Some fileformats do require to have the `mimetype` file
                # as the first file in the archive.
                if self._get_member_name(item) == 'mimetype':
                    items = [item] + items
                else:
                    items.append(item)

            # Since files order is a fingerprint factor,
            # we're iterating (and thus inserting) them in lexicographic order.
            for item in items:
                member_name = self._get_member_name(item)
                if member_name[-1] == '/':  # `is_dir` is added in Python3.6
                    continue  # don't keep empty folders

                zin.extract(member=item, path=temp_folder)
                full_path = os.path.join(temp_folder, member_name)

                original_permissions = os.stat(full_path).st_mode
                os.chmod(full_path, original_permissions | stat.S_IWUSR | stat.S_IRUSR)

                if self._specific_cleanup(full_path) is False:
                    logging.warning("Something went wrong during deep cleaning of %s",
                                    member_name)
                    abort = True
                    continue

                if any(map(lambda r: r.search(member_name), self.files_to_keep)):
                    # those files aren't supported, but we want to add them anyway
                    pass
                elif any(map(lambda r: r.search(member_name), self.files_to_omit)):
                    continue
                else:  # supported files that we want to first clean, then add
                    member_parser, mtype = parser_factory.get_parser(full_path)  # type: ignore
                    if not member_parser:
                        if self.unknown_member_policy == UnknownMemberPolicy.OMIT:
                            logging.warning("In file %s, omitting unknown element %s (format: %s)",
                                            self.filename, member_name, mtype)
                            continue
                        elif self.unknown_member_policy == UnknownMemberPolicy.KEEP:
                            logging.warning("In file %s, keeping unknown element %s (format: %s)",
                                            self.filename, member_name, mtype)
                        else:
                            logging.error("In file %s, element %s's format (%s) " \
                                          "isn't supported",
                                          self.filename, member_name, mtype)
                            abort = True
                            continue
                    else:
                        if member_parser.remove_all() is False:
                            logging.warning("In file %s, something went wrong \
                                             with the cleaning of %s \
                                             (format: %s)",
                                            self.filename, member_name, mtype)
                            abort = True
                            continue
                        os.rename(member_parser.output_filename, full_path)

                zinfo = self.member_class(member_name)  # type: ignore
                zinfo = self._set_member_permissions(zinfo, original_permissions)
                clean_zinfo = self._clean_member(zinfo)
                self._add_file_to_archive(zout, clean_zinfo, full_path)

        shutil.rmtree(temp_folder)
        if abort:
            os.remove(self.output_filename)
            return False
        return True


class TarParser(ArchiveBasedAbstractParser):
    mimetypes = {'application/x-tar'}
    def __init__(self, filename):
        super().__init__(filename)
        # yes, it's tarfile.open and not tarfile.TarFile,
        # as stated in the documentation:
        # https://docs.python.org/3/library/tarfile.html#tarfile.TarFile
        # This is required to support compressed archives.
        self.archive_class = tarfile.open
        self.member_class = tarfile.TarInfo

    def is_archive_valid(self):
        if tarfile.is_tarfile(self.filename) is False:
            raise ValueError
        self.__check_tarfile_safety()

    def __check_tarfile_safety(self):
        """Checks if the tarfile doesn't have any "suspicious" members.

        This is a rewrite of this patch: https://bugs.python.org/file47826/safetarfile-4.diff
        inspired by this bug from 2014: https://bugs.python.org/issue21109
        because Python's stdlib doesn't provide a way to "safely" extract
        things from a tar file.
        """
        names = set()
        with tarfile.open(self.filename) as f:
            members = f.getmembers()
        for member in members:
            name = member.name
            if os.path.isabs(name):
                raise ValueError("The archive %s contains a file with an " \
                        "absolute path: %s" % (self.filename, name))
            elif os.path.normpath(name).startswith('../') or '/../' in name:
                raise ValueError("The archive %s contains a file with an " \
                        "path traversal attack: %s" % (self.filename, name))

            if name in names:
                raise ValueError("The archive %s contains two times the same " \
                        "file: %s" % (self.filename, name))
            else:
                names.add(name)

            if member.isfile():
                if member.mode & stat.S_ISUID:
                    raise ValueError("The archive %s contains a setuid file: %s" % \
                        (self.filename, name))
                elif member.mode & stat.S_ISGID:
                    raise ValueError("The archive %s contains a setgid file: %s" % \
                            (self.filename, name))
            elif member.issym():
                linkname = member.linkname
                if os.path.normpath(linkname).startswith('..'):
                    raise ValueError('The archive %s contains a symlink pointing' \
                            'outside of the archive via a path traversal: %s -> %s' % \
                            (self.filename, name, linkname))
                if os.path.isabs(linkname):
                    raise ValueError('The archive %s contains a symlink pointing' \
                            'outside of the archive: %s -> %s' % \
                            (self.filename, name, linkname))
            elif member.isdev():
                raise ValueError("The archive %s contains a non-regular " \
                        "file: %s" % (self.filename, name))
            elif member.islnk():
                raise ValueError("The archive %s contains a hardlink: %s" \
                        % (self.filename, name))

    @staticmethod
    def _clean_member(member: ArchiveMember) -> ArchiveMember:
        assert isinstance(member, tarfile.TarInfo)  # please mypy
        member.mtime = member.uid = member.gid = 0
        member.uname = member.gname = ''
        return member

    @staticmethod
    def _get_member_meta(member: ArchiveMember) -> Dict[str, str]:
        assert isinstance(member, tarfile.TarInfo)  # please mypy
        metadata = {}
        if member.mtime != 0:
            metadata['mtime'] = str(datetime.datetime.fromtimestamp(member.mtime))
        if member.uid != 0:
            metadata['uid'] = str(member.uid)
        if member.gid != 0:
            metadata['gid'] = str(member.gid)
        if member.uname != '':
            metadata['uname'] = member.uname
        if member.gname != '':
            metadata['gname'] = member.gname
        return metadata

    @staticmethod
    def _add_file_to_archive(archive: ArchiveClass, member: ArchiveMember,
                             full_path: str):
        assert isinstance(member, tarfile.TarInfo)  # please mypy
        assert isinstance(archive, tarfile.TarFile)  # please mypy
        archive.add(full_path, member.name, filter=TarParser._clean_member)  # type: ignore

    @staticmethod
    def _get_all_members(archive: ArchiveClass) -> List[ArchiveMember]:
        assert isinstance(archive, tarfile.TarFile)  # please mypy
        return archive.getmembers()  # type: ignore

    @staticmethod
    def _get_member_name(member: ArchiveMember) -> str:
        assert isinstance(member, tarfile.TarInfo)  # please mypy
        return member.name

    @staticmethod
    def _set_member_permissions(member: ArchiveMember, permissions: int) -> ArchiveMember:
        assert isinstance(member, tarfile.TarInfo)  # please mypy
        member.mode = permissions
        return member


class TarGzParser(TarParser):
    compression = ':gz'
    mimetypes = {'application/x-tar+gz'}


class TarBz2Parser(TarParser):
    compression = ':bz2'
    mimetypes = {'application/x-tar+bz2'}


class TarXzParser(TarParser):
    compression = ':xz'
    mimetypes = {'application/x-tar+xz'}


class ZipParser(ArchiveBasedAbstractParser):
    mimetypes = {'application/zip'}
    def __init__(self, filename):
        super().__init__(filename)
        self.archive_class = zipfile.ZipFile
        self.member_class = zipfile.ZipInfo

    def is_archive_valid(self):
        try:
            zipfile.ZipFile(self.filename)
        except zipfile.BadZipFile:
            raise ValueError

    @staticmethod
    def _clean_member(member: ArchiveMember) -> ArchiveMember:
        assert isinstance(member, zipfile.ZipInfo)  # please mypy
        member.create_system = 3  # Linux
        member.comment = b''
        member.date_time = (1980, 1, 1, 0, 0, 0)  # this is as early as a zipfile can be
        return member

    @staticmethod
    def _get_member_meta(member: ArchiveMember) -> Dict[str, str]:
        assert isinstance(member, zipfile.ZipInfo)  # please mypy
        metadata = {}
        if member.create_system == 3:  # this is Linux
            pass
        elif member.create_system == 2:
            metadata['create_system'] = 'Windows'
        else:
            metadata['create_system'] = 'Weird'

        if member.comment:
            metadata['comment'] = member.comment  # type: ignore

        if member.date_time != (1980, 1, 1, 0, 0, 0):
            metadata['date_time'] = str(datetime.datetime(*member.date_time))

        return metadata

    @staticmethod
    def _add_file_to_archive(archive: ArchiveClass, member: ArchiveMember,
                             full_path: str):
        assert isinstance(archive, zipfile.ZipFile)  # please mypy
        assert isinstance(member, zipfile.ZipInfo)  # please mypy
        with open(full_path, 'rb') as f:
            archive.writestr(member, f.read())

    @staticmethod
    def _get_all_members(archive: ArchiveClass) -> List[ArchiveMember]:
        assert isinstance(archive, zipfile.ZipFile)  # please mypy
        return archive.infolist()  # type: ignore

    @staticmethod
    def _get_member_name(member: ArchiveMember) -> str:
        assert isinstance(member, zipfile.ZipInfo)  # please mypy
        return member.filename
