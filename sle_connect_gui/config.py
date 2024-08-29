from qfluentwidgets import (QConfig, OptionsConfigItem,
                            OptionsValidator, __version__)

YEAR = 2024
AUTHOR = "Chen YunBo"
VERSION = "1.0.1"
FEEDBACK_URL = "https://github.com/chenyunbovo/nearlink_sle_connect_bs21/issues"

class Config(QConfig):
    com_list = []
    for i in range(100):
        com_list.append(i)

    com = OptionsConfigItem("MainWindow", "com", "0", OptionsValidator(com_list), restart=True)


cfg = Config()