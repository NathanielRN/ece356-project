import argparse

from client_backend import shell_context

# TODO: Can we make this a static global variable?
fs_db = FSDatabase('~/.fs_db_rdbsh')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Finds directories and files matching provided name')
    parser.add_argument('findPath', help='the directory and (partial) name of the file to be found')

    args = parser.parse_args()

    findPath = args.findPath

    findPathComponents = findPath.split('/')

    findDirectory = None

    if len(findPathComponents) == 1:
        findDirectory = Directory(fs_db, shell_context.PWD)
    else:
        findDirectory = Directory(fs_db, findPathComponents[:-1].join('/'))

    matchedFiles = None
    if '*' in filePatternComponents[-1]:
        matchedFiles = findDirectory.get_all_files_like(filePatternComponents[-1].replace('*', '%'))
    else:
        matchedFiles = [findDirectory.get_file(filePatternComponents[-1])]

    for fileObject in matchedFiles:
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

        print(fileDescriptionString)
