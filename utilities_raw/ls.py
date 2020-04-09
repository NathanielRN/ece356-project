
from client_backend import shell_context
from pathlib import PurePosixPath
from pathlib import Path
from client_backend.fs_db_file import Directory, SymbolicLink, RegularFile

def listDirectories(pathForDirectoryListing=None, useLongListFormat=False):
    if (useLongListFormat):
        for item in PurePosixPath(shell_context.PWD).iterdir():
            print(item.name())
    else:


if __name__ == "__main__":
    useLongListFormat = False
    pathForDirectoryListing = None
    for item in sys.argv:
        if item.startswith('-'):
            if item == '-l':
                useLongListFormat=True
            elif item == '-h':
                print('''
                Usage: ls [OPTION]... [FILE]...
                Options: -l use a long listing format
                ''')
            else:
                raise SyntaxError('Unknown Option Provided: ', item)
        elif pathForDirectoryListing is None:
            pathForDirectoryListing = item
        else:
            raise SyntaxError('Invalid argument', item)
    listDirectories(pathForDirectoryListing, useLongListFormat)