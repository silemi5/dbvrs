import os
import json

class Config:
    def __init__(self,config_path=False,bk_loc=False):
        if(not config_path):
            # Read from current
            config_path = os.environ['APPDATA'] + "\\DBVRS"

        # Configuration not found
        if not os.path.exists(config_path + "\\dbvrs.json"):
            with open(config_path + "\\dbvrs.json", "w") as json_file:
                json.dump(self.getDefaultConfiguration(bk_loc), json_file)

        config_file = open(config_path + "\\dbvrs.json")

        self.config = json.load(config_file)

    def getBackupLocation(self):
        return self.config['backup_location']

    def getFoldersToBackup(self):
        return self.config['folders_to_backup']

    def getDefaultConfiguration(self, backup_location):
        return {
            "backup_location":backup_location,
            "folders_to_backup":[]
        }

    def updateConfiguration(self, backup_location=False, folders_to_backup=False):
        config_path = os.environ['APPDATA'] + "\\DBVRS"

        # Backup location update
        if(backup_location != False):
            self.config['backup_location'] = backup_location

        # Folders to backup. Must be array.
        if(folders_to_backup != False):
            self.config['folders_to_backup'] = folders_to_backup

        with open(config_path + "\\dbvrs.json", "w") as json_file:
                json.dump(self.config, json_file)