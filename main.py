import os
from datetime import datetime
import hashlib
import zipfile
import fnmatch
import string

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

    for file in files:
        filename = file[0]
        zipObj.write(filename)
        metadata.write('\n"{}",{}'.format(file[0], file[1]))

    metadata.close()
    zipObj.write('.ics')
    zipObj.close()

    print("Backup completed.")
    
    return 0

def restore():
    # TODO: Validate every file inside the zip archive if it matches.
    zipObj = zipfile.ZipFile(''.join([DIRECTORY_TO_STORE_BACKUP, '2019-11-13_051110.zip']))
    metadata = zipObj.open('.ics').read().splitlines()

    listOfFiles = zipObj.namelist()

    # for f in listOfFiles:
    #     file = zipObj.read(f)
    #     print(''.join([f, ', ', hashlib.md5(file).hexdigest()]))

    for f in metadata:
        print(f)

    # for line in metadata:
    #     print(line)
    # print(metadata[0])

def main():
    # backup()
    # restore()
    import ui_window

main()
