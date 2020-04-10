import argparse
import shell_context

from fs_db_file import Directory

# TODO: Can we make this a static global variable?
fs_db = FSDatabase('~/.fs_db_rdbsh')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change the current working directory.")
    parser.add_argument('pathToChangeTo', help='The relative or absoulte path to navigate to')

    args = parser.parse_args()

    newFileDirectory = Directory(fs_db, args.pathToChangeTo)

    shell_context.PWD = newFileDirectory.name