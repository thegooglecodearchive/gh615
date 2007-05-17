from gh615 import *


print "What do you want to do?\n [a]=get list of all tracks\n [b]=export a single track\n [c]=export all tracks\n [d]=import waypoints\n [e]=export waypoints\n [ff]=format tracks"
command = raw_input("=>").strip()

if command == "a":
    print "Getting tracklist"
    tracks = getTracklist()
    print tracks

elif command == "b":
    print "Download a track"
    trackId = raw_input("enter trackID(s) [space delimited] ").strip()
    trackIds = trackId.split(' ');
    tracks = getTracks(trackIds)
    
    format = raw_input("Choose output format: [c]=console [gpx]=gpx [csv]=csv ").strip()    
    exportTracks(tracks,format)
    
elif command == "c":
    print "Download all tracks"
    allTracks = getTracklist()
    ids = list()
    for track in allTracks:
        ids.append(track['id'])
    print ids
    
    time.sleep(2)
    tracks = getTracks(ids)
    
    exportTracks(tracks,'csv')
    
elif command == "d":
    waypoints = getWaypoints()    
    exportWaypoints(waypoints)
    
elif command == "e":
    waypoints = importWaypoints()
    setWaypoints(waypoints)
    
elif command == "ff":
    warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
    formatTracks()
    
else:
    print "whatever"