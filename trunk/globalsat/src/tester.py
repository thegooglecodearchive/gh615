from gh615 import *

command = raw_input("What do you want to do? [a]=get list of all tracks [b]=export a single track [c]=export all tracks").strip()

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
    waypoint = {
        'latitude' : '48052725',
        'longitude': '8211262',
        'altitude' : '985',
        'title'    : '003000',
        'type'     : '19'
    };
    waypoint2 = {
        'latitude' : '40052725',
        'longitude': '8011262',
        'altitude' : '100',
        'title'    : 'wurst1',
        'type'     : '12'
    };
    setWaypoints([waypoint,waypoint2])