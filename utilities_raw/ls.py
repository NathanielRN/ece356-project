import argparse

from client_backend import shell_context
from pathlib import PurePosixPath
from pathlib import Path
from client_backend.fs_db_file import Directory

# TODO: Can we make this a static global variable?
fs_db = FSDatabase('~/.fs_db_rdbsh')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='List files in a directory.')
    parser.add_argument('-l', '--long_format', action='store_true')
    parser.add_argument('pathForDirectoryListing', help='the path of the \
    directory whose files should be listed')

    args = parser.parse_args()

    targetPath = shell_context.PWD

    if args.pathForDirectoryListing:
        targetPath = args.pathForDirectoryListing

    targetDirectory = Directory(fs_db, targetPath)

    if args.long_format:
        fileDescriptionStrings = []
        totalSize = 0

        for fileObject in targetDirectory.walk():
            totalSize = fileObject.size
            fileDescriptionString = ''

            fileObjectType = fileObject.type
            if fileObjectType is Directory:
                fileDescriptionString += 'd'
            elif fileObjectType is SymbolicLink:
                fileDescriptionString += 'l'
            else:
                fileDescriptionString += '-'
            
            fileObjectPermissions = fileObject.permissions
            for i in range(2, -1, -1):
                for j in range(2, -1, -1):
                    if fileObjectPermissions >> 3*i+j & 1:
                        if j == 2:
                            fileDescriptionString += 'r'
                        elif j == 1:
                            fileDescriptionString += 'w'
                        else:
                            fileDescriptionString += 'x'
                    else:
                        fileDescriptionString += '-'
            
            fileDescriptionString += fileObject.numOfHardlinks

            fileDescriptionString += fileObject.owner.name

            fileDescriptionString += fileObject.group_owner.name

            if fileObjectType is Directory:
                # Just make it 0 because directories don't have a size
                fileDescriptionString += '0'
            elif fileObjectType is SymbolicLink:
                fileDescriptionString += len(fileObject.name)
            else:
                fileDescriptionString += fileObject.size

            fileDescriptionString += fileObject.modified_date

            fileDescriptionString += fileObject.name
        print([fileDescriptionString for fileDescriptionString in fileDescriptionStrings])
    else:
        print([fileObject.name for fileObject in targetDirectory.walk()])
