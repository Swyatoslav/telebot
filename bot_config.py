import configparser
import os


class ConfigManager:

    @staticmethod
    def create_config(path):
        """Метод создает файл конфига
        :param path - путь до будущего конфига
        """
        if not os.path.exists(path):
            config = configparser.ConfigParser()
            config.add_section("general")
            config.set("general", "token", "")
            config.set("general", "db", "")
            config.set("general", "db_user_name", "postgres")
            config.set("general", "db_user_password", "")
            config.set("general", 'settings_path', 'C:\\Projects')
            config.set("general", 'exec_time', '0.5')

            with open(path, "w") as config_file:
                config.write(config_file)

        else:
            config = configparser.ConfigParser()
            config.read(path)

        return config
