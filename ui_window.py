import tkinter as tk
from tkinter import*
#import os

def backup():
    master.destroy()
    import ui_backup
    
def recover():
    print("recover")

master = Tk()
master.title("Data Backup, Validation, and Recovey System")
master.resizable(False, False)

#button attrib
backupButton = Button(master,
                      text = 'Backup',
                      bg = "red",
                      fg = "white",
                      command = backup)
recoverButton = Button(master,
                       text = 'Recover',
                       bg = "green",
                       fg = "white",
                       command = recover)

#Buttons layout
backupButton.grid(row = 2,
                  column = 1,
                  ipady = 2,
                  ipadx = 2,
                  padx = 5)
recoverButton.grid(row = 2,
                   column = 3,
                   ipady = 2,
                   ipadx = 2,
                   padx = 5)

#for empty grids
Label(master, text = ' ').grid(row = 0, column = 0, ipadx = 25)
Label(master, text = ' ').grid(row = 0, column = 4, ipadx = 25)
Label(master, text = ' ').grid(row = 3, column = 0, ipadx = 25)

master.mainloop()
