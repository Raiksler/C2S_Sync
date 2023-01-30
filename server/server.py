from flask import Flask, request, Response, jsonify
import hashlib
import json
import psycopg2


app = Flask(__name__)


class Db_manager:         #Класс управления базой данных
    def __init__(self):
        self.connection = psycopg2.connect(user='postgres', password='pgadminpass', host='localhost', database='text_syncro')
        self.cursor = self.connection.cursor()

    def add_change(self, changes):      #Добабвление новых изменений в систему контроля версий.
        changes["changes"] = changes["changes"].replace("\n", "\\n")
        self.cursor.execute("INSERT INTO changelog (base_hash, new_line, changes) VALUES ({hash}, {is_new_line}, E'{text}');".format(hash = changes["base_hash"], is_new_line = changes["new_line"], text = changes["changes"]))
        self.connection.commit()
    
    def get_last_change(self):          #Получение последнего изменения из системы контроля версий.
        self.cursor.execute("SELECT changes, new_line FROM changelog ORDER BY id DESC LIMIT 1;")
        return self.cursor.fetchall()[0]

    def get_updates(self, base_hash):   #Получение списка изменений, начиная с заданного хэша.
        self.cursor.execute("WITH start_from_id AS (SELECT id FROM changelog WHERE base_hash = '{hash}') SELECT changes, new_line FROM changelog WHERE id >= (SELECT id FROM start_from_id ORDER BY id LIMIT 1);".format(hash = base_hash))
        return self.cursor.fetchall()

@app.route("/ping")                     #Пинг сервера.
def ping():
        return Response(status=200)


@app.route("/check_sum")
def check_sum():                        #Запрос хэш суммы текущего образца файла на сервере.
    with open("data.txt", "r") as data:
        data_lines = data.readlines()
        joined_lines = "".join(data_lines).encode("UTF-8")
        data_hash = int(hashlib.md5(joined_lines).hexdigest(), 16)
        return str(data_hash)


@app.route("/send_changes", methods=["POST"])
def get_changes():                      #Внесение новых изменений в файл на сервере с занесением новых записей в систему контроля версий.
    changes = json.loads(request.data.decode("UTF-8"))
    Db_manager().add_change(changes=changes)
    last_change = Db_manager().get_last_change()
    apply_changes(last_change)
    return Response(status=200)


@app.route("/request_update", methods=["GET"])
def request_updates():                  #Запрос данных из системы контроля версий.
    base_hash = request.args.get("base_hash")
    updates = Db_manager().get_updates(base_hash)
    return jsonify(updates)


def apply_changes(change):
    if change[1] == True:               #Локальная функция. Применение изменения к образцу файла на сервере.
        with open ("data.txt", "r") as data:
            data_lines = data.readlines()
    else:
        with open ("data.txt", "r") as data:
            data_lines = data.readlines()
            data_lines[-1] = data_lines[-1].rstrip("\n")
    data_lines.extend([change[0]])
    with open ("data.txt", "w") as data:
        data.write(''.join(data_lines))


if __name__ == "__main__":
    app.run()