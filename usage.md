# command line only #

At the current time, this utility is command line only, meaning there is no Graphical User Interface. That should not keep you from trying it out, as the command line is very intuitive for the basic operations supported.

# Configuration #

Configuration is done via the `config.ini` file

# Usage #

Double click `gh615_console.exe` and follow the instructions

> - or -

execute with the following arguments:

## arguments: ##
  * **a**: get a list of all tracks - no options
  * **b**: download track(s) - -t, -f, -m, -o
  * **c**: download all tracks - -f, -m, -o
  * **d**: upload tracks - -i
  * **e**: download waypoints - -o
  * **f**: upload waypoints - -i
  * **gg**: format all tracks - no options
  * **h**: connection test - no options
  * **i**: unit information - no options

## explanation of options ##
  * **-t, --track**: id of a track to be downloaded (can be used multiple times)
  * **-f, --format**: export-format that will be used (default can be set in config.ini)
  * **-m, --merge**: whether the tracks should be merged into one file (only if supported by format) (default: false)
  * **-o, --output**: path to directory where exported files will be stored (default: /export)
  * **-i, --input**: files used for input (either formatted waypoints.txt of gpx file)

  * **-v, --firmware**: set to 1 if you have the old firmware without lap support (originally GH-615); 2 for the new firmware with lap-support  (overwrites the value specified in config.ini)
  * **-c, --com**: set the comport that will be used for connecting (overwrites the value specified in config.ini)

# examples #

`gh615_console.exe b -t 0 -t 1 -f gpx -o c://` Saves tracks 0 and 1 in the "gpx" format to the root of c:

`gh615_console.exe c -f fitlog -m` Saves all tracks in the "fitlog" format to the "export" directory of the running application

`gh615_console.exe d -i c://track1.gpx -i c://track2.gpx` Uploads both gpx-files


## Working with Waypoints ##
The waypoint implementation is still kind of sketchy at the moment.

Currently this is the way to do it:

  1. Download trackpoints (option `d`); waypoints.txt will be created in the root.
  1. Edit waypoints.txt; if you change the title of a waypoint a new waypoint will be created instead of updating the exisiting one
  1. Upload trackpoints (option `e`)

### structure of waypoints.txt ###
waypoints.txt is a simple dump of a list of dictionaries, which looks like this:

```
[
{'latitude': '48.052148', 'longitude': '8.210360', 'altitude': 583, 'type': 55, 'title': 'waypo1'},
{'latitude': '50.052148', 'longitude': '5.210360', 'altitude': 883, 'type': 54, 'title': 'waypo2'}
]
```

#### fields ####
most fields are self explanatory, just note that the `title` can not exceed 6 characters. `type` assigns the icon that is display on the map of the gh615.

##### available icon types #####

  * 0:  'DOT',
  * 1:  'HOUSE',
  * 2:  'TRIANGLE',
  * 3:  'TUNNEL',
  * 4:  'CROSS',
  * 5:  'FISH',
  * 6:  'LIGHT',
  * 7:  'CAR',
  * 8:  'COMM',
  * 9:  'REDCROSS',
  * 10: 'TREE',
  * 11: 'BUS',
  * 12: 'COPCAR',
  * 13: 'TREES',
  * 14: 'RESTAURANT',
  * 15: 'SEVEN',
  * 16: 'PARKING',
  * 17: 'REPAIRS',
  * 18: 'MAIL',
  * 19: 'DOLLAR',
  * 20: 'GOVOFFICE',
  * 21: 'CHURCH',
  * 22: 'GROCERY',
  * 23: 'HEART',
  * 24: 'BOOK',
  * 25: 'GAS',
  * 26: 'GRILL',
  * 27: 'LOOKOUT',
  * 28: 'FLAG',
  * 29: 'PLANE',
  * 30: 'BIRD',
  * 31: 'DAWN',
  * 32: 'RESTROOM',
  * 33: 'WTF',
  * 34: 'MANTARAY',
  * 35: 'INFORMATION',
  * 36: 'BLANK'