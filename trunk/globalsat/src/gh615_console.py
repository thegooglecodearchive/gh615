from gh615_oo import *

gh615 = gh615()

def choose():
    print "What do you want to do?\n [a]=get list of all tracks\n [b]=export a single track\n [c]=export all tracks\n [d]=download waypoints\n [e]=upload waypoints\n [ff]=format tracks"
    command = raw_input("=>").strip()
    
    if command == "a":
        print "Getting tracklist"
        tracks = gh615.getTracklist()
        
        #display
        row = string.Template('$id | $date | $distance | $calories | $topspeed | $trackpoints')
        print 'id |         date        | distance | calories | topspeed | trackpoints'
        for track in tracks:
            print row.substitute(id='%02d'%track['id'], date=track['date'], distance='%08d'%track['distance'], calories='%08d'%track['calories'], topspeed='%08d'%track['topspeed'], trackpoints='%08d'%track['trackpoints'])
        choose()
    
    elif command == "b":
        print "Download a track"
        trackId = raw_input("enter trackID(s) [space delimited] ").strip()
        trackIds = trackId.split(' ');
        tracks = gh615.getTracks(trackIds)
        
        format = raw_input("Choose output format: [c]=console [gpx]=gpx [csv]=csv ").strip()    
        gh615.exportTracks(tracks,format)
        choose()
        
    elif command == "c":
        print "Download all tracks"
        allTracks = gh615.getTracklist()
        ids = list()
        for track in allTracks:
            ids.append(track['id'])

        tracks = gh615.getTracks(ids)

        gh615.exportTracks(tracks,'gpx')
        choose()
        
    elif command == "d":
        waypoints = gh615.getWaypoints()    
        gh615.exportWaypoints(waypoints)
        choose()
        
    elif command == "e":
        waypoints = gh615.importWaypoints()
        gh615.setWaypoints(waypoints)
        choose()
        
    elif command == "ff":
        warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
        gh615.formatTracks()
        choose()
        
    else:
        print "whatever"
        choose()
        
choose()