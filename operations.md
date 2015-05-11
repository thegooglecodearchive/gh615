# Implemented #
  * download a list of all tracks
  * download tracks
  * upload tracks
  * delete all tracks
  * download waypoints
  * upload waypoints
  * delete all waypoints
  * get user Information (including waypoint- and track-count)
  * get live NMEA data

# Not implemented #
  * delete individual track/waypoint using software

# functions from GH615\_PCAPI.dll #

the original globalsat software utilizes a GH615\_PCAPI.dll, which has references to the following commands (thanks RunOway):

## general functions ##
  * OpenPortForGPS(HWND hWnd,TCHAR ComPort?,UINT BaudRate?);
  * OpenPortForGPS\_EX(HWND hWnd,TCHAR ComPort?,UINT BaudRate?,UINT Timeout);
  * ClosePortForGPS();
  * UpgradeFirmware?(TCHAR filename);
  * GetSystemConfiguration?(SystemConfiguration? pSystemConfiguration);
  * SendNEMACommand(TCHAR szCommand);
  * OpenTraceLog?();
  * CloseTraceLog?();

## track related ##
  * GetTrackFileCount?(UINT pCountofTrackFile);
  * GetTrackPointFileList?(TrackPointFileHeader? pTrackFileHeader, UINT pNumofTracks);
  * RequsetTrackPointFilesByIndex?(UINT id, UINT NumofFiles?);
  * RequsetCurrentTrackPointFile?();
  * RequsetFirstTrackPointFile?();
  * RequsetNextTrackPointFile?();
  * ReSendTrackPointFile?();
  * SendTrackPointFile?(TrackPointFile? pTrackPointFile, UINT pNumofPoints);
  * ReceiveTrackPointFile?(TrackPointFile? pTrackPointFile, UINT pNumofPoints);
  * DelAllTrackFiles?();
  * DelTrackFiles?(UINT id, UINT NumofFiles?);

## waypoint related ##
  * GetWayPointFileCount?(UINT pCountofWayPointFile);
  * RequsetWayPointFile?();
  * RequestNextWayPointFile?();
  * SendWayPointFile?(WayPoints? pWayPoints, UINT pNumofWayPoints);
  * ReceiveWayPointFile?(WayPoints? pWayPoints, UINT pNumofWayPoints);