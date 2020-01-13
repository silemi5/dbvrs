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

# Gets current date and time upon backup execution.
today = datetime.now().strftime("%Y-%m-%d_%H%M%S")

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
backupMessageToShow = " "

validateFileCount = 0
validateFilesTotal = 0
validationStats = []

# Variable to report to the GUI if something's amiss.
status = 0
statusMessage = ""

def resetVariables():
    global backupFileCount, backupFilesTotal
    global validateFileCount, validateFilesTotal

    backupFileCount = 0
    backupFilesTotal = 0
    validateFileCount = 0
    validateFilesTotal = 0

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def writeLog(message):
    # log = open("dbvrs_{}.log".format(today), "w+")
    log.write("[{}]: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))
    if(PRINT_LOG):
        print("[{}]: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))
    # log.close()

def disk_usage(path="/"):
    total, used, free = shutil.disk_usage(path)

    return { "total": total, "used": used, "free": free }

    # print("Total: %d GiB" % (total // (2**30)))
    # print("Used: %d GiB" % (used // (2**30)))
    # print("Free: %d GiB" % (free // (2**30)))

def backup(to_backup=False, store_backup=False):
    startLog()

    resetVariables()

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

    # Checks if backup location exists. If not, creates one.
    if not os.path.exists(DIRECTORY_TO_STORE_BACKUP):
        os.makedirs(DIRECTORY_TO_STORE_BACKUP)

    # r=root, d=directories, f = files
    for r, d, f in os.walk(DIRECTORY_TO_BACKUP):
        for file in f:
            backupFilesTotal += 1
            path = os.path.join(r, file)
            file_size = os.path.getsize(path)
            archive_size += file_size
            files.append([path, md5(path), file_size])

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
    
    return 0

def validate(mode=0, backupFile=False):
    startLog()
    
    resetVariables()

    writeLog("Started validation module")

    # Backup file not specified.
    if (not backupFile):
        writeLog("Backup file not provided!")
        return 1000
    
    # TODO: Arguements for validation
    # TODO: Check if provided file is NOT a backup archive.
    writeLog("Opening archive '{}'".format(backupFile))
    zipObj = zipfile.ZipFile(backupFile)

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
    validator = open(tempDir + '/.ics').readlines()

    # Files inside the archive, not including the metadata
    totalFilesChecked = len(files) - 1

    # Files listed in the .ics metadata, not including the first line of the metadata.
    totalFilesExpected = len(validator) - 1

    global validateFilesTotal, validateFileCount
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
            fileAuditChecksum = ''.join(e for e in validator[cnt - totalUnmatchedFiles].split(",")[1] if e.isalnum())

            if(file[0] == fileAuditName):
                if(file[1] == fileAuditChecksum):
                    writeLog("Hash value matched for file '{}'.".format(file[0]))
                    totalFilesMatched += 1
                else:
                    writeLog("Hash value failed to matched for file '{}'.".format(file[0]))
                    totalMismatchedFiles += 1
                validateFileCount += 1
            else:
                # Filename mismatch. Will not include in restoration.
                writeLog("Expected: {}, got {}".format(fileAuditName, file[0]))
                os.remove(file[0])
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
                totalMismatchedFiles
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
    
    global status, validationStats
    status = 0
    validationStats = [
        totalFilesChecked,
        totalFilesExpected,
        totalFilesMatched,
        totalUnmatchedFiles,
        totalMismatchedFiles
    ]

    return 0

def restore(backupFile=False, restoreLocation=False):
    startLog()

    resetVariables()
    
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

    if(validationResults[2] is True):
        tempDir = validationResults[1]
        # Moves the backup
        restoredFolder = shutil.move(tempDir + "/", restoreLocation)
        # for i in os.listdir(tempDir):
        #     shutil.move(os.path.join(tempDir, i), restoreLocation)
    
def startLog():
    global log
    log = open("dbvrs_{}.log".format(today), "w+")

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

if __name__ == '__main__':
    main()
