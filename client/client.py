import pyinotify
import time
import filecmp
import difflib
import pathlib
import hashlib
import requests

class EventHandler(pyinotify.ProcessEvent):

    def process_IN_MODIFY(self, event):
        time.sleep(0.3)
        global modify_mode
        modify_mode = True                                                        #Останавливаем мониторинг событий, чтобы избежать лишних срабатываний во время изменений файла.
        print("Detected file saving, checking...")
        if validate_changes() == True:                                            #Проводим валидацию изменений на клиенте.
            backup_hash = get_backup_hash()                                       #Получаем хэш бэкап файла, будем сравнивать его с хэшэм файла на сервере.
            print("Comparing local file with server...")
            same_cash = compare_hash(backup_hash)
            if same_cash == True:
                print("Local and server files are same. Proceed to send update to server...")
                new_data = get_difference()                                       #Получаем новые данные.
                if new_data != None:                                              #Если в локальном файле есть изменения - отправляем их на сервер.
                    new_data["base_hash"] = backup_hash                           #!!! Добавляем к отправляемым данным хэш сумму файла, на которой базируются изменения. Это понадобится для работы системы контроля верссий на сервере.
                    update_on_server = requests.post("http://127.0.0.1:5000/send_changes", json = new_data)
                    if update_on_server.status_code == 200:                       #Данные улетели. Если все ок, обновляем бэкап файл до текущих изменений.
                        print("Update sent!")
                        update_backup()
                        print()
            else:
                print("Local and server files are different. Proceed to updating local file...")
                new_data = get_difference()                                       #Получаем разницу между бэкапом и редактируемым файлом.
                return_to_backup()
                updates = requests.get("http://127.0.0.1:5000/request_update?base_hash={hash}".format(hash=backup_hash)).json()
                apply_updates(updates)
                update_backup()
                backup_hash = get_backup_hash()                                   #Получаем хэш бэкап файла, будем сравнивать его с хэшэм файла на сервере.
                if new_data != None:                                              #Если в локальном файле есть изменения - отправляем их на сервер.
                    new_data["base_hash"] = backup_hash                           #!!! Добавляем к отправляемым данным хэш сумму файла, на которой базируются изменения. Это понадобится для работы системы контроля верссий на сервере.
                    update_on_server = requests.post("http://127.0.0.1:5000/send_changes", json = new_data)
                    if update_on_server.status_code == 200:                       #Данные улетели. Если все ок, обновляем бэкап файл до текущих изменений.
                        updates = requests.get("http://127.0.0.1:5000/request_update?base_hash={hash}".format(hash=backup_hash)).json()
                        apply_updates(updates)
                        update_backup()                        
                        print()

        modify_mode = False                                                       #Снова запускаем мониторинг событий.
        notifier.loop(callback=stop_monitoring_to_modify)


def apply_updates(updates):                             #Функция применяет апдейты, полученные от системы контроля версий на сервере.
    for item in updates:
        if item[1] == True:
            with open ("data.txt", "r") as data:
                data_lines = data.readlines()
        else:
            with open ("data.txt", "r") as data:
                data_lines = data.readlines()
                data_lines[-1] = data_lines[-1].rstrip("\n")
        data_lines.extend([item[0]])
        with open ("data.txt", "w") as data:
            data.write(''.join(data_lines))
    print("data.txt has been updated to actual version!")


def compare_hash(local_hash):                                                   #Функция сравнивает хэш сумму локального и удаленного файлов.
    server_hash = requests.get("http://127.0.0.1:5000/check_sum").text
    return local_hash == server_hash


def get_backup_hash():                                                         #Функция получает хэш сумму бэкап файла.
    with open("data_backup.txt", "r") as backup:
        backup_lines = backup.readlines()
        joined_lines = "".join(backup_lines).encode("UTF-8")
        backup_hash = int(hashlib.md5(joined_lines).hexdigest(), 16)
        return str(backup_hash)


