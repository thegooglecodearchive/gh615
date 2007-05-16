from gh615 import *

command = raw_input("What do you want to do? [a]=get list of all tracks [b]=export a track ").strip()

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
    
else:
    print sys.path[0]+'\\exportTemplates\\'