#!/usr/bin/env python3

'''
MIT License

Copyright (c) 2019 Frank Eberle // www.frank-eberle.de

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from garminexport.garminclient import GarminClient
from datetime import datetime, timedelta
from dateutil.tz import gettz
from configparser import ConfigParser
import dateutil
import sys
import os
import logging
import argparse
import time
import shutil
from GarminUploader import udisks2



log = logging.getLogger("garmin-uploader")


class AppError(Exception):
    pass


def get_config_dir():
    config_base = None
    if "XDG_CONFIG_HOME" in os.environ:
        config_base = os.environ["XDG_CONFIG_HOME"]
    else:
        if not "HOME" in os.environ:
            raise AppError("Can't get home directory")
        config_base = os.path.join(os.environ["HOME"], ".config")
    dir = os.path.join(config_base, "garmin-uploader")
    if os.path.exists(dir):
        if not os.path.isdir(dir):
            raise AppError("{} is not a directory".format(dir))
    else:
        os.mkdir(dir)
    return dir


def check_config(config, section, req_settings):
    for key, default in req_settings.items():
        if not key in config[section]:
            if default != None:
                config.set(section, key, default)
            else:
                raise AppError("Option %s/%s missing in config file" % (section, key))


def load_config(filename = None):
    req_account_setting = {
        "username": None,
        "password": None,
    }
    req_generic_settings = {
        "timezone": "Europe/Berlin",
        "garmin_model": None,
        "activities_dir": "Garmin/Activities",
        "backup_dir": "",
    }
    config = ConfigParser()
    if filename == None:
        filename = get_config_dir() + "/config.ini"
    try:
        with open(filename, "r") as fd:
            config.read_file(fd)
    except Exception as e:
        raise AppError("Failed to read config file: " + str(e))
    # Check for required settings
    check_config(config, "account", req_account_setting)
    check_config(config, "settings", req_generic_settings)
    return config


class LastSync():

    def __init__(self):
        self._filename = get_config_dir() + "/lastsync.txt"

    def get(self):
        lastSync = None
        try:
            with open(self._filename, "r") as fd:
                line = fd.readline()
                lastSync = datetime.fromtimestamp(float(line))
                lastSync = lastSync.replace(tzinfo=dateutil.tz.tzlocal())
        except FileNotFoundError:
            lastSync = datetime.today().replace(tzinfo=dateutil.tz.tzlocal()) - timedelta(days=360)
        return lastSync

    def put(self, value):
        with open(self._filename,"w") as fd:
            fd.write(str(value.timestamp()))


def get_fit_files(path, lastSync, tzInfo):
    log.debug("Last sync: %s" % lastSync)
    result = []
    for entry in os.scandir(path):
        if not entry.name.endswith(".fit"):
            continue
        args = [int(x) for x in entry.name[:-4].split("-")] 
        created = datetime(*args, tzinfo=tzInfo)
        if created <= lastSync:
            continue
        result.append((entry.path, created))
    result.sort(key=lambda x:x[1])
    return result


def get_activities(client, lastSync):
    result = []
    startIdx = 0
    limit = 50
    terminate = False
    while not terminate:
        activities = client._fetch_activity_ids_and_ts(startIdx, limit)
        if len(activities) == 0:
            break
        for a in activities:
            if a[1] < lastSync:
                terminate = True
                break
            result.append(a)
        startIdx += 50
    return result


def get_garmin_fs_opath(udisks, model):
    max_wait = 40
    garmin_drive = None
    for w in range(0, max_wait):
        udisks.scan()
        drives = udisks.get_drives_by_prop("Model", model)
        if len(drives) == 0:
            if w == 0:
                print("Waiting for GARMIN device %s " % model, end = "", flush = True)
            print(".", end = "", flush = True)
            time.sleep(1)
        else:
            garmin_drive = drives[0]
            break
    print("")
    if garmin_drive == None:
        raise AppError("No GARMIN device found")
    opath = udisks.get_block_devices_by_prop("Drive", garmin_drive["path"])[0]["path"]
    return opath


def umount(udisks, opath):
    success = False
    for i in range(0, 5):
        try:
            udisks.umount(opath)
            success = True
            break
        except Exception as e:
            log.debug(str(e))
            time.sleep(1)
    if success == False:
        raise AppError("Failed to unmount GARMIN device")


def get_cmd_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--activities", default = None)
    arg_parser.add_argument("--config", default = None)
    arg_parser.add_argument("--dry-run", default = False, action = "store_true")
    arg_parser.add_argument("--debug", default = False, action = "store_true")
    args = arg_parser.parse_args()
    return args


def run():
    garmin_fs_opath = None
    udisks = None
    backup_dir = None

    args = get_cmd_args()

    if args.debug == True:
        logging.getLogger("garminexport").setLevel(logging.ERROR)
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.basicConfig(level=logging.DEBUG)
        log.setLevel(logging.DEBUG)

    try:
        config = load_config(args.config)

        # Check backup directory
        if config["settings"]["backup_dir"] != "":
            backup_dir = config["settings"]["backup_dir"]
            if not os.path.exists(backup_dir):
                raise AppError("Backup directory '%s' does not exist" % backup_dir)
            if not os.path.isdir(backup_dir):
                raise AppError("Specified backup directoy '%s' is not a directory" % backup_dir)
            if not os.access(backup_dir, os.W_OK):
                raise AppError("Specified backup directoy '%s' is not writeable" % backup_dir)

        if args.activities != None:
            activities_path = args.activities
        else:
            udisks = udisks2.UDisks2()
            garmin_fs_opath = get_garmin_fs_opath(udisks, config["settings"]["garmin_model"])
            log.debug("Mounting %s" % garmin_fs_opath)
            mount_point = udisks.mount(garmin_fs_opath)
            activities_path = os.path.join(mount_point, config["settings"]["activities_dir"])
        log.debug("activities path is %s" % activities_path)

        tzInfo = gettz(config["settings"]["timezone"])
        last_sync = LastSync()
        fit_files = get_fit_files(activities_path, last_sync.get(), tzInfo)
        if len(fit_files) == 0:
            print("No files to process")
            sys.exit(0)
        garmin_client = GarminClient(config["account"]["username"], config["account"]["password"])
        garmin_client.connect()
        activities = get_activities(garmin_client, last_sync.get())
        cnt_uploaded = 0
        for f in fit_files:
            found = False
            for a in activities:
                if f[1] == a[1]:
                    found = True
                    break
            if args.dry_run == False:
                last_sync.put(f[1])
            if found:
                log.debug("%s already uploaded" % f[0])
                continue
            else:
                print("uploading %s" % f[0])
                cnt_uploaded += 1
                if args.dry_run == False:
                    garmin_client.upload_activity(f[0])
                    if backup_dir != None:
                        shutil.copy(f[0], backup_dir)
                    
        print("%d activities uploaded" % cnt_uploaded)
    except AppError as e:
        print("Error: ", str(e), "\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Terminated by user")
        sys.exit(0)
    finally:
        if garmin_fs_opath != None:
            umount(udisks, garmin_fs_opath)
            


if __name__ == "__main__":
    main()
    sys.exit(0)
