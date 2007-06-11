from gh615 import *

gh615 = gh615()

def choose():
    print "\n What do you want to do?\n [a]=get list of all tracks\n [b]=export a single track\n [c]=export all tracks\n [d]=download waypoints\n [e]=upload waypoints\n [ff]=format tracks\n [q]=quit"
    command = raw_input("=>").strip()
    
    if command == "a":
        print "Getting tracklist"
        tracks = gh615.getTracklist()
        
        #display
        if tracks:
            row = string.Template('$id | $date | $distance | $calories | $topspeed | $trackpoints')
            print 'id |         date        | distance | calories | topspeed | trackpoints'
            for track in tracks:
                print row.substitute(id='%02d'%track['id'], date=track['date'], distance='%08d'%track['distance'], calories='%08d'%track['calories'], topspeed='%08d'%track['topspeed'], trackpoints='%08d'%track['trackpoints'])
        else:
            print 'no tracks found'
        choose()
    
    elif command == "b":
        print "Download a track"
        trackId = raw_input("enter trackID(s) [space delimited] ").strip()
        trackIds = trackId.split(' ');
        tracks = gh615.getTracks(trackIds)
        
        format = raw_input("Choose output format: [c]=console [gpx]=gpx [csv]=csv ").strip()    
        results = gh615.exportTracks(tracks,format)
        print 'exported tracks', results
        choose()
        
    elif command == "c":
        print "Download all tracks"
        allTracks = gh615.getTracklist()
        ids = list()
        for track in allTracks:
            ids.append(track['id'])

        tracks = gh615.getTracks(ids)

        results = gh615.exportTracks(tracks,'gpx')
        print 'exported tracks', results
        choose()
        
    elif command == "d":
        print "Export Waypoints"
        waypoints = gh615.getWaypoints()    
        results = gh615.exportWaypoints(waypoints)
        print 'exported Waypoints to', results
        choose()
        
    elif command == "e":
        print "Import Waypoints"
        waypoints = gh615.importWaypoints()
        results = gh615.setWaypoints(waypoints)
        print 'Imported Waypoints', results
        choose()
        
    elif command == "ff":
        warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
        results = gh615.formatTracks()
        print 'Formatted all Tracks:', results
        choose()
    
    elif command == "q":
        sys.exit()
    
    else:
        print "whatever"
        choose()
        
choose()