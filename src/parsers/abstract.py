class AbstractParser(object):
    def __init__(self, filename: str):
        self.filename = filename
        self.output_filename = filename + '.cleaned'
        self.meta_list = set()
        self.mimetypes = set()

    def get_meta(self):
        raise NotImplementedError

    def remove_all(self):
        raise NotImplementedError
