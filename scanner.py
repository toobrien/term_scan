from json import loads, dumps
from scan import scan
from result_store import result_store
from data.data_store import data_store
from sqlite3 import connect


with open("./config.json") as fd:
    config = loads(fd.read())
        

def batch_execute(batch):
    results = result_store()

    connection = connect(config["db_path"])
    cursor = connection.cursor()

    #for scan_def in batch:
    for i in range(0,1):
        s = scan(batch[0], cursor)
        r = s.execute()
        results.add_result(r)

    connection.close()

    return results.export()

if __name__=="__main__":
    batch_execute(config["default_scan_batch"])