import pyinotify
import time
import filecmp
import difflib
import pathlib

class EventHandler(pyinotify.ProcessEvent):

    def process_IN_MODIFY(self, event):
        time.sleep(0.3)
        global modify_mode
        modify_mode = True                                                        #Останавливаем мониторинг событий, чтобы избежать лишних срабатываний во время изменений файла.
        print("Detected file saving, checking...".format(path=event.path))
        if validate_changes() == True:                                            #Проводим валидацию изменений на клиенте.
            new_data = get_difference()                                           #Получаем новые данные.
        modify_mode = False                                                       #Снова запускаем мониторинг событий.
        notifier.loop(callback=stop_monitoring_to_modify)


def get_difference():
    with open("data.txt","r") as data, open("data_backup.txt", "r") as backup:
        data_lines = data.readlines()
        backup_lines = backup.readlines()
        data_path = pathlib.Path("data.txt")
        backup_path = pathlib.Path("data_backup.txt")
        if filecmp.cmp(data_path, backup_path) == True:
            print("Changes not detected")
            return None
        else:
            difference = difflib.unified_diff(backup_lines, data_lines, "data_backup.txt", "data.txt")
            print(list(difference))
                
                
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


def count_lines(file):
    lines = 0
    for line in file:
        lines += 1
    file.seek(0)       #Возврат к началу файла
    return lines


def validate_changes():
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
    return True
            

def local_backup():
    with open("data.txt","r") as data, open("data_backup.txt", "w") as backup:
        for line in data:                          
            backup.write(line)


def return_to_backup():
    print("Returning to backup...")
    with open("data.txt","w") as data, open("data_backup.txt", "r") as backup:
        for line in backup:                          
            data.write(line)
        print("data.txt returned to backup")


def stop_monitoring_to_modify(notifier):                                    #Колбек цикла мониторинга изменений файла. Отключает мониторинг на время изменения файлов.
    global modify_mode
    return modify_mode           


if __name__ == "__main__":
    local_backup()                                                          #Создаем бэкап данных на клиенте, в дальнейшем он понадобится для реализации запрета на удаление текста.
    modify_mode = False
    watch_manager = pyinotify.WatchManager()                                #Создаем инстанс менеджера, через который будем мониторить изменения файла.
    target_event = pyinotify.IN_MODIFY                                      #Выбираем ивент, который будем мониторить.
    handler = EventHandler()
    notifier = pyinotify.Notifier(watch_manager, handler, threshold=1)                   #Задаем параметры проверки на изменения.
    work_dir = watch_manager.add_watch('.', target_event, rec=True)         #Задаем директорию и событие, которое будем ловить.
    notifier.loop(callback=stop_monitoring_to_modify)                       #Основной цикл мониторинга. Колбэк функция останавливает выполнение.


