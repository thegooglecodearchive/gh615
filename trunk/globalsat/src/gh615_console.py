import sys
from optparse import OptionParser
from string import Template

from gh615 import gh615

gh615 = gh615()

def tracklist():
    tracks = gh615.getTracklist()
    #display
    if tracks:
        row = Template('$id | $date | $distance | $calories | $topspeed | $trackpoints')
        print 'id |         date        | distance | calories | topspeed | trackpoints'
        for track in tracks:
            print row.substitute(id='%02d'%track['id'], date=track['date'], distance='%08d'%track['distance'], calories='%08d'%track['calories'], topspeed='%08d'%track['topspeed'], trackpoints='%08d'%track['trackpoints'])
    else:
        print 'no tracks found'
    pass

def choose():    
    print "\n What do you want to do?\n\
 ------TRACKS-------\n\
 [a]=get list of all tracks\n\
 [b]=export a single track\n\
 [c]=export all tracks\n\
 [d]=upload tracks\n\
 -----WAYPOINTS-----\n\
 [e]=download waypoints\n\
 [f]=upload waypoints\n\
 -----ETC-----------\n\
 [gg]=format tracks\n\
 [h]=usb connection test\n\
 [i]=get device information\n\
 -------------------\n\
 [q]=quit"
    command = raw_input("=>").strip()
    
    if command == "a":
        print "Getting tracklist"
        tracklist()
        choose()
    
    elif command == "b":
        print "Download track(s)"
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
        tracks = gh615.getAllTracks()
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
        pass
        choose()
        
    elif command == "gg":
        print "Format all Tracks"
        warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
        results = gh615.formatTracks()
        print 'Formatted all Tracks:', results
        choose()
        
    elif command == "h":
        print 'Testing serial port connectivity'
        print 'Autodetecting serial port'
        ports = gh615.getSerialPort()
        if ports:
            print 'the most likely port your unit is connected to is ', ports[0]
            prompt = raw_input("do you want to use "+ports[0]+" for this session instead of the port in the config.ini? [y,n]: ").strip()    
            if prompt == 'y':
                gh615.config.set('serial','comport',ports[0])
                
                prompt = raw_input("do you want to use "+ports[0]+" as your permanent port? [y,n]: ").strip()
                if prompt == 'y':
                    f = open(gh615.getAppPrefix('config.ini'),"w")
                    gh615.config.write(f)
                    f.close()
        else:
            print 'no suitable ports found'
        choose()
    
    elif command == "i":
        print gh615.getUnitInformation()
        choose()
    
    elif command == "test":
        gh615.unknown()
    
    elif command == "q":
        sys.exit()
    
    else:
        print "whatever"
        choose()


def main():  
    #use standard console interface
    if not sys.argv[1:]:
        choose()
    #parse command line args
    else:
        usage = 'usage: %prog arg [options]'
        description = 'Command Line Interface for GH-615 Python interface, for list of args see the README'
        parser = OptionParser(usage, description=description)
        #parser.add_option("-a", "--tracklist", help="output a list of all tracks")
        #parser.add_option("-b", "--download-track")
        #parser.add_option("-c", "--download-all-tracks")
        #parser.add_option("-d", "--upload-track")
        #parser.add_option("-e", "--download-waypoints")
        #parser.add_option("-f", "--upload-waypoints")  
        #parser.add_option("-gg","--format-tracks") 
        #parser.add_option("-h", "--connection-test")
        #parser.add_option("-i", "--unit-information") 
        
        parser.set_defaults(
            format="gpx",
            merge=False,
            input=None,
            output=None,
        )
        
        parser.add_option("-t", "--track", help="a track id",  action="append", dest="tracks", type="int")
        parser.add_option("-f", "--format", help="the format to export to (default: %default)", dest="format", choices=[format['filename'] for format in gh615.getExportFormats()])
        parser.add_option("-m", "--merge", help="merge into single file?", dest="merge", action="store_true")
        parser.add_option("-c", "--com", dest="com",  help="the comport to use")
        
        parser.add_option("-i", "--input", help="input file(s)", action="append", dest="input")
        parser.add_option("-o", "--output", help="the path to output to", dest="output")
        
        (options, args) = parser.parse_args()
        
        if len(args) != 1:
            parser.error("incorrect number of arguments")
        
        #set serial port
        if options.com:
            gh615.config.set('serial','comport',options.com)
        
        if args[0] == "a":
            tracklist()
            
        if args[0] == "b":            
            if not options.tracks:
                parser.error("use option '--track' to select track")
                
            tracks = gh615.getTracks(options.tracks)         
            gh615.exportTracks(tracks, options.format, options.merge, path=options.output)
            
        if args[0] == "c":        
            tracks = gh615.getAllTracks()
            results = gh615.exportTracks(tracks, options.format, path=options.output)
            
        if args[0] == "d":
            if not options.input:
                parser.error("use option '--input' to select files")
            tracks = gh615.importTracks(options.input)
            results = gh615.setTracks(tracks)
        
        if args[0] == "e":
            waypoints = gh615.getWaypoints()    
            results = gh615.exportWaypoints(waypoints, path=options.output)
            
        if args[0] == "f":
            waypoints = gh615.importWaypoints(path=options.input[0])
            results = gh615.setWaypoints(waypoints)
            print 'Imported Waypoints', results
            
        if args[0] == "gg":
            warning = raw_input("warning, FORMATTING ALL TRACKS").strip()
            results = gh615.formatTracks()
                    
        if args[0] == "i":
            print gh615.getUnitInformation()
            
        else:
            print "no valid argument, see README"
            
        #if options.tracks:
        #    print options.tracks

        
if __name__ == "__main__":
    main()