import PySimpleGUI as sg
from tkinter import messagebox
import threading

import main as dbvrs
from config import Config

# Theme
sg.theme('TanBlue')

# Menubar
menuBar = [
    ['File', ['Validate a backup...', 'Restore from a backup...', 'Start/Stop scheduled backups', 'Configure']],
    ['Help', ['About this program']]
]

# layout
welcomeLayout = None
validateLayout = None
restoreLayout = None
configLayout = None
backgroundTray = None

def initiateLayoutVariables():
    global welcomeLayout, validateLayout, restoreLayout, configLayout, backgroundTray

    welcomeLayout = [
        [ sg.Menu(menuBar)],
        [ sg.Text("Hello!") ],
        [ sg.Text("To begin to backup, press 'Start' to continue.") ],
        [ sg.Text("Otherwise, select a module to start in the menu.") ],
        [ sg.Button("Start"), sg.Exit() ],
    ]

    validateLayout = [
        [ sg.Text("Please select a backup file generated by this program.") ],
        [ sg.Input(), sg.FileBrowse(file_types=(("DBVRS generated archive", "*.zip"),))],
        [ sg.Button("Validate"), sg.Cancel()]
    ]

    restoreLayout = [
        [ sg.Text("Please select a backup file to restore.") ],
        [ sg.Input(), sg.FileBrowse(file_types=(("DBVRS generated archive", "*.zip"),)) ],
        [ sg.Button("Next"), sg.Cancel() ],
    ]

    configLayout = [
        [sg.Text('Configuration', font=('Helvetica', 16), justification='left')],      
        [sg.Text('Scheduled backups', font=('Helvetica', 13), justification='left')],      
        [
            sg.Radio('Daily', key='-sbDaily-', group_id='scheduledBackup-', size=(12, 1)), sg.Radio('Weekly', key='-sbWeekly-', group_id='scheduledBackup-', size=(12, 1))
        ],          
        [
            sg.Radio('Monthly', key='-sbMonthly-', group_id='scheduledBackup-', size=(12, 1)), sg.Radio('Off', key='-sbOff-', group_id='scheduledBackup-', size=(12, 1))
        ],      
        [sg.Text('_'  * 100, size=(20, 1))],
        [sg.Text('Schedule', font=('Helvetica', 13), justification='left')],      
        [sg.Text('Scheduled backup time:'), sg.Input(key='-TIME-')],
        [
            sg.Text('Scheduled backup weekday:'),
            sg.Combo([
                'Sunday',
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
            ], size=(13,1), key='-WEEKDAY-', default_value='')
        ],
        [
            sg.Text('Scheduled backup monthly:'),
            sg.Input(key='-DAY-', size=(13,1), enable_events=True)
        ],
        [sg.Submit(), sg.Cancel()]
    ]

    backgroundTray = ['BLANK', ['!Scheduled backups is on', 'E&xit']]

# create window
initiateLayoutVariables()
window = sg.Window("Data backup, validation, and recovery system").Layout(welcomeLayout)

