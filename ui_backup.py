import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Progressbar
from tkinter import *
import main


location = ''

def askDir():
    global location
    location = tk.filedialog.askdirectory()
    fileLocEntry.delete(0, END)
    fileLocEntry.insert(0, location)
    # print(location)

def startBackup():
    status = main.backup(location)
    if(status == 0):
        messagebox.showinfo("Backup success", "Backup completed.")
        import os
        os.startfile("D:/Capstone/backup")
        backupWin.destroy()



backupWin = Tk()
backupWin.resizable(False, False)
backupWin.title('Backup')

ment = StringVar()
Label(backupWin, text = "To backup").grid(row = 1, column = 0, sticky = E)
fileLocEntry = Entry(backupWin)
Button(backupWin, text = "Browse", command = askDir).grid(row = 1, column = 2)
Button(backupWin, text = "Backup", command = startBackup, bg = "green", fg = "white",).grid(row = 2, column = 1)

fileLocEntry.grid(row = 1, column = 1)
backupWin.mainloop()

'''
tkinter.filedialog.asksaveasfilename()
tkinter.filedialog.asksaveasfile()
tkinter.filedialog.askopenfilename()
tkinter.filedialog.askopenfile()
tkinter.filedialog.askdirectory()
tkinter.filedialog.askopenfilenames()
tkinter.filedialog.askopenfiles()
'''