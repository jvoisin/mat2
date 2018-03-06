class AbstractParser(object):
    def __init__(self, filename: str):
        self.filename = filename
        self.meta_list = set()

    def get_meta(self):
        raise NotImplementedError

    def remove_all(self):
        raise NotImplementedError
