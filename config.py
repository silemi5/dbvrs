import os
import json

class Config:
    
    NO_CONFIG = False

    def __init__(self,config_path=False,bk_loc=False):
        if(not config_path):
            # Read from current
            config_path = os.environ['APPDATA'] + "\\DBVRS"

        self.checkConfigurationIfExists()

        # Configuration exists
        if not self.NO_CONFIG:
            config_file = open(config_path + "\\dbvrs.json")

            self.config = json.load(config_file)

    def getBackupLocation(self):
        return self.config['backup_location']

    def getFoldersToBackup(self):
        return self.config['folders_to_backup']

    def getScheduledTime(self):
        return self.config['scheduled_backup_time']

    def getScheduledWeekDay(self):
        return self.config['scheduled_backup_weekday']

    def getScheduledBackupMode(self):
        return self.config['scheduled_backup_mode']

    def getLastBackup(self):
        return self.config['last_backup']
    
    def getBackupDay(self):
        return self.config['scheduled_backup_day']

    def getNextBackupMonth(self):
        return self.config['next_scheduled_backup_month']

    def updateLastBackup(self, timestamp):
        config_path = os.environ['APPDATA'] + "\\DBVRS"

        config_file = open(config_path + "\\dbvrs.json")
        
        self.config = json.load(config_file)

        self.config['last_backup'] = timestamp

        with open(config_path + "\\dbvrs.json", "w") as json_file:
            json.dump(self.config, json_file)

    def checkConfigurationIfExists(self):
        config_path = os.environ['APPDATA'] + "\\DBVRS"

        # Creates dbvrs config folder if not exists.
        if not os.path.exists(config_path):
            # os.makedirs(config_path)
            self.NO_CONFIG = True

        # Configuration not found
        if not os.path.exists(config_path + "\\dbvrs.json"):
            self.NO_CONFIG = True
            # with open(config_path + "\\dbvrs.json", "w") as json_file:
            #     json.dump(self.getDefaultConfiguration(bk_loc), json_file)
        
        return self.NO_CONFIG

    def getDefaultConfiguration(self, backup_location):
        return {
            "backup_location":backup_location,
            "folders_to_backup":[],
            "scheduled_backup_time": "",
            "scheduled_backup_day": ""
        }

    def updateConfiguration(self, backup_location=False, folders_to_backup=False):
        config_path = os.environ['APPDATA'] + "\\DBVRS"

        # Creates dbvrs config folder if not exists.
        if not os.path.exists(config_path):
            os.makedirs(config_path)

        # Creates a default config file if not exists.
        if not os.path.exists(config_path + "\\dbvrs.json"):
            with open(config_path + "\\dbvrs.json", "w") as json_file:
                json.dump(self.getDefaultConfiguration(backup_location), json_file)
        
        config_file = open(config_path + "\\dbvrs.json")
        
        self.config = json.load(config_file)

        # Backup location update
        if(backup_location != False):
            self.config['backup_location'] = backup_location

        # Folders to backup. Must be array.
        if(folders_to_backup != False):
            self.config['folders_to_backup'] = folders_to_backup

        with open(config_path + "\\dbvrs.json", "w") as json_file:
                json.dump(self.config, json_file)