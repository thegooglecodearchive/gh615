from gh615 import *

gh615 = gh615()

def choose():    
    print "\n What do you want to do?\n [a]=get list of all tracks\n [b]=export a single track\n [c]=export all tracks\n [d]=upload tracks\n [e]=download waypoints\n [f]=upload waypoints\n -------------------\n [gg]=format tracks\n [h]=usb connection test\n [i]=get device information\n -------------------\n [q]=quit"
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
        
        print 'available exportFormats:'
        for format in gh615.getExportFormats():
            print "["+format['filename']+"] = "+format['nicename']
        
        format = raw_input("Choose output format: ").strip()
        format = gh615.getExportFormat(format)
        
        merge = False
        if format['hasMultiple']:
            merge = raw_input("Do you want to merge all tracks into a single file? [y/n]: ").strip()
            merge = (False,True)[merge == 'y']
        
        results = gh615.exportTracks(tracks,format['filename'], merge)

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
        print "Upload Tracks"
        
        files = glob.glob(os.path.join(gh615.getAppPrefix(),"import","*.gpx"))
        for i,format in enumerate(files):
            (filepath, filename) = os.path.split(format)
            #(shortname, extension) = os.path.splitext(filename)
            print '['+str(i)+'] = '+ filename
        
        fileId = raw_input("enter number(s) [space delimited] ").strip()
        fileIds = fileId.split(' ');
        
        filesToBeImported = []
        for fileId in fileIds:
            filesToBeImported.append(files[int(fileId)])
                
        tracks = gh615.importTracks(filesToBeImported)
        results = gh615.setTracks(tracks)
        print 'successfully uploaded tracks ', str(results)
        choose()
        
    elif command == "e":
        print "Download Waypoints"
        waypoints = gh615.getWaypoints()    
        results = gh615.exportWaypoints(waypoints)
        print 'exported Waypoints to', results
        choose()
        
    elif command == "f":
        print "Upload Waypoints"
        waypoints = gh615.importWaypoints()
        results = gh615.setWaypoints(waypoints)
        print 'Imported Waypoints', results
        choose()
        
    elif command == "gg":
        warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
        results = gh615.formatTracks()
        print 'Formatted all Tracks:', results
        choose()
        
    elif command == "h":
        print 'Testing serial port connectivity'
        print 'Autodetecting serial port'
        #gh615.diagnostic()
        ports = gh615.getSerialPort()
        if ports:
            print 'the most likely port your unit is connected to is ', ports[0]
            prompt = raw_input("do you want to use "+ports[0]+" for this session instead of the port in the config.ini? [y,n]: ").strip()    
            if prompt == 'y':
                gh615.config.set('serial','comport',ports[0])
                
                prompt = raw_input("do you want to use "+ports[0]+" as your permanent port? [y,n]: ").strip()
                if prompt == 'y':
                    f = open(os.path.join(gh615.getAppPrefix(),'config.ini'),"w")
                    gh615.config.write(f)
                    f.close()
        else:
            print 'no suitable ports found'
        choose()
    
    elif command == "i":
        print gh615.getUnitInformation()
        choose()
    
    elif command == "test":
        '''test stuff here'''
        gh615.unknown()
    
    elif command == "q":
        sys.exit()
    
    else:
        print "whatever"
        choose()
        
choose()