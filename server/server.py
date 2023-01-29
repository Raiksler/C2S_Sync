from flask import Flask, request, Response
import hashlib
import json
import psycopg2


app = Flask(__name__)


class Db_manager:
    def __init__(self):
        self.connection = psycopg2.connect(user='postgres', password='pgadminpass', host='localhost', database='text_syncro')
        self.cursor = self.connection.cursor()

    def add_change(self, changes):
        changes["changes"] = changes["changes"].replace("\n", "\\n")
        self.cursor.execute("INSERT INTO changelog (base_hash, new_line, changes) VALUES ({hash}, {is_new_line}, E'{text}');".format(hash = changes["base_hash"], is_new_line = changes["new_line"], text = changes["changes"]))
        self.connection.commit()
    
    def get_last_change(self):
        self.cursor.execute("SELECT changes, new_line FROM changelog ORDER BY id DESC LIMIT 1;")
        return self.cursor.fetchall()[0]


@app.route("/check_sum")
def check_sum():
    with open("data.txt", "r") as data:
        data_lines = data.readlines()
        joined_lines = "".join(data_lines).encode("UTF-8")
        data_hash = int(hashlib.md5(joined_lines).hexdigest(), 16)
        return str(data_hash)


@app.route("/send_changes", methods=["POST"])
def get_changes():
    changes = json.loads(request.data.decode("UTF-8"))
    print(changes)
    Db_manager().add_change(changes=changes)
    last_change = Db_manager().get_last_change()
    print(last_change)
    apply_changes(last_change)
    return Response(status=200)

def apply_changes(change):
    if change[1] == True:
        with open ("data.txt", "r") as data:
            data_lines = data.readlines()
    else:
        with open ("data.txt", "r") as data:
            data_lines = data.readlines()[:-1]
    data_lines.extend([change[0]])
    with open ("data.txt", "w") as data:
        print(data_lines)
        data.write(''.join(data_lines))


if __name__ == "__main__":
    app.run()