# Event loop
while True:
    event, values = window.Read()

    if event is None or event == 'Exit':
        break
    
    # Backup module 
    if event == "Start":
        window.Hide()

        # TODO: Check if config file exists then save it
        config = Config()

        # Backup location
        backupLocation = ""

        if config.NO_CONFIG == True:
            while backupLocation == "":
                backupLocation = sg.PopupGetFolder('Please select a folder to store your backups.', 'Backup')

            # Empty backup location or clicked cancel
            if(backupLocation is None or not backupLocation):
                window.UnHide()
                continue

            # TODO: Multiple folders selection on UI.
            # To backup location
            toBackup = []
            continueAddingFolders = True
            while continueAddingFolders:
                folderToBackup = sg.PopupGetFolder('Please select a folder to backup.', 'Backup')

                # Empty to backup location or clicked cancel
                if(folderToBackup is None or not folderToBackup):
                    window.UnHide()
                    break

                toBackup.append(folderToBackup)
                
                promptContinueAddingFolders = sg.popup_yes_no('Do you want to add another folder?')

                if promptContinueAddingFolders == "Yes":
                    continueAddingFolders = True
                else:
                    continueAddingFolders = False

            # Empty to backup location or clicked cancel
            if(toBackup is None or not toBackup):
                window.UnHide()
                continue
        else:
            backupLocation = config.getBackupLocation()
            toBackup = config.getFoldersToBackup()

        backupLocation += "/"
        mode = 1
        # toBackup += "/"
        backupThread = threading.Thread(target=dbvrs.backup, args=(toBackup, backupLocation, mode))
        backupThread.start()

        while backupThread.is_alive():
            current = dbvrs.backupFileCount
            total = dbvrs.backupFilesTotal

            if(dbvrs.backupFileCount == 0):
                current = 0
            if(dbvrs.backupFilesTotal == 0):
                total = 1

            sg.OneLineProgressMeter('Backup progress', current, total, '__backupProgress__',"Backup in progress...",orientation='h',)

        if(dbvrs.status != 0):
            sg.OneLineProgressMeterCancel('__backupProgress__')
            messagebox.showerror(title="Error!", message=dbvrs.statusMessage)
            window.UnHide()
        else:
            sg.OneLineProgressMeter('Backup progress', total, total, '__backupProgress__',"Backup in progress...",orientation='h',)
            sg.PopupOK("Successfully backed up the specified folder!")

            if config.NO_CONFIG:
                configAnswer = sg.popup_yes_no('Do you want to save this session?')
                
                if configAnswer == "Yes":
                    config.updateConfiguration(backup_location=backupLocation, folders_to_backup=toBackup)
                    
            window.UnHide()

    # Validate module
    if event == "Validate a backup...":
        window.Hide()
        initiateLayoutVariables()
        validateWindow = sg.Window("Validate a backup").Layout(validateLayout)

        while True:
            validateEvent, validateValues = validateWindow.Read()

            if validateEvent is None or validateEvent == "Cancel":
                window.UnHide()
                validateWindow.close()
                break
            
            if validateEvent == "Validate":
                # Gets the file location of the archive.
                validateArchive = validateValues[0]

                if(validateArchive == ""):
                    continue

                # Creates a thread for validation
                validateThread = threading.Thread(target=dbvrs.validate, args=(0, validateArchive))
                validateThread.start()
                validateWindow.Hide()

                while validateThread.is_alive():
                    current = dbvrs.validateFileCount
                    total = dbvrs.validateFilesTotal

                    if(dbvrs.validateFileCount == 0):
                        current = 0
                    if(dbvrs.validateFilesTotal == 0):
                        total = 1

                    sg.OneLineProgressMeter('Validating backup', current, total, '__validateProgress__',"Validating backup in progress...",orientation='h',)
                
                if(dbvrs.status != 0):
                    sg.OneLineProgressMeter('Validating backup', total, total, '__validateProgress__',"Validating backup in progress...",orientation='h',)
                    sg.OneLineProgressMeterCancel("__validateProcess__")
                    messagebox.showerror(title="Error!", message=dbvrs.statusMessage)
                    window.UnHide()
                    break
                else:
                    sg.OneLineProgressMeter('Validating backup', total, total, '__validateProgress__',"Validating backup in progress...",orientation='h',)
                    
                    validationStatsOutput = "Validation results\n\nFiles in backup: {}\nExpected: {}\nMatched: {}\nUnlisted: {}\nHash value mismatched: {}\n\nMismatched files:\n{}\n\nUnlisted files:\n{}\n\n".format(
                        dbvrs.validationStats[0],
                        dbvrs.validationStats[1],
                        dbvrs.validationStats[2],
                        dbvrs.validationStats[3],
                        dbvrs.validationStats[4],
                        dbvrs.validationStats[5],
                        dbvrs.validationStats[6]
                    )
                    sg.PopupScrolled(validationStatsOutput, size=(50, 10))
                    window.UnHide()
                    break
    
    # Restore module
    if event == "Restore from a backup...":
        window.Hide()
        initiateLayoutVariables()
        restoreWindow = sg.Window("Restore from a backup").Layout(restoreLayout)

        while True:
            restoreEvent, restoreValues = restoreWindow.Read()

            if restoreEvent is None or restoreEvent == "Cancel":
                window.UnHide()
                restoreWindow.close()
                break

            if restoreEvent == "Next":
                backupFile = restoreValues[0]

                # Skip if empty
                if(backupFile == ""):
                    continue

                restoreWindow.Hide()

                restoreLocation = ""

                while restoreLocation == "":
                    restoreLocation = sg.PopupGetFolder('Please select a folder to restore your backups.')
                
                if (restoreLocation is None or restoreLocation == "Cancel" or restoreLocation == ""):
                    window.UnHide()
                    restoreWindow.close()
                
                # TODO: Restore backup command
                restoreThread = threading.Thread(target=dbvrs.restore, args=(backupFile, restoreLocation))
                restoreThread.start()
                
                while restoreThread.is_alive():
                    current = dbvrs.validateFileCount
                    total = dbvrs.validateFilesTotal

                    if(dbvrs.validateFileCount == 0):
                        current = 0
                    if(dbvrs.validateFilesTotal == 0):
                        total = 1
                    if(current == total):
                        current -= 1
                        sg.OneLineProgressMeter('Restoring backup', current, total, '__restoreProgress__',"Validation completed. Restoring.",orientation='h',)
                    else:
                        sg.OneLineProgressMeter('Restoring backup', current, total, '__restoreProgress__',"Validating backup in progress...",orientation='h',)
                    
                if(dbvrs.status != 0):
                    sg.OneLineProgressMeterCancel("__restoreProgress__")
                    messagebox.showerror(title="Error!", message=dbvrs.statusMessage)
                    window.UnHide()
                else:
                    sg.OneLineProgressMeter('Restoring backup', total, total, '__restoreProgress__',"Validating backup in progress...",orientation='h',)

                    validationStatsOutput = "Restoration results\n\nFiles in backup: {}\nExpected: {}\nMatched: {}\nUnlisted: {}\nHash value mismatched: {}\n\nNot restored files due to following:\nMismatched files:\n{}\n\nUnlisted files:\n{}\n\n".format(
                        dbvrs.validationStats[0],
                        dbvrs.validationStats[1],
                        dbvrs.validationStats[2],
                        dbvrs.validationStats[3],
                        dbvrs.validationStats[4],
                        dbvrs.validationStats[5],
                        dbvrs.validationStats[6],
                    )
                    sg.PopupScrolled(validationStatsOutput, size=(70, 10))
                    sg.Popup("Archive successfully restored!")
                    window.UnHide()
                    break

    # About screen
    if event == "About this program":
        aboutString = "Data backup, validation, and recovery system\n"
        aboutString += "In Partial Fulfillment of the Requirements for the CSIT 141 Capstone Project\n\n"
        aboutString += "Members:\nEmir Jo Jr.\nMoh. Alnaghil Teo\nSadik Mujaal"
        aboutString += "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nThank you for the hard work!"
        sg.PopupScrolled(aboutString, size=(50, 10), auto_close=True)

    # Configure screen
    if event == "Configure":
        window.Hide()

        config = dbvrs.getConfig()

        if(config.NO_CONFIG):
            sg.Popup("Please backup first by clicking 'Start' on the welcome screen.")
            window.UnHide()
        else:
            scheduled_backup_mode = config.getScheduledBackupMode()
            scheduled_backup_time = config.getScheduledTime()
            scheduled_backup_weekday = config.getScheduledWeekDay()
            scheduled_backup_day = config.getBackupDay()

            initiateLayoutVariables()
            configWindow = sg.Window('DBVRS Configuration', layout=configLayout, finalize=True)

            if scheduled_backup_weekday == 0:
                configWindow['-WEEKDAY-'].update('Sunday')
            elif scheduled_backup_weekday == 1:
                configWindow['-WEEKDAY-'].update('Monday')
            elif scheduled_backup_weekday == 2:
                configWindow['-WEEKDAY-'].update('Tuesday')
            elif scheduled_backup_weekday == 3:
                configWindow['-WEEKDAY-'].update('Wednesday')
            elif scheduled_backup_weekday == 4:
                configWindow['-WEEKDAY-'].update('Thursday')
            elif scheduled_backup_weekday == 5:
                configWindow['-WEEKDAY-'].update('Friday')
            elif scheduled_backup_weekday == 6:
                configWindow['-WEEKDAY-'].update('Saturday')

            if scheduled_backup_mode == 0:
                configWindow['-sbDaily-'].update(True)
            elif scheduled_backup_mode == 1:
                configWindow['-sbWeekly-'].update(True)
            elif scheduled_backup_mode == 2:
                configWindow['-sbMonthly-'].update(True)
            elif scheduled_backup_mode == 3:
                configWindow['-sbOff-'].update(True)

            configWindow['-TIME-'].update(scheduled_backup_time)
            configWindow['-DAY-'].update(scheduled_backup_day)


            while True:
                configEvent, configValues = configWindow.read()

                if configEvent is None or configEvent == 'Exit' or configEvent == 'Cancel':
                    window.UnHide()
                    configWindow.close()
                    break

                if configEvent == 'Submit':
                    
                    if configValues['-sbDaily-'] is True:
                        config.setScheduledBackupMode(0)
                    elif configValues['-sbWeekly-'] is True :
                        config.setScheduledBackupMode(1)
                    elif configValues['-sbMonthly-'] is True :
                        config.setScheduledBackupMode(2)
                    elif configValues['-sbOff-'] is True :
                        config.setScheduledBackupMode(3)

                    if configValues['-WEEKDAY-'] == 'Sunday':
                        config.setScheduledWeekDay(0)
                    elif configValues['-WEEKDAY-'] == 'Monday':
                        config.setScheduledWeekDay(1)
                    elif configValues['-WEEKDAY-'] == 'Tuesday':
                        config.setScheduledWeekDay(2)
                    elif configValues['-WEEKDAY-'] == 'Wednesday':
                        config.setScheduledWeekDay(3)
                    elif configValues['-WEEKDAY-'] == 'Thursday':
                        config.setScheduledWeekDay(4)
                    elif configValues['-WEEKDAY-'] == 'Friday':
                        config.setScheduledWeekDay(5)
                    elif configValues['-WEEKDAY-'] == 'Saturday':
                        config.setScheduledWeekDay(6)

                    config.setBackupDay(configValues['-DAY-'])
                    config.setScheduledTime(configValues['-TIME-'])
                    config.saveChanges()

                    window.UnHide()
                    configWindow.close()

    if event == 'Start/Stop scheduled backups':
        initiateLayoutVariables()

        config = dbvrs.getConfig()

        if(config.NO_CONFIG):
            sg.Popup("Please backup first by clicking 'Start' on the welcome screen.")
        else:
            print("Proceed")

            tray = sg.SystemTray(menu=backgroundTray, data_base64=sg.DEFAULT_BASE64_ICON, )

            scheduledBackupThread = threading.Thread(target=dbvrs.backgroundProcess, args=())
            scheduledBackupThread.start()
            
            while True:
                menu_item = tray.read()
                if menu_item == 'Exit':
                    scheduledBackupThread.do_run = False
                    break
                elif menu_item == 'Open':
                    sg.SystemTray.notify('Notification Open', 'This is the notification message')
                    sg.popup('Menu item chosen', menu_item)
            
            tray.Close()
# read window

window.close()
