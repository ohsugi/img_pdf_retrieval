import configparser
import pathlib
import glob
import os

class ConfigReader:
    config = configparser.ConfigParser()
    config_file_name = "./config.ini"

    cache_path = ""
    feature_path = ""
    feature_file_ext = ""
    uploaded_path = ""
    pdf_image_path = ""
    face_included_images_path = ""

    face_filtering = False

    indexing_folder_list = []
    type_list = []

    last_checked = ""

    def get_data_path(self, path):
        data_path = pathlib.Path(path)
        if not data_path.exists():
            if not data_path.parent.exists():
                self.get_data_path(data_path.parent)
            data_path.mkdir(exist_ok=True)
        return path

    def load_config(self, filename):
        config = self.config
        config.read(filename)

        self.cache_path = self.get_data_path(config.get("DATA_PATH", "cache_path"))
        self.feature_path = config.get("DATA_PATH", "feature_path")
        self.feature_file_ext = config.get("DATA_PATH", "feature_file_ext")
        self.uploaded_path = config.get("DATA_PATH", "uploaded_path")
        self.pdf_image_path = config.get("DATA_PATH", "pdf_image_path")
        self.face_included_images_path = config.get("DATA_PATH", "face_included_images_path")

        self.face_filtering = (config.get("CONDITIONS", "face_filtering") == "True")

        self.last_checked = config.get("USER_STATUS", "last_checked")

        i = 0
        self.indexing_folder_list = []
        try:
            while config.get("INDEXING_FOLDERS", str(i)):
                value = config.get("INDEXING_FOLDERS", str(i))
                self.indexing_folder_list.append(value)
                i += 1
        except configparser.NoOptionError:
            pass

        i = 0
        self.type_list = []
        try:
            while config.get("TYPES", str(i)):
                value = config.get("TYPES", str(i))
                self.type_list.append(value)
                i += 1
        except configparser.NoOptionError:
            pass
    
    def get_file_list(self, folder_list):
        file_list = []
        for folder in folder_list:
            files = glob.glob(folder + "**", recursive=True)
            for file in files:
                if os.path.isfile(file) and self.get_file_ext(file) in self.type_list:
                    file_list.append(file)
        return file_list

    def get_indexing_file_list(self):
        return self.get_file_list(self.indexing_folder_list)

    def get_file_ext(self, file):
        return pathlib.Path(file).suffix.lower()

    def exists_query_data_file(self):
        return os.path.isfile(self.query_data_file_path)

    def is_pdf_file(self, file):
        return self.get_file_ext(file) == ".pdf"

    def escape_file_name(self, file_name):
        (wo_ext, ext) = os.path.splitext(file_name)
        return wo_ext.replace('.', '').replace(':', '').replace('¥¥', '_').replace('\\', '_').replace('/', '_') + ext

    def serialize(self):
        config = self.config
        config["USER_STATUS"]["last_checked"] = self.last_checked
        with pathlib.Path(self.config_file_name).open(mode='w') as configfile:
            config.write(configfile)

    def __init__(self, filename=""):
        if filename != "":
            self.config_file_name = filename
        self.load_config(self.config_file_name)

    def __del__(self):
        pass
        # self.serialize()
