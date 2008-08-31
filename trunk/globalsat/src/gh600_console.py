import glob, os, sys
from optparse import OptionParser

from gh600 import GH600, ExportFormat, Utilities

gh = GH600()

def tracklist():
    tracks = gh.getTracklist()
    #display
    if tracks:
        print 'id         date        distance calories topspeed trkpnts  laps'
        for track in tracks:
            print str(track)
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
 [hh]=format waypoints\n\
 [j]=get device information\n\
 -------------------\n\
 [q]=quit"
    command = raw_input("=>").strip()
    
    if command == "a":
        print "Getting tracklist"
        tracklist()
    
    elif command == "b":
        print "Download track(s)"
        trackId = raw_input("enter trackID(s) [space delimited] ").strip()
        trackIds = trackId.split(' ');
        tracks = gh.getTracks(trackIds)
        
        print 'available exportFormats:'
        for format in gh.getExportFormats():
            print "[%s] = %s" % (format.name, format.nicename)
        
        format = raw_input("Choose output format: ").strip()
        
        merge = False
        ef = ExportFormat(format)
        if ef.hasMultiple and len(tracks) > 1:
            merge = raw_input("Do you want to merge all tracks into a single file? [y/n]: ").strip()
            merge = True if merge == "y" else False
        
        ef.exportTracks(tracks, merge = merge)
        print 'exported %d tracks' % len(tracks)
        
    elif command == "c":
        tracks = gh.getAllTracks()
        ef = ExportFormat('gpx')
        results = ef.exportTracks(tracks, 'gpx')
        print 'exported tracks', results
        
    elif command == "d":
        print "Upload Tracks"
        files = glob.glob(os.path.join(Utilities.getAppPrefix(),"import","*.gpx"))
        for i,format in enumerate(files):
            (filepath, filename) = os.path.split(format)
            #(shortname, extension) = os.path.splitext(filename)
            print '[%i] = %s' % (i, filename)
        
        fileId = raw_input("enter number(s) [space delimited] ").strip()
        fileIds = fileId.split(' ');
        
        filesToBeImported = []
        for fileId in fileIds:
            filesToBeImported.append(files[int(fileId)])
                    
        tracks = gh.importTracks(filesToBeImported)        
        results = gh.setTracks(tracks)
        print 'successfully uploaded tracks ', str(results)
        
    elif command == "e":
        print "Download Waypoints"
        waypoints = gh.getWaypoints()    
        results = gh.exportWaypoints(waypoints)
        print 'exported Waypoints to', results
        
    elif command == "f":
        print "Upload Waypoints"
        waypoints = gh.importWaypoints()        
        results = gh.setWaypoints(waypoints)
        print 'Imported Waypoints', results
        
    elif command == "gg":
        print "Delete all Tracks"
        warning = raw_input("warning, DELETING ALL TRACKS").strip()
        results = gh.formatTracks()
        print 'Deleted all Tracks:', results
        
    elif command == "hh":
        print "Delete all Waypoints"
        warning = raw_input("WARNING DELETING ALL WAYPOINTS").strip()
        results = gh.formatWaypoints()
        print 'Formatted all Waypoints:', results
    
    elif command == "i":
        unit = gh.getUnitInformation()
        print "* %s waypoints on watch" % unit['waypoint_count']
        print "* %s trackpoints on watch" % unit['trackpoint_count']
    
    elif command == "x":
        print gh.getNmea()
    
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
        parser = OptionParser(usage, description = description)
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
            format = "gpx",
            merge  = False,
            input  = None,
            output = None,
        )
        
        parser.add_option("-t", "--track", help="a track id",  action="append", dest="tracks", type="int")
        parser.add_option("-f", "--format", help="the format to export to (default: %default)", dest="format", choices=[format['filename'] for format in gh.getExportFormats()])
        parser.add_option("-m", "--merge", help="merge into single file?", dest="merge", action="store_true")
        parser.add_option("-c", "--com", dest="com",  help="the comport to use")
        parser.add_option("-fi", "--firmware", dest="firmware", type="int", choices=[1,2], help="firmware of your GH: (1 for old, 2 for new)")
        
        
        parser.add_option("-i", "--input", help="input file(s)", action="append", dest="input")
        parser.add_option("-o", "--output", help="the path to output to", dest="output")
        
        (options, args) = parser.parse_args()
        
        if len(args) != 1:
            parser.error("incorrect number of arguments")
        
        #set firmware version
        if options.firmware:
            gh.config.set('general', 'firmware', options.firmware)
        
        #set serial port
        if options.com:
            gh.config.set('serial', 'comport', options.com)
        
        if args[0] == "a":
            tracklist()
            
        if args[0] == "b":            
            if not options.tracks:
                parser.error("use option '--track' to select track")
                
            tracks = gh.getTracks(options.tracks)
            ef = ExportFormat(options.format)
            ef.exportTracks(tracks, merge = options.merge, path = options.output)
            
        if args[0] == "c":        
            tracks = gh.getAllTracks()
            ef = ExportFormat(options.format)
            ef.exportTracks(tracks, merge = options.merge, path = options.output)
            
        if args[0] == "d":
            if not options.input:
                parser.error("use option '--input' to select files")
            tracks = gh.importTracks(options.input)
            results = gh.setTracks(tracks)
        
        if args[0] == "e":
            waypoints = gh.getWaypoints()    
            results = gh.exportWaypoints(waypoints, path=options.output)
            
        if args[0] == "f":
            waypoints = gh.importWaypoints(path=options.input[0])
            results = gh.setWaypoints(waypoints)
            print 'Imported Waypoints', results
            
        if args[0] == "gg":
            warning = raw_input("warning, DELETING ALL TRACKS").strip()
            results = gh.formatTracks()
            
        if args[0] == "hh":
            warning = raw_input("warning, DELETING ALL WAYPOINTS").strip()
            results = gh.formatWaypoints()
                    
        if args[0] == "i":
            return gh.getUnitInformation()
            
        else:
            parser.error("invalid argument, try -h or see README for help")
        
if __name__ == "__main__":
    main()