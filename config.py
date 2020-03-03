import os
import json

class Config:
    def __init__(self,config_path=False,bk_loc=False):
        if not os.path.exists(config_path + "\\dbvrs.json"):
            with open(config_path + "\\dbvrs.json", "w") as json_file:
                json.dump(self.setDefaultConfiguration(bk_loc), json_file)

        config_file = open(config_path + "\\dbvrs.json")

        self.config = json.load(config_file)

    def getBackupLocation(self):
        return self.config['backup_location']

    def getFoldersToBackup(self):
        return self.config['folders_to_backup']

    def setDefaultConfiguration(self, backup_location):
        return {
            "backup_location":backup_location,
            "folders_to_backup":[]
        }