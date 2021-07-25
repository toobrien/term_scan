from json import loads
from scan import scan
from sqlite3 import connect


with open("./config.json") as fd:
    config = loads(fd.read())

def batch_execute(batch):
    connection = connect(config["db_path"])
    cursor = connection.cursor()
    all_results = []

    for scan_def in batch:
        s = scan(scan_def, cursor)
        rs = s.execute()
        all_results.append(rs)

    connection.close()

    return all_results

if __name__=="__main__":
    all_results = batch_execute(config["default_scan_batch"])

    for result_set in all_results:
        print(result_set["name"], result_set["contract"])
        for result in result_set["results"]:
            print(result)