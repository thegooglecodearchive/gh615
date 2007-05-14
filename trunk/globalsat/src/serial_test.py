import serial, string, datetime, time, sys
from stpy import Template

commands = {'get_tracklist' : '0x0200017879', 
            'get_waypoints' : '555-1212', 
            'get_track' : '553-1337'}

def chop(s, chunk):
    return [s[i*chunk:(i+1)*chunk] for i in range((len(s)+chunk-1)/chunk)]

def dec2hex(n):
    return "%X" % n
 
def hex2dec(s):
    return int(s, 16)

def hex2chr(hex):
    out = ''
    debug = ''
    for i in range(0,len(hex),2):
        out += chr(int('0x'+hex[i:i+2],16))
        debug += str(hex[i:i+2])
    print 'debug', str(debug)
    return out

def connectSerial():
    ser = serial.Serial(port='COM1',baudrate=56000,timeout=2)
    print ser.portstr
    return ser
    

command = raw_input("What do you want to do? [a]=get list of all tracks [b]=export a track ").strip()

if command == "a":
    print "Getting tracklist"
    
    #connect serial connection
    ser = connectSerial()
    #write tracklisting command to serial port
    ser.write(hex2chr('0200017879'))
    #wait for response
    time.sleep(2)
    print ser.inWaiting()
    #tracklist = ser.read(512)
    tracklist = ser.readline()
    ser.close()
    
    #trim header/teil
    tracklist = tracklist[6:-2]
    #seperate tracks
    tracks = chop(tracklist,48)
    
    #if tracks exist    
    if tracks > 1:    
        tracksParsed = list()
        for track in tracks:
            date = str(datetime.datetime(2000+hex2dec(track[0:2]), hex2dec(track[2:4]), hex2dec(track[4:6]), hex2dec(track[6:8]), hex2dec(track[8:10]), hex2dec(track[10:12])))
            tracksParsed.append({
                'date': date,
                'duration':hex2dec(track[12:20]),
                'distance':hex2dec(track[20:28]),
                'calories':hex2dec(track[28:32]),
                'topspeed':hex2dec(track[32:36]),
                'trackpoints':hex2dec(track[36:44]),
                'id':hex2dec(track[44:48])
            });
        
        print tracksParsed
     
    #if no tracks exist
    else:
        print "Keine Tracks gefunden"

elif command == "b":
    print "Download a track"
    trackId = raw_input("enter trackID(s) [space delimited] ").strip()

    trackIds = trackId.split(' ');
    #convert inputted track ids to hex-4-digit format
    for i in range(len(trackIds)):
        trackIds[i] = '%04X' % int(trackIds[i])
    
    #calculate payload
    payload = '%04X' % ((len(trackIds)*512)+896)
    pay1 = hex2dec(payload[0:2])
    pay2 = hex2dec(payload[2:4])
    
    #number of tracks
    numberOfTracks = '%04X' % len(trackIds)
    num1 = hex2dec(numberOfTracks[0:2])
    num2 = hex2dec(numberOfTracks[2:4])
    
    #calculate checksum
    xorsum = 0
    for i in range(0,len(''.join(trackIds)),2):
        xorsum = int(''.join(trackIds)[i:i+2],16)^xorsum
    checksum = dec2hex(pay1^pay2^num1^num2^xorsum)
      
    #connect serial connection
    ser = connectSerial()
    #write request to serial port
    ser.write(hex2chr('0200'+payload+numberOfTracks+' '.join(trackIds)+checksum))
    #wait for response
    time.sleep(2)
    print ser.inWaiting()
    #read trackpoints into var
    #TODO: read at most 512(?)byte, then send command to send next payload
    track = ser.readline()
    #close serial connection
    ser.close()
    
    #trim to trackheader
    trackinfo = track[6:52]
    trackinfo = {
        'date':     datetime.datetime(2000+hex2dec(trackinfo[0:2]), hex2dec(trackinfo[2:4]), hex2dec(trackinfo[4:6]), hex2dec(trackinfo[6:8]), hex2dec(trackinfo[8:10]), hex2dec(trackinfo[10:12])),
        'duration': hex2dec(trackinfo[12:20]),
        'distance': hex2dec(trackinfo[20:28]),
        'calories': hex2dec(trackinfo[28:32]),
        'topspeed': hex2dec(trackinfo[32:36])
    }
    #trim to trackpoints
    trackpoints = track[58:-2]
    #seperate trackpoints
    trackpoints = chop(trackpoints,30)
    if (len(trackpoints) > 0):
        timeFromStart = trackinfo['date']
        #init trackpoints list
        trackpointsParsed = list()
        #loop over trackpoints and output
        for trackpoint in trackpoints: 
            timeFromStart = timeFromStart + datetime.timedelta(milliseconds=(hex2dec(trackpoint[26:30])*100)) 
            trackpointsParsed.append({
                'latitude': hex2dec(trackpoint[0:8]),
                'longitude':hex2dec(trackpoint[8:16]),
                'altitude': hex2dec(trackpoint[16:20]),
                'speed':    hex2dec(trackpoint[20:24]),
                'heartrate':hex2dec(trackpoint[24:26]),
                'interval': hex2dec(trackpoint[26:30]),
                'date':     timeFromStart
            });    
        
        #output format
        format = raw_input("Choose output format: [c]=console [gpx]=gpx [csv]=csv ").strip()    
        if format != 'c':
            #read template
            fileHandle = open(sys.path[0]+'\\exportTemplates\\'+format+'.txt')
            templateImport = fileHandle.read()
            fileHandle.close() 
            #parse template
            template = Template(templateImport)
            file = template.render(trackpoints = trackpointsParsed)
            #prompt for filename
            filename = raw_input("Enter a filename: ").strip()
            filename = sys.path[0]+'\\export\\'+filename+'.'+format
            #write to file
            fileHandle = open(filename,'wt')
            fileHandle.write(file)
            fileHandle.close()
            print 'Successfully wrote', filename
            
        elif format == 'c':
            print trackpointsParsed
    else:
        print 'Error fetching track'
    
else:
    print sys.path[0]+'\\exportTemplates\\'