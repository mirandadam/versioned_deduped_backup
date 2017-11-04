# versioned_deduped_backup
Simple folder backup with versioning, deduplication and deduplication.

This is a simple script collection for backing up files to a folder structure. Subsequent backups will reuse files in the folder structure.

Files from the source folder are scanned, hashed and copied to a folder structure with the following characteristics:
* The output file name is the same as the sha256 hash of it's contents
* The output file path is inside a two level folder structure, with the first level folders named with the first hexadecimal character of the hash, and the second level folders named with the second hexadecimal character of the hash.

The metadata of the file is recorded in a log file containing the hash, the file size, the date of last modification and the file path.

## Example

TODO

## Usage

Edit do_backup.py to setup your source folder, output folder and log file.

Run do_backup with Python 3.5 or later.

## File format
sha256hash \<tab\> file size in bytes \<tab\> last modification date \<tab\> file path

## To do
* implement command-line configuration
* implement incremental backup
* implement full folder structure consistency check and heal
* implement checking file change dates (time zones and small time differences have to be considered)
* check if the date of last modification respects time zones