def get_difference():                                                           #Функция возвращает словарь с двумя ключами. Changes - новая строка (str), и new_line (boolean) указтель на то, нужно ли добавлять changes овой строкой или присоединять к имеющейся.
    with open("data.txt","r") as data, open("data_backup.txt", "r") as backup:
        data_lines = data.readlines()
        backup_lines = backup.readlines()
        data_path = pathlib.Path("data.txt")
        backup_path = pathlib.Path("data_backup.txt")
        if filecmp.cmp(data_path, backup_path) == True:
            print("Changes not detected")
            print()
            return None
        else:
            difference = list(difflib.unified_diff(backup_lines, data_lines, "data_backup.txt", "data.txt", n=0))[3:]
            changes = {"changes" : "", "new_line" : True}
            i = 0
            while i < len(difference):
                if i == 0 and difference[i][0] == "-":
                    changes["new_line"] = False
                    changes["changes"] = "".join([changes["changes"], difference[1][len(difference[0])-1:]])
                    i += 2
                else:
                    changes["changes"] = "".join([changes["changes"], difference[i][1:]])
                    i += 1
            return changes
                
                
def compare_lines(data, backup):                                                  #Функция проверяет, что новые данные добавлены только в конец файла.

    def stripper(lines):
        lines_stripped = list()
        for line in lines:
            lines_stripped.append(line.strip('\n'))
        return lines_stripped
            
    data_lines = stripper(data.readlines())
    backup_lines = stripper(backup.readlines())
    i = 0
    while i < len(backup_lines):
        if i == len(backup_lines) -1:
            if backup_lines[i] not in data_lines[i][0: len(backup_lines[i])]:
                return False
        elif data_lines[i] != backup_lines[i]:
            return False
        i += 1
    return True


def count_lines(file):                                                          #Функция считает строки в
    lines = 0
    for line in file:
        lines += 1
    file.seek(0)       #Возврат к началу файла
    return lines


def validate_changes():                                               #Функция проводит локальную валидацию изменений. Проверяет, что использованы только допустимые сиволы, а изменения внесены только в конец файла.
    with open("data.txt","r") as data, open("data_backup.txt", "r") as backup:
        data_lines = count_lines(data)
        backup_lines = count_lines(backup)
        if data_lines < backup_lines:                                 #Если количество строк относительно локального бэкапа уменьшилось, откатываем изменения.
            print("Error: data.txt lenght decreased!")
            return_to_backup()
            return False
        if compare_lines(data, backup) == False:
            print("Error: data added not in the end of the file!")
            return_to_backup()
            return False
        data.seek(0)
        for line in data.readlines():
            if line.isascii() != True:
                print("Error: invalid characters added!")
                return_to_backup()
                return False
    return True


def return_to_backup():                                            #Функция возвращает data.txt к бэкапу.
    print("Returning to backup...")
    with open("data.txt","w") as data, open("data_backup.txt", "r") as backup:
        for line in backup:                          
            data.write(line)
        print("data.txt returned to backup\n")


def update_backup():                                              #Функция обновляет бэкап данными из data.txt
    with open("data.txt", 'r') as data, open ("data_backup.txt", "w") as backup:
        data_lines = data.readlines()
        backup.write("".join(data_lines))
        print("Backup updated!")

def stop_monitoring_to_modify(notifier):                                    #Колбек цикла мониторинга изменений файла. Отключает мониторинг на время изменения файлов.
    global modify_mode
    return modify_mode           


if __name__ == "__main__":

    if requests.get('http://127.0.0.1:5000/ping').status_code == 200:
        print("All clear! Server ready to recieve data...\n")
    else:
        print("Some problems with connection to server. It may be good idea to restart server or check connection settings.")
        
    update_backup()                                                          #Создаем бэкап данных на клиенте, в дальнейшем он понадобится для реализации запрета на удаление локального текста и прочих ограничений.
    modify_mode = False
    watch_manager = pyinotify.WatchManager()                                #Создаем инстанс менеджера, через который будем мониторить изменения файла.
    target_event = pyinotify.IN_MODIFY                                      #Выбираем ивент, который будем мониторить.
    handler = EventHandler()
    notifier = pyinotify.Notifier(watch_manager, handler, threshold=1)                   #Задаем параметры проверки на изменения.
    work_dir = watch_manager.add_watch('.', target_event, rec=True)         #Задаем директорию и событие, которое будем ловить.
    notifier.loop(callback=stop_monitoring_to_modify)                       #Основной цикл мониторинга. Колбэк функция останавливает выполнение.


