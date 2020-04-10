import argparse

from client_backend import shell_context

# TODO: Can we make this a static global variable?
fs_db = FSDatabase('~/.fs_db_rdbsh')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find provided pattern in files')
    parser.add_argument('searchPattern', help='the pattern to search for in matching files')
    parser.add_argument('filePattern', help='files that match this file pattern will be searched')

    args = parser.parse_args()

    filePattern = args.filePattern

    filePatternComponents = filePattern.split('/')

    findDirectory = None

    if len(filePatternComponents) == 1:
        findDirectory = Directory(fs_db, shell_context.PWD)
    else:
        findDirectory = Directory(fs_db, filePatternComponents[:-1].join('/'))

    matchedFiles = None
    if '*' in filePatternComponents[-1]:
        matchedFiles = findDirectory.get_all_files_like(filePatternComponents[-1].replace('*', '%'))
    else:
        foundFile = findDirectory.get_file(filePatternComponents[-1])
 
        if foundFile is Directory:
            raise ValueError(f"{fileName} is a directory.")
        
        matchedFiles = [foundFile]
    
    for fileObject in matchedFiles:
        for line_no, line_content in fs_.find_in_file(fileObject, args.searchPattern)
            print(f"{fileObject.name} - Line {line_no}: {line_content}")