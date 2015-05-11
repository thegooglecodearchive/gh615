# Build 186 #
  * added a webfrontend for editing waypoints

# Build 168 #
  * fixed several GH615 compatibility issues ([issue21](https://code.google.com/p/gh615/issues/detail?id=21))
  * changed UI to ask less question while being more flexible ([issue22](https://code.google.com/p/gh615/issues/detail?id=22))(thanks Zingo)

# Build 158 #
  * completely refactored everything
  * added support for new GH625 Firmware, which supports laps
  * uses Decimals instead of floats internally
  * ability to delete all waypoints
  * serial port communication improved

# Build 128 #
  * No more crashes when exporting single tracks
  * waypoint type is now being correctly set when uploading waypoints

# Build 118 #
  * added command line interface, see [usage](usage.md)
  * More than 14 Waypoints can be uploaded
  * Corrected Latitude for Trackpoints in the southern hemisphere
  * added "fitlog" export format (thanks Zingo)

# Build 104 #
  * made it possible to upload tracks (currently only from gpx-files) just drop files named `*.gpx` with one (or multiple) tracks in the import directory and use option `d` from the main menu
  * added function to get user and device Information (not very useful yet)
  * made paths everywhere platform independant (sorry for that)

# Build 98 #
  * multiple tracks can now be merged into a single output file
  * added formats.ini for better configuration of exportFormats
  * fixed waypoint uploading: more than 3 waypoints can be uploaded
  * added detection of comport settings

# Build 56 #
  * waypoint coordinates can now be negativ
  * added google maps exportTemplate
  * exportTemplates can be extended using preCalculations