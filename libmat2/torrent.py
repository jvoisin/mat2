import logging
from typing import Union, Tuple, Dict

from . import abstract


class TorrentParser(abstract.AbstractParser):
    mimetypes = {'application/x-bittorrent', }
    allowlist = {b'announce', b'announce-list', b'info'}

    def __init__(self, filename):
        super().__init__(filename)
        with open(self.filename, 'rb') as f:
            self.dict_repr = _BencodeHandler().bdecode(f.read())
        if self.dict_repr is None:
            raise ValueError

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        metadata = {}
        for key, value in self.dict_repr.items():
            if key not in self.allowlist:
                metadata[key.decode('utf-8')] = value
        return metadata

    def remove_all(self) -> bool:
        cleaned = dict()
        for key, value in self.dict_repr.items():
            if key in self.allowlist:
                cleaned[key] = value
        with open(self.output_filename, 'wb') as f:
            f.write(_BencodeHandler().bencode(cleaned))
        self.dict_repr = cleaned  # since we're stateful
        return True


class _BencodeHandler():
    """
    Since bencode isn't that hard to parse,
    MAT2 comes with its own parser, based on the spec
    https://wiki.theory.org/index.php/BitTorrentSpecification#Bencoding
    """
    def __init__(self):
        self.__decode_func = {
            ord('d'): self.__decode_dict,
            ord('i'): self.__decode_int,
            ord('l'): self.__decode_list,
        }
        for i in range(0, 10):
            self.__decode_func[ord(str(i))] = self.__decode_string

        self.__encode_func = {
            bytes: self.__encode_string,
            dict: self.__encode_dict,
            int: self.__encode_int,
            list: self.__encode_list,
        }

    @staticmethod
    def __decode_int(s: bytes) -> Tuple[int, bytes]:
        s = s[1:]
        next_idx = s.index(b'e')
        if s.startswith(b'-0'):
            raise ValueError  # negative zero doesn't exist
        elif s.startswith(b'0') and next_idx != 1:
            raise ValueError  # no leading zero except for zero itself
        return int(s[:next_idx]), s[next_idx+1:]

    @staticmethod
    def __decode_string(s: bytes) -> Tuple[bytes, bytes]:
        colon = s.index(b':')
        # FIXME Python3 is broken here, the call to `ord` shouldn't be needed,
        # but apparently it is. This is utterly idiotic.
        if (s[0] == ord('0') or s[0] == '0') and colon != 1:
            raise ValueError
        str_len = int(s[:colon])
        s = s[1:]
        return s[colon:colon+str_len], s[colon+str_len:]

    def __decode_list(self, s: bytes) -> Tuple[list, bytes]:
        ret = list()
        s = s[1:]  # skip leading `l`
        while s[0] != ord('e'):
            value, s = self.__decode_func[s[0]](s)
            ret.append(value)
        return ret, s[1:]

    def __decode_dict(self, s: bytes) -> Tuple[dict, bytes]:
        ret = dict()
        s = s[1:]  # skip leading `d`
        while s[0] != ord(b'e'):
            key, s = self.__decode_string(s)
            ret[key], s = self.__decode_func[s[0]](s)
        return ret, s[1:]

    @staticmethod
    def __encode_int(x: bytes) -> bytes:
        return b'i' + bytes(str(x), 'utf-8') + b'e'

    @staticmethod
    def __encode_string(x: bytes) -> bytes:
        return bytes((str(len(x))), 'utf-8') + b':' + x

    def __encode_list(self, x: str) -> bytes:
        ret = b''
        for i in x:
            ret += self.__encode_func[type(i)](i)
        return b'l' + ret + b'e'

    def __encode_dict(self, x: dict) -> bytes:
        ret = b''
        for key, value in sorted(x.items()):
            ret += self.__encode_func[type(key)](key)
            ret += self.__encode_func[type(value)](value)
        return b'd' + ret + b'e'

    def bencode(self, s: Union[dict, list, bytes, int]) -> bytes:
        return self.__encode_func[type(s)](s)

    def bdecode(self, s: bytes) -> Union[dict, None]:
        try:
            ret, trail = self.__decode_func[s[0]](s)
        except (IndexError, KeyError, ValueError) as e:
            logging.warning("Not a valid bencoded string: %s", e)
            return None
        if trail != b'':
            logging.warning("Invalid bencoded value (data after valid prefix)")
            return None
        return ret
