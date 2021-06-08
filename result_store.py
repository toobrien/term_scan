class result_store:

    def __init__(self):
        self.result_set = {}

    def add_result(self, result):
        self.result_set[result.get_id()] = result

    def export(self):
        return {}