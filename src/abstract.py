class AbstractParser(object):
    meta_list = set()
    mimetypes = set()

    def __init__(self, filename: str):
        self.filename = filename
        self.output_filename = filename + '.cleaned'

    def get_meta(self):
        raise NotImplementedError

    def remove_all(self):
        raise NotImplementedError
