import serial, string, datetime, time
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

command = raw_input("What do you want to do?:")
command = command.strip()

if command == "a":
    print "Getting tracklist"
    
    ser = serial.Serial(port='COM1',baudrate=56000,timeout=2)
    print ser.portstr
    ser.write(hex2chr('0200017879'))
    command = raw_input("waiting")
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
            dated = str(datetime.datetime(2000+hex2dec(track[0:2]), hex2dec(track[2:4]), hex2dec(track[4:6]), hex2dec(track[6:8]), hex2dec(track[8:10]), hex2dec(track[10:12])))
            tracksParsed.append({
                'dated': dated,
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
    trackId = raw_input("enter trackID(s) [space delimited]").strip()

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
    ser = serial.Serial(port='COM1',baudrate=56000,timeout=2)
    print ser.portstr
    #write request to serial port
    ser.write(hex2chr('0200'+payload+numberOfTracks+' '.join(trackIds)+checksum))
    waiting = raw_input("waiting")
    print ser.inWaiting()
    #read trackpoints into var
    track = ser.readline()
    #close serial connection
    ser.close()
    
    #trim to trackheader
    trackinfo = track[6:52]
    trackinfo = {
        'dated':    datetime.datetime(2000+hex2dec(trackinfo[0:2]), hex2dec(trackinfo[2:4]), hex2dec(trackinfo[4:6]), hex2dec(trackinfo[6:8]), hex2dec(trackinfo[8:10]), hex2dec(trackinfo[10:12])),
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
        #loop over trackpoints and output
        timeFromStart = time.mktime(trackinfo['dated'].timetuple());
        #trackpoints list
        trackpointsParsed = list()
        for trackpoint in trackpoints: 
            timeFromStart = timeFromStart+hex2dec(trackpoint[26:30])/10
            trackpointsParsed.append({
                'latitude':hex2dec(trackpoint[0:8]),
                'longitude':hex2dec(trackpoint[8:16]),
                'altitude':hex2dec(trackpoint[16:20]),
                'speed':hex2dec(trackpoint[20:24]),
                'heartrate':hex2dec(trackpoint[24:26]),
                'interval':hex2dec(trackpoint[26:30]),
                'date':timeFromStart+hex2dec(trackpoint[26:30])/10
            });    
        
        #output format
        format = raw_input("Choose output format: [c]=console [g]=gpx").strip()    
        if format == 'a':
            fileHandle = open('d:/template.gpx.txt')
            templateImport = fileHandle.read()
            fileHandle.close() 
            template = Template(templateImport)
            print template.render(trackpoints = trackpointsParsed)
        elif format == 'b':
            print trackpointsParsed
    else:
        print 'Error fetching track'
    
else:
    '''  
    fileHandle = open('d:/template.gpx.txt')
    templateImport = fileHandle.read()
    fileHandle.close() 
    
    template = Template(templateImport)
    
    file = template.render(
          trackpoints = [
              dict(
                  title='Test',
                  text='Hihi'
              ),
              dict(
                  title='Foobar',
                  text='blub'
              )
          ]
      )

    fileHandle = open('d:/gps.txt','wt')
    fileHandle.write(file)
    fileHandle.close()
    '''
