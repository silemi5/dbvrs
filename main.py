import os
from datetime import datetime
import hashlib
import zipfile
import fnmatch
import string
import tempfile

# Gets current date and time upon backup execution.
today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
files = []

# Variables that can be edited
# TODO: Prevent users from backing-up system files.
DIRECTORY_TO_BACKUP = 'D:/Capstone/files'
DIRECTORY_TO_STORE_BACKUP = 'D:/Capstone/backup/'
filetypes_to_include = ['*.prn']

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def backup(to_backup=False):
    if(to_backup != False):
        DIRECTORY_TO_BACKUP = to_backup

    print(DIRECTORY_TO_BACKUP)
    
    # r=root, d=directories, f = files
    for r, d, f in os.walk(DIRECTORY_TO_BACKUP):
        for file in f:
            path = os.path.join(r, file)
            files.append([path, md5(path)])

    # Create a metadata
    metadata = open(".ics", "w+")
    metadata.write('{},"{}","{}",{}'.format(today, DIRECTORY_TO_BACKUP, DIRECTORY_TO_STORE_BACKUP, filetypes_to_include))

    # Creates a ZIP archive using LZMA compression
    zipName = ''.join([DIRECTORY_TO_STORE_BACKUP, today, '.zip'])
    zipObj = zipfile.ZipFile(zipName, 'w', zipfile.ZIP_LZMA)

    # TODO: Progress bar
    # print("Files: " + str(files))
    # print("File count: " + str(len(files)))

    # Starts storing files to archive
    for file in files:
        filename = file[0]
        zipObj.write(filename)
        metadata.write('\n"{}",{}'.format(file[0], file[1]))

    metadata.close()
    zipObj.write('.ics')
    zipObj.close()

    # TODO: Delete .ics file

    print("Backup completed.")
    
    return 0

def validate(mode=0):
    if(mode == 1):
        print("Mode 1 initiated.")
        return 0
    
    # TODO: Arguements for validation
    # TODO: Check if provided file is NOT a backup archive.
    zipObj = zipfile.ZipFile(''.join([DIRECTORY_TO_STORE_BACKUP, '2019-12-06_200319.zip']))

    # Creates a temporary directory for validation
    tempDir = tempfile.mkdtemp()
    print(tempDir)
    zipObj.extractall(path=tempDir)

    for r, d, f in os.walk(tempDir):
        for file in f:
            path = os.path.join(r, file)
            files.append([path.replace(tempDir + '\\', ""), md5(path)])

    validator = open(tempDir + '/.ics').readlines()

    # print(validator)

    for cnt, file in enumerate(files):
        # print("{}: {}".format(cnt, file[0]))
        # Skip metadata
        if(file[0] == ".ics"):
            continue
        else:
            fileAuditName = validator[cnt].split(",")[0].replace("/", "\\").replace("\"", "").split(":\\")[1]
            fileAuditChecksum = ''.join(e for e in validator[cnt].split(",")[1] if e.isalnum())

            if(file[0] == fileAuditName):
                print("'{}' == '{}'".format(file[1], fileAuditChecksum))
                if(file[1] == fileAuditChecksum):
                    print("File: {}, Checksum matched!".format(file[0]))
            else:
                print("File name didn't matched.")

    return 0

def restore():
    # TODO: Validate the backup first!
    validationStatus = validate(mode=1)
    print("Validation status: {}".format(validationStatus))


def main():
    # backup(DIRECTORY_TO_BACKUP)
    # validate()
    restore()
    # import ui_window
    # Really am not hacking

main()
