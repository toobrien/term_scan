from json import loads
from scan import scan
from sqlite3 import connect


with open("./config.json") as fd:
    config = loads(fd.read())

def batch_execute(batch):
    connection = connect(config["db_path"])
    cursor = connection.cursor()
    results = []

    for scan_def in batch:
        s = scan(scan_def, cursor)
        rs = s.execute()
        # discard spread_set data, output match string only
        rs["results"] = [ r["match"] for r in rs["results"] ]
        results.append(rs)

    connection.close()

    return results

if __name__=="__main__":
    all_results = batch_execute(config["scans"])

    for result_set in all_results:
        print(result_set["name"], result_set["contract"])
        for result in result_set["results"]:
            print(result)