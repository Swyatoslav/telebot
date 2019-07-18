import subprocess
import threading
import os


# todo Тест на проверку доступности БД
# todo Тест на проверку работы с пользователем без фамилии
# todo Тест на проверку вытаскивания погоды
# todo Тест на проверку приветствия
# todo Тест на проверку прощания
# todo Тест на проверку общения

def run_receiver():
    os.system("python receiver_bot.py")


def run_sender():
    os.system("python sender_bot.py")


# путь до папки с bot_tests добавлен в переменную Path
if __name__ == "__main__":
    t = threading.Thread(target=run_sender)
    t.daemon = True
    t.start()

    run_sender()