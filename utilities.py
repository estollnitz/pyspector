import os
import platform
import subprocess

def openFile(filePath):
    '''Opens a file using the system's default application.'''
    if platform.system() == 'Darwin':
        subprocess.call(('open', filePath))
    elif platform.system() == 'Windows':
        os.startfile(filePath)
    else:
        subprocess.call(('xdg-open', filePath))
