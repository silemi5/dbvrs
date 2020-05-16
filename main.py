import os
from datetime import datetime
import hashlib
import zipfile
import fnmatch
import string
import tempfile
import time
import shutil
import sys
import json
from config import Config

# Array of files
files = []

# Creates a log file.
log = None

# Print log to console?
PRINT_LOG = False

start_process_time = 0

# Variables that can be edited
# TODO: Prevent users from backing-up system files.
DIRECTORY_TO_BACKUP = ''
DIRECTORY_TO_STORE_BACKUP = 'D:/backup/'
filetypes_to_include = ['*.prn']

# Variables used to show progress in the GUI.
backupFileCount = 0
backupFilesTotal = 0

validateFileCount = 0
validateFilesTotal = 0
validationStats = []
filesMismatched = ""
filesUnlisted = ""

# Variable to report to the GUI if something's amiss.
status = 0
statusMessage = ""

def resetVariables():
    global backupFileCount, backupFilesTotal
    global validateFileCount, validateFilesTotal, validationStats, filesMismatched, filesUnlisted
    global today, status, statusMessage
    global start_process_time
    global files

    backupFileCount = 0
    backupFilesTotal = 0
    validateFileCount = 0
    validateFilesTotal = 0
    validationStats = []

    start_process_time = 0
    files = []
    filesMismatched = ""
    filesUnlisted = ""

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def writeLog(message):
    global log
    # log = open("dbvrs_{}.log".format(today), "w+")
    log.write("[{}]: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))
    if(PRINT_LOG):
        print("[{}]: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))
    # log.close()

def startLog():
    global log, today

    # Gets current date and time upon backup execution.
    today = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    log = open("dbvrs_{}.log".format(today), "w+")

def endLog():
    log.close()

def disk_usage(path="/"):
    total, used, free = shutil.disk_usage(path)

    return { "total": total, "used": used, "free": free }

    # print("Total: %d GiB" % (total // (2**30)))
    # print("Used: %d GiB" % (used // (2**30)))
    # print("Free: %d GiB" % (free // (2**30)))

def backup(to_backup=False, store_backup=False, mode=0):
    # Modes:
    #   Mode 0 - single folder backup
    #   Mode 1 - multiple folder backup
    resetVariables()
    startLog()

    start_process_time = time.process_time()
    global DIRECTORY_TO_BACKUP, DIRECTORY_TO_STORE_BACKUP, backupFilesTotal
    global status, statusMessage

    archive_size = 0

    writeLog("Backup started.")

    if(to_backup != False):
        DIRECTORY_TO_BACKUP = to_backup
    if(store_backup != False):
        DIRECTORY_TO_STORE_BACKUP = store_backup

    # No directory selected for backup.
    if(DIRECTORY_TO_BACKUP == ''):
        writeLog("Error! No directory to backup! Exiting.")
        status = 1001
        return 1001
    
    # No directory selected to store backup.
    if(DIRECTORY_TO_STORE_BACKUP == ''):
        writeLog("Error! No directory to store backup! Exiting.")
        status = 1002
        return 1002

    # print(DIRECTORY_TO_BACKUP[-1:])
    # Missing slash at the end of directory
    # if(DIRECTORY_TO_BACKUP[-1:] != '/' or DIRECTORY_TO_BACKUP[-1:] != '\\'):
    #     DIRECTORY_TO_BACKUP += "/"

    # print(DIRECTORY_TO_BACKUP[-1:])
    # print(DIRECTORY_TO_STORE_BACKUP)

    # Starts loop here
    # Checks if backup location exists. If not, creates one.
    if not os.path.exists(DIRECTORY_TO_STORE_BACKUP):
        os.makedirs(DIRECTORY_TO_STORE_BACKUP)

    # Transform single folder backup into array.
    if(mode == 0):
        DIRECTORY_TO_BACKUP = [ DIRECTORY_TO_BACKUP ]

    for directory in DIRECTORY_TO_BACKUP:
        # r=root, d=directories, f = files
        for r, d, f in os.walk(directory):
            for file in f:
                backupFilesTotal += 1
                path = os.path.join(r, file)
                file_size = os.path.getsize(path)
                archive_size += file_size
                files.append([path, md5(path), file_size])
        # Loop will end here

    writeLog("Time to finished generating hash value: {} seconds".format(time.process_time() - start_process_time))
    writeLog("Total files' size: {} bytes".format(archive_size))

    # Checks if backup location has enough space.
    # In addition to the archive size, at least 1GB must be free.
    current_disk = disk_usage()
    if(current_disk["free"] - archive_size < 1073741824):
        writeLog("Not enough free space on backup location!")
        writeLog("Reported free space: {} MB".format(((current_disk["free"] / 1024)/1024)))
        writeLog("Needed: {} MB".format(((archive_size / 1024)/1024)))
        status = 1003
        statusMessage = "Not enough space on backup location!"
        return 1003

    # Create a metadata
    metadata = open(".ics", "w+")
    metadata.write('{},"{}","{}",{}'.format(today, DIRECTORY_TO_BACKUP, DIRECTORY_TO_STORE_BACKUP, filetypes_to_include))

    # Creates a ZIP archive using LZMA compression
    zipName = ''.join([DIRECTORY_TO_STORE_BACKUP, today, '.zip'])
    zipObj = zipfile.ZipFile(zipName, 'w', zipfile.ZIP_LZMA)
    writeLog("Saving backup to: {}".format(zipName))

    # Gets process time for start time of storing.
    start_storing_time = time.process_time()

    # Starts storing files to archive
    for index, file in enumerate(files):
        global backupFileCount
        backupFileCount = index
        file_process_time_start = time.process_time()
        filename = file[0]
        zipObj.write(filename)
        metadata.write('\n"{}",{}'.format(file[0], file[1]))
        writeLog("Storing '{}' took {} seconds.".format(filename, time.process_time() - file_process_time_start))
    
    writeLog("The script took {} seconds to store the files.".format(time.process_time() - start_storing_time))

    metadata.close()
    zipObj.write('.ics')
    zipObj.close()
    
    # Remove metadata
    os.remove('.ics')

    writeLog("The script took {} seconds to finish backing up.".format(time.process_time() - start_process_time))
    writeLog("Backup completed!")

    endLog()
    
    return 0

def validate(mode=0, backupFile=False):
    resetVariables()
    startLog()
    
    writeLog("Started validation module")

    # Backup file not specified.
    if (not backupFile):
        writeLog("Backup file not provided!")
        return 1000
    
    # TODO: Arguements for validation
    # TODO: Check if provided file is NOT a backup archive.
    zipObj = None
    global statusMessage, status
    try:
        writeLog("Opening archive '{}'".format(backupFile))
        zipObj = zipfile.ZipFile(backupFile)
    except zipfile.BadZipFile:
        writeLog("Not a valid archive! Exiting!")
        statusMessage = "Not a valid archive!"
        status = 1000
        return [None,None,False]

    # TODO: Check free space for validation

    # Creates a temporary directory for validation
    tempDir = tempfile.mkdtemp()
    writeLog("Temporary directory: {}".format(tempDir))
    zipObj.extractall(path=tempDir)

    for r, d, f in os.walk(tempDir):
        for file in f:
            path = os.path.join(r, file)
            files.append([path.replace(tempDir + '\\', ""), md5(path)])

    # Gets metadata of the archive
    # TODO: Check if file is a valid backup archive

    validator = None
    try:
        validator = open(tempDir + '/.ics').readlines()
    except FileNotFoundError:
        statusMessage = "Not a valid backup archive! Exiting!"
        writeLog(statusMessage)
        status = 1000
        return [None,None,False]

    # Files inside the archive, not including the metadata
    totalFilesChecked = len(files) - 1

    # Files listed in the .ics metadata, not including the first line of the metadata.
    totalFilesExpected = len(validator) - 1

    global validateFilesTotal, validateFileCount, filesMismatched, filesUnlisted
    validateFilesTotal = totalFilesExpected
    validateFileCount = 0

    totalFilesMatched = 0
    totalUnmatchedFiles = 0
    totalMismatchedFiles = 0

    for cnt, file in enumerate(files):
        # Skip metadata
        if(file[0] == ".ics"):
            continue
        else:
            fileAuditName = validator[cnt - totalUnmatchedFiles].split(",")[0].replace("/", "\\").replace("\"", "").split(":\\")[1]
            fileAuditHashValue = ''.join(e for e in validator[cnt - totalUnmatchedFiles].split(",")[1] if e.isalnum())

            if(file[0] == fileAuditName):
                if(file[1] == fileAuditHashValue):
                    writeLog("Hash value matched for file '{}'.".format(file[0]))
                    totalFilesMatched += 1
                else:
                    writeLog("Hash value failed to matched for file '{}'.".format(file[0]))
                    writeLog("Expected '{}', got '{}'".format(file[1], fileAuditHashValue))
                    filesMismatched += "'{}'\n".format(file[0])
                    totalMismatchedFiles += 1
                    
                    # Mismatched hash value. Will not include in restoration.
                    os.remove(tempDir + "\\" + file[0])
                validateFileCount += 1
            else:
                # Filename mismatch. Will not include in restoration.
                writeLog("Expected: {}, got {}".format(fileAuditName, file[0]))
                filesUnlisted += "'{}'\n".format(file[0])

                os.remove(tempDir + "\\" + file[0])
                totalUnmatchedFiles += 1
                # print("Got: {}".format(file[0]))

    # Mode 1: Report success and returns temp directory.
    if(mode == 1):
        return [
            [
                totalFilesChecked,
                totalFilesExpected,
                totalFilesMatched,
                totalUnmatchedFiles,
                totalMismatchedFiles,
                filesMismatched,
                filesUnlisted
            ],
            tempDir,
            True
        ]
    # Default mode: Validate only
    else:
        # Disposes temp files used in validation
        shutil.rmtree(tempDir)

    writeLog("Files in backup: {}".format(totalFilesChecked))
    writeLog("Expected: {}".format(totalFilesExpected))
    writeLog("Matched: {}".format(totalFilesMatched))
    writeLog("Unlisted: {}".format(totalUnmatchedFiles))
    writeLog("Hash value mismatch: {}".format(totalMismatchedFiles))
    
    global validationStats
    status = 0
    validationStats = [
        totalFilesChecked,
        totalFilesExpected,
        totalFilesMatched,
        totalUnmatchedFiles,
        totalMismatchedFiles,
        filesMismatched,
        filesUnlisted
    ]

    endLog()

    return 0

def restore(backupFile=False, restoreLocation=False, ignore_mismatched_unlisted=False):
    resetVariables()
    startLog()

    writeLog("Started recover module.")

    # TODO: Validate the backup first!
    if (not backupFile):
        print("Backup file not provided!")
        return 1000
    if (not restoreLocation):
        print("Restore location not provided!")
        return 1000

    writeLog("Validating backup archive.")

    # Validate first.
    validationResults = validate(mode=1, backupFile=backupFile)

    # if validationResults == 

    # print(validationResults[0])
    global validationStats
    validationStats = validationResults[0]

    if(validationResults[2] is True):
        tempDir = validationResults[1]
        # Moves the backup
        # restoredFolder = shutil.move(tempDir + "/", restoreLocation)
        for i in os.listdir(tempDir):
            shutil.move(os.path.join(tempDir, i), restoreLocation)

    endLog()

def oneClickBackup(backup_location=None):
    config = Config(bk_loc=backup_location)

    backup(config.getFoldersToBackup(), config.getBackupLocation(), mode=1)
    
def configUpdate(backup_location=False, folders_to_backup=[]):
    # Backup setting directory
    # dbvrs_config_path = os.environ['APPDATA'] + "\\DBVRS"

    config = Config(bk_loc=backup_location)

    config.updateConfiguration(backup_location, folders_to_backup)


def main():
    global PRINT_LOG
    PRINT_LOG = True

    startLog()

    writeLog("Script executed, no UI.")

    if(sys.argv[1] == "-bk"):
        backup(sys.argv[2], sys.argv[3])
    elif(sys.argv[1] == "-v"):
        validate(mode=0, backupFile=sys.argv[2])
    elif(sys.argv[1] == "-r"):
        restore(sys.argv[2], sys.argv[3])
    # TEST COMMAND: Multiple folder
    elif(sys.argv[1] == "-t1"):
        DIRECTORIES_TO_BACKUP = ["E:\\Capstone\\files\\test_case_4", "E:\\Capstone\\files\\test_case_8"]
        backup(DIRECTORIES_TO_BACKUP, "E:\\Capstone\\backup\\test", mode=1)
    # TEST COMMAND: Single folder
    elif(sys.argv[1] == "-t2"):
        DIRECTORIES_TO_BACKUP = "E:\\Capstone\\files\\test_case_4"
        backup(DIRECTORIES_TO_BACKUP, "E:\\Capstone\\backup\\test", mode=0)
    # TEST COMMAND: One click
    elif(sys.argv[1] == "-t3"):
        oneClickBackup(backup_location="E:\\Capstone\\backup\\test")
    # TEST COMMAND: Update configuration
    elif(sys.argv[1] == "-t4"):
        configUpdate("E:\\Capstone\\backup\\test1", ["E:\\Capstone\\files\\test_case_8", "E:\\Capstone\\files\\test_case_4"])

if __name__ == '__main__':
    main()
