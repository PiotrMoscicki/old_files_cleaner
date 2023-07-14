# This script removes files from provided directory based on yaml config file from the same directory.
# Types of rules are:
# 1. Remove files older than X days
# 2. Remove oldest files to keep only X files
# 3. Remove oldest files to keep only X GB of files
# Additionally script can move files to archive directory instead of removing them based on config file
# with the same types of rules as above.
# Script can be run with --dry-run option to see what files will be removed.
# Script can be run with --verbose option to see what files are removed.
# Example config file:
# ---
# archive:
#   - max_files: 10
# remove:
#   - days: 30
# ---
# above config will archive 10 oldest files and remove files older than 30 days (including those in archive directory)

import os
import sys
import yaml
import shutil
import argparse
import logging
import logging.handlers
from datetime import datetime, timedelta


default_config_file_name = 'old_files_cleaner.yaml'
default_archive_directory_name = 'archive'


def get_args():
    parser = argparse.ArgumentParser(description='Remove files from provided directory based on yaml config file from the same directory.')
    parser.add_argument('-d', '--directory', required=True, help='Directory to clean')
    parser.add_argument('-c', '--config', default=default_config_file_name, help='Config file name')
    parser.add_argument('-a', '--archive', default=default_archive_directory_name, help='Archive directory name')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print what files are removed')
    parser.add_argument('-n', '--dry-run', action='store_true', help='Print what files will be removed without removing them')
    return parser.parse_args()


def get_logger():
    logger = logging.getLogger('old_files_cleaner')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def get_files(directory):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files


def get_file_age(file):
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file))
    return file_age.days


def get_file_size(file):
    file_size = os.path.getsize(file)
    return file_size


def remove_file(file, dry_run, verbose, logger):
    if dry_run:
        logger.info('Would remove file: {}'.format(file))
    else:
        os.remove(file)
        if verbose:
            logger.info('Removed file: {}'.format(file))


def move_file(file, archive, dry_run, verbose, logger):
    if dry_run:
        logger.info('Would move file: {}'.format(file))
    else:
        shutil.move(file, archive)
        if verbose:
            logger.info('Moved file: {}'.format(file))


def get_files_to_remove_or_move(files, config):
    files_to_remove_or_move = []
    for rule in config:
        if 'days' in rule:
            for file in files:
                if get_file_age(file) > rule['days']:
                    files_to_remove_or_move.append(file)
        elif 'max_files' in rule:
            files.sort(key=os.path.getmtime)
            files.reverse()
            for file in files[rule['max_files']:]:
                files_to_remove_or_move.append(file)
        elif 'max_size' in rule:
            files.sort(key=os.path.getmtime)
            files.reverse()
            size = 0
            for file in files:
                size += get_file_size(file)
                if size > rule['max_size']:
                    files_to_remove_or_move


def main():
    args = get_args()
    logger = get_logger()
    config = get_config(args.config)
    files = get_files(args.directory)
    files.sort(key=os.path.getmtime)
    files.reverse()


