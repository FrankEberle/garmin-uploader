# garmin-uploader
Tool to upload activities from Garmin Forerunner 110 to the Garmin Connect website.

## Prerequisites
* Python3
* My modified version of [GarminExport](https://github.com/FrankEberle/garminexport) forked from [Peter Gardfjäll](https://github.com/petergardfjall/garminexport)
* [dbus-python](https://pypi.org/project/dbus-python/)

## Configuration
The tool requires a configuration file stored at $HOME/.config/garmin-connect/config.ini with the following contents:
```
[account]
username=<garmin connect username>
password=<garmin connect password>

[settings]
# Optional, time zone in which the Garmin device is used.
# Default is 'Europe/Berlin'
timezone=Europe/Berlin

# Model name of the USB mass storage provided by the Garmin device
garmin_model=FR110 Flash

# Optional, directory on the USB mass storage containing the activities (as .fit files).
# Default is 'Garmin/Activities'
activities_dir=Garmin/Activities
```

## Installation
Run the following command:
```
python3 setup.py install
```

## How it works
The tool uses the [Udisks2 D-Bus API](http://storaged.org/doc/udisks2-api/latest/) to scan for a Forerunner device connected via USB. If not already mounted, it mounts the file system found
on the device and scans for activities (.fit files) which are not already uploaded to Garmin Connect.
When the upload is finished, the file system is automatically unmounted.

## Usage
Run ```./garmin-uploader --help``` for usage information.