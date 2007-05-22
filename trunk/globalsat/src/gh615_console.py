from gh615 import *

def choose():
    print "What do you want to do?\n [a]=get list of all tracks\n [b]=export a single track\n [c]=export all tracks\n [d]=download waypoints\n [e]=upload waypoints\n [ff]=format tracks"
    command = raw_input("=>").strip()
    
    if command == "a":
        print "Getting tracklist"
        tracks = getTracklist()
        
        #display
        row = string.Template('$id | $date | $distance | $calories | $topspeed | $trackpoints')
        print 'id |         date        | distance | calories | topspeed | trackpoints'
        print '00 | 2007-05-16 20:08:18 | 000015   | 0000     | 0139     | 00022'
        for track in tracks:
            print row.substitute(id='%02d'%track['id'], date=track['date'], distance='%08d'%track['distance'], calories='%08d'%track['calories'], topspeed='%08d'%track['topspeed'], trackpoints='%08d'%track['trackpoints'])
        choose()
    
    elif command == "b":
        print "Download a track"
        trackId = raw_input("enter trackID(s) [space delimited] ").strip()
        trackIds = trackId.split(' ');
        tracks = getTracks(trackIds)
        
        format = raw_input("Choose output format: [c]=console [gpx]=gpx [csv]=csv ").strip()    
        exportTracks(tracks,format)
        choose()
        
    elif command == "c":
        print "Download all tracks"
        allTracks = getTracklist()
        ids = list()
        for track in allTracks:
            ids.append(track['id'])
        print ids
        time.sleep(2)
        tracks = getTracks(ids)

        exportTracks(tracks,'gpx')
        choose()
        
    elif command == "d":
        waypoints = getWaypoints()    
        exportWaypoints(waypoints)
        choose()
        
    elif command == "e":
        waypoints = importWaypoints()
        setWaypoints(waypoints)
        choose()
        
    elif command == "ff":
        warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
        formatTracks()
        choose()
        
    else:
        print "whatever"
        choose()
        
choose()