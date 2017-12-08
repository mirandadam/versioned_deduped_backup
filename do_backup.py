#!/usr/bin/python3
# -*- coding: <encoding name> -*-

"""
Versioned Deduped Backup

Folder backup with versioning and deduplication

log file format:
sha256hash<tab>file size in bytes<tab>last modification date<tab>full file path
"""
# TODO: document this.

import os
import sys
import hashlib
import re
import datetime
import shutil
import itertools
import argparse

assert sys.version_info > (3, 4)  # TODO: properly require python 3.5 or later

# user configuration:
parser = argparse.ArgumentParser(description='Folder backup with versioning and deduplication')
parser.add_argument('log_file', nargs=1,  help='the log file that stores the file metadata')
parser.add_argument('output_folder', nargs=1,  help='folder to store the backup as a tree of files renamed according to their hash')
parser.add_argument('source_folders', metavar='source_folder', nargs='+',  help='original folders to be backed up')

args = parser.parse_args()

source_folders = list(i.rstrip(os.sep) for i in args.source_folders)
output_folder = args.output_folder[0].rstrip(os.sep)
log_file = args.log_file[0]
# end of user configuration.

name_validator = re.compile('[0-9a-f]{64}')  # sha256 lowercase hash
folder_validator = re.compile('[0-9a-f]')  # single hexadecimal lowercase character
if not os.path.exists(output_folder):
    print('Creating', output_folder)
    os.makedirs(output_folder)
else:
    print('Output folder already exists. Trying to continue previous inventory...')


def calculate_hash(filename):
    # sha256 hasher
    h = hashlib.sha256()
    f = open(filename, 'rb')
    b = f.read(8 * 1024 * 1024)
    c = len(b)  # byte count
    while b:
        h.update(b)
        b = f.read(8 * 1024 * 1024)
        c = c + len(b)
    return (h.hexdigest(), c)


def parse_date(x):
    r = None
    try:
        r = datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%f")  # isoformat with fraction of seconds
    except ValueError:
        try:
            r = datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")  # isoformat
        except ValueError:
            pass
    return r


def make_path(h, root_folder):
    """
      Generate the expected path to find the file in.
      At this time, the folders are nested in two levels, giving
      16*16=256 subfolders. In a 100000 file backup, each folder is expected
      to hold about 400 files.
    """
    return root_folder + os.sep + h[0] + os.sep + h[1] + os.sep + h


raw_log = []
if os.path.isfile(log_file):
    print('Reading existing log at ' + log_file)
    raw_log = list(i.rstrip('\r\n ').split('\t', 3) for i in open(log_file, 'r').readlines())
    print(len(raw_log), 'files found in log.')
else:
    print('No log file found to continue. Starting from the beginning.')

current_log = []
bogus_entries = []
if raw_log:
    print("Checking log file consistency...")
    warned = False
    for i in raw_log:
        target_file = make_path(i[0], output_folder)
        error = False
        if not os.path.isfile(target_file):
            print('WARNING: log entry points to a non-existing file in output folder.')
            error = True
        if not int(i[1]) == os.stat(target_file).st_size:
            print('WARNING: log entry size is different from size of file in output folder.')
            print(' File REMOVED from output folder:', target_file)
            os.remove(target_file)
            error = True
        if not parse_date(i[2]):
            print('WARNING: error parsing entry modification date.')
            error = True
        if error:
            print(' Entry NOT removed from log file. Contents follow:')
            print('', i)
            bogus_entries.append(i)
        else:
            current_log.append(i)


print('Scanning for existing files in destination folder...')
files_in_output = set()
for root, dirs, files in os.walk(output_folder):
    for d in dirs:
        assert folder_validator.fullmatch(d)  # TODO: handle malformed folders
    if root != output_folder:
        for f in files:
            assert name_validator.fullmatch(f)  # TODO: handle spurious files
            assert f not in files_in_output  # TODO: handle repeated files
            assert root + os.sep + f == make_path(f, output_folder)  # TODO: handle misplaced files
            files_in_output.add(f)
print(len(files_in_output), 'files found in output folder.')


print('Scanning for files in the source folder...')
backlog = set()
for root, dirs, files in itertools.chain.from_iterable(map(os.walk, source_folders)):
    for f in files:
        backlog.add(root + os.sep + f)
print(len(backlog), 'files in the source folder.')


already_processed_files = set(i[3] for i in current_log)
if already_processed_files:
    print(len(already_processed_files), 'files already processed.')
backlog.difference_update(already_processed_files)
print(len(backlog), 'files to process.')

f = open(log_file, 'a')  # open for appending, create if not exists
for i in backlog:
    try:
        # print(i)
        m = datetime.datetime.fromtimestamp(os.stat(i).st_mtime).isoformat()
        # print(m)
        h, s = calculate_hash(i)
        #print(h, s)
        assert s == os.stat(i).st_size  # TODO: check if this is always true. I am still wary that st_size might include slack space or filesystem structures.
        if h not in files_in_output:
            destination_file = make_path(h, output_folder)
            if not os.path.exists(os.path.dirname(destination_file)):
                os.makedirs(os.path.dirname(destination_file))
            shutil.copy(i, destination_file)
            files_in_output.add(h)
        f.write('\t'.join([h, str(s), m, i]) + '\n')
        f.flush()
    except Exception as e:
        print(e)
f.close()

print('Finished processing.')
if bogus_entries:
    print('Found', len(bogus_entries), 'invalid entries in current log file:')
    for i in bogus_entries:
        print('\t'.join(i))
