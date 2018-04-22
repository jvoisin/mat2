import os
import re
import shutil
import tempfile
import datetime
import zipfile

from . import abstract, parser_factory



class TorrentParser(abstract.AbstractParser):
    mimetypes = {'application/x-bittorrent', }
    whitelist = {b'announce', b'announce-list', b'info'}

    def __init__(self, filename):
        super().__init__(filename)
        self.__decode_func = {
                    ord('l'): self.__decode_list,
                    ord('d'): self.__decode_dict,
                    ord('i'): self.__decode_int
            }
        for i in range(0, 10):
            self.__decode_func[ord(str(i))] = self.__decode_string

        self.__encode_func = {
                int: self.__encode_int,
                bytes: self.__encode_string,
                list: self.__encode_list,
                dict: self.__encode_dict,
        }


    def get_meta(self):
        metadata = {}
        with open(self.filename, 'rb') as f:
            d = self.__bdecode(f.read())
        for k,v in d.items():
            if k not in self.whitelist:
                metadata[k.decode('utf-8')] = v
        return metadata


    def remove_all(self):
        cleaned = dict()
        with open(self.filename, 'rb') as f:
            d = self.__bdecode(f.read())
        for k,v in d.items():
            if k in self.whitelist:
                cleaned[k] = v
        with open(self.output_filename, 'wb') as f:
            f.write(self.__bencode(cleaned))
        return True

    def __decode_int(self, s):
        s = s[1:]
        next_idx = s.index(b'e')
        if s.startswith(b'-0'):
            raise ValueError  # negative zero doesn't exist
        if s.startswith(b'0') and next_idx != 1:
            raise ValueError  # no leading zero except for zero itself
        return int(s[:next_idx]), s[next_idx+1:]

    def __decode_string(self, s):
        end = s.index(b':')
        str_len = int(s[:end])
        if s[0] == b'0' and end != 1:
            raise ValueError
        s = s[1:]  # skip terminal `:`
        return s[end:end+str_len], s[end+str_len:]

    def __decode_list(self, s):
        r = list()
        s = s[1:]  # skip leading `l`
        while s[0] != ord('e'):
            v, s = self.__decode_func[s[0]](s)
            r.append(v)
        return r, s[1:]

    def __decode_dict(self, s):
        r = dict()
        s = s[1:]
        while s[0] != ord(b'e'):
            k, s = self.__decode_string(s)
            r[k], s = self.__decode_func[s[0]](s)
        return r, s[1:]

    def __bdecode(self, s):
        try:
            r, l = self.__decode_func[s[0]](s)
        except (IndexError, KeyError, ValueError) as e:
            print("not a valid bencoded string: %s" % e)
            return None
        if l != b'':
            print("invalid bencoded value (data after valid prefix)")
            return None
        return r

    @staticmethod
    def __encode_int(x):
        return b'i' + bytes(str(x), 'utf-8') + b'e'

    @staticmethod
    def __encode_string(x:str):
        return bytes((str(len(x))), 'utf-8') + b':' + x

    def __encode_list(self, x):
        ret = b''
        for i in x:
            ret += self.__encode_func[type(i)](i)
        return b'l' + ret + b'e'

    def __encode_dict(self, x):
        ret = b''
        for k, v in sorted(x.items()):
            ret += self.__encode_func[type(k)](k)
            ret += self.__encode_func[type(v)](v)
        return b'd' + ret + b'e'

    def __bencode(self, x):
        return self.__encode_func[type(x)](x)


