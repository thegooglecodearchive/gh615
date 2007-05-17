import serial, string, datetime, time, os, sys
from stpy import Template

COMMANDS = {
            'getTracklist'                    : '0200017879',
            'getTracks'                       : '0200%(payload)s%(numberOfTracks)s%(trackIds)s%(checksum)s', 
            'requestNextTrackSegment'         : '0200018180', 
            'requestErrornousTrackSegment'    : '0200018283',
            'formatTracks'                    : '0200037900641E',
            'getWaypoints'                    : '0200017776',
            'setWaypoints'                    : '0200%(payload)s76%(numberOfWaypoints)s%(waypoints)s%(checksum)s',
            'unitInformation'                 : '0200018584'
            }

def getAppPrefix():
    #Return the location the app is running from
    isFrozen = False
    try:
        isFrozen = sys.frozen
    except AttributeError:
        pass
    if isFrozen:
        appPrefix = os.path.split(sys.executable)[0]
    else:
        appPrefix = os.path.split(os.path.abspath(sys.argv[0]))[0]
    return appPrefix

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
    #print 'debug hex2chr ', str(debug)
    return out

def chr2hex(chr):
    out = ''
    debug = ''
    for i in range(0,len(chr)):
        out += '%(#)02X' % {"#": ord(chr[i])}
        debug += '%(#)02X' % {"#": ord(chr[i])}
    #print 'debug chr2hex ', str(debug)
    return out

def checkersum(hex):
    checksum = 0
    for i in range(0,len(hex),2):
        checksum = checksum^int(hex[i:i+2],16)
    return dec2hex(checksum)
    
def parseTrack(hex):
    #create here
    return track

def parseTrackInfo(hex):
    if len(hex) == 44 or len(hex) == 48:
        trackinfo = {
            'date':        datetime.datetime(2000+hex2dec(hex[0:2]), hex2dec(hex[2:4]), hex2dec(hex[4:6]), hex2dec(hex[6:8]), hex2dec(hex[8:10]), hex2dec(hex[10:12])),
            'duration':    hex2dec(hex[12:20]),
            'distance':    hex2dec(hex[20:28]),
            'calories':    hex2dec(hex[28:32]),
            'topspeed':    hex2dec(hex[32:36]),
            'trackpoints': hex2dec(hex[36:44])
        } 
        if len(hex) == 48:
            trackinfo['id'] = hex2dec(hex[44:48])
        return trackinfo
    else:
        print 'incorrect track length', len(hex)
        pass

def parseTrackpoint(hex, timeFromStart = False):
    if len(hex) == 30:
        trackpoint = {
            #'latitude':  float(hex2dec(hex[0:8]))/float(1000000),
            #'longitude': float(hex2dec(hex[8:16]))/float(1000000),
            'latitude'  : '%.6f' % (float(hex2dec(hex[0:8]))/1000000.0),
            'longitude'  : '%.6f' % (float(hex2dec(hex[8:16]))/1000000.0),
            'altitude':  hex2dec(hex[16:20]),
            'speed':     float(hex2dec(hex[20:24]))/float(100),
            'heartrate': hex2dec(hex[24:26]),
            'interval':  hex2dec(hex[26:30]),
        };
        if timeFromStart != False:
            trackpoint['date'] = timeFromStart + datetime.timedelta(milliseconds=(hex2dec(hex[26:30])*100)) 
        return trackpoint
    else:
        print 'incorrect trackpoint length'
        pass
        
def parseTrackpoints(hex, timeFromStart = False):
    trackpoints = chop(hex,30)
    if (len(trackpoints) > 0):
        #init trackpoints list
        ParsedTrackpoints = list()
        #loop over trackpoints and output
        for trackpoint in trackpoints: 
            parsedTrackpoint = parseTrackpoint(trackpoint, timeFromStart)
            ParsedTrackpoints.append(parsedTrackpoint);
            timeFromStart = parsedTrackpoint['date']
        return ParsedTrackpoints

def connectSerial():
    ser = serial.Serial(port='COM1',baudrate=56000,timeout=2)
    print ser.portstr
    return ser

def getTracklist():
    #connect serial connection
    ser = connectSerial()
    #write tracklisting command to serial port
    ser.write(hex2chr(COMMANDS['getTracklist']))
    #wait for response
    time.sleep(1)
    print ser.inWaiting()
    tracklist = chr2hex(ser.readline())
    time.sleep(2)
    ser.close()
    
    #trim header/teil
    tracklist = tracklist[6:-2]
    #seperate tracks
    tracks = chop(tracklist,48)
    #if tracks exist    
    if tracks > 1:    
        tracksParsed = list()
        for track in tracks:
            tracksParsed.append(parseTrackInfo(track));
        print 'number of tracks', len(tracksParsed)
        return tracksParsed 
    #if no tracks exist
    else:
        print "no tracks available"
        pass
    
def getTracks(trackIds):
    #trackIds = trackId.split(' ');
    #convert inputted track ids to hex-4-digit format
    for i in range(len(trackIds)):
        trackIds[i] = '%04X' % int(trackIds[i])
    
    #calculate payload
    payload = '%04X' % ((len(trackIds)*512)+896)   
    #number of tracks
    numberOfTracks = '%04X' % len(trackIds)

    checksum = checkersum(payload+numberOfTracks+''.join(trackIds))
      
    #connect serial connection
    ser = connectSerial()
    #write request to serial port
    ser.write(hex2chr(COMMANDS['getTracks'] % {'payload':payload, 'numberOfTracks':numberOfTracks, 'trackIds': ''.join(trackIds), 'checksum':checksum}))
    #wait for response
    time.sleep(1)

    print 'waiting at start', ser.inWaiting()
    '''
    if len(data) > 4170:
        print 'initial segment to large, quitting'
        end == True
        ser.close()
    '''
    tracks = list()
    track = dict([('trackinfo', dict()), ('trackpoints', list())])
    last = -1
    finished = False;
    while finished == False:
        data = chr2hex(ser.read(2070))
        print 'waiting in loop', ser.inWaiting()
        time.sleep(2)
        #TODO: Kill if data > 2070 
        if data != '8A000000':
            print 'compare', str(last+1)+'/'+str(hex2dec(data[50:54]))
            if (hex2dec(data[50:54]) == last+1):
                #debug
                print 'getting trackpoints', str(hex2dec(data[50:54]))+'-'+str(hex2dec(data[54:58]))
                #check if first segment of track
                if last == -1:
                    #parse trackinfo
                    track['trackinfo'] = parseTrackInfo(data[6:50])
                #parse trackpoints
                track['trackpoints'].extend(parseTrackpoints(data[58:-2], track['trackinfo']['date']))
                #remeber last trackpoint
                last = hex2dec(data[54:58])
                #check if last segment of track
                if len(data) < 4140:
                    #init new track
                    print 'initializd new track'
                    tracks.append(track)
                    track = dict([('trackinfo', dict()), ('trackpoints', list())])
                    last = -1
                
                #request next segment
                ser.write(hex2chr(COMMANDS['requestNextTrackSegment']))
                #take a rest
                time.sleep(1)
            else:
                #re-request last segment again
                print 're-requesting last segment'
                ser.write(hex2chr(COMMANDS['requestErrornousTrackSegment']))
                #take a rest
                time.sleep(1)
        else:
            #received finished sign
            finished = True
            ser.close()
    
    print 'number of tracks', len(tracks)
    return tracks

def exportTracks(tracks, format):
    #read template
    fileHandle = open(getAppPrefix()+'\\exportTemplates\\'+format+'.txt')
    templateImport = fileHandle.read()
    fileHandle.close() 
    for track in tracks:
        #parse template
        template = Template(templateImport)
        file = template.render(trackinfo = track['trackinfo'], trackpoints = track['trackpoints'])
        #prompt for filename
        #filename = raw_input("Enter a filename: ").strip()
        filename = track['trackinfo']['date'].strftime("%Y-%m-%d_%H-%M-%S")
        filename = getAppPrefix()+'\\export\\'+filename+'.'+format
        #write to file
        fileHandle = open(filename,'wt')
        fileHandle.write(file)
        fileHandle.close()
        print 'Successfully wrote', filename
        
def formatTracks():
    #connect serial connection
    ser = connectSerial()
    #write tracklisting command to serial port
    ser.write(hex2chr(COMMANDS['formatTracks']))
    #wait for response
    time.sleep(12)
    response = chr2hex(ser.read(4070))
    ser.close()
    
    if response == '79000000':
        return true
    else:
        return false

def parseWaypoint(hex):
    if len(hex) == 36:
        waypoint = {
            #if float()ed numbers have a stange amount of decimals   
            'latitude' : '%.6f' % (float(hex2dec(hex[20:28]))/1000000.0),
            'longitude': '%.6f' % (float(hex2dec(hex[28:36]))/1000000.0),
            'altitude' : hex2dec(hex[16:20]),
            'title'    : chr(hex2dec(hex[0:2]))+chr(hex2dec(hex[2:4]))+chr(hex2dec(hex[4:6]))+chr(hex2dec(hex[6:8]))+chr(hex2dec(hex[8:10]))+chr(hex2dec(hex[10:12])),
            'type'     : hex2dec(hex[24:26])
        };
        return waypoint
    else:
        print 'incorrect waypoint length'
        pass

def getWaypoints():
    #connect serial connection
    ser = connectSerial()
    ser.write(hex2chr(COMMANDS['getWaypoints']))
    #wait for response
    time.sleep(2)
    data = chr2hex(ser.readline())
    ser.close()
    
    waypoints = data[6:-2]
    waypoints = chop(waypoints,36)

    waypointsParsed = list()
    for waypoint in waypoints:
        waypointsParsed.append(parseWaypoint(waypoint));
    print 'number of waypoints', len(waypointsParsed)
    return waypointsParsed

def exportWaypoints(waypoints):
    #write to file
    fileHandle = open(getAppPrefix()+'\\waypoints.txt','wt')
    fileHandle.write(str(waypoints))
    fileHandle.close()
    print 'Successfully wrote waypoints'

def importWaypoints(filepath=getAppPrefix()+'\\waypoints.txt'):
    #read from file
    fileHandle = open(filepath)
    waypointsImported = fileHandle.read()
    fileHandle.close()    
    waypoints = eval(waypointsImported)
    print 'Successfully read waypoints', len(waypoints)
    return waypoints

def setWaypoints(waypoints):
    numberOfWaypoints = '%04X' % len(waypoints)
    payload = 3+(12*len(waypoints))
        
    data = ''
    for waypoint in waypoints:
        chr1 = dec2hex(ord(waypoint['title'][0]))
        chr2 = dec2hex(ord(waypoint['title'][1]))
        chr3 = dec2hex(ord(waypoint['title'][2]))
        chr4 = dec2hex(ord(waypoint['title'][3]))
        chr5 = dec2hex(ord(waypoint['title'][4]))
        chr6 = dec2hex(ord(waypoint['title'][5]))
        
        lat = '%08X' % (float(waypoint['latitude'])*1000000)
        lng = '%08X' % (float(waypoint['longitude'])*1000000)
        alt = '%04X' % int(waypoint['altitude'])
        type = '%02X' % int(waypoint['type'])
        
        data += chr1+chr2+chr3+chr4+chr5+chr6+str('00')+type+alt+lat+lng
    
    checksum = checkersum(str(payload)+str('76')+str(numberOfWaypoints)+data)
    #print 'checksum', checksum
    #print 'data', data
    
    #connect serial connection
    ser = connectSerial()
    #write tracklisting command to serial port
    ser.write(hex2chr(COMMANDS['setWaypoints'] % {'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': data, 'checksum':checksum}))
    #wait for response
    time.sleep(2)
    response = chr2hex(ser.readline())
    ser.close()
    
    if response[:8] == '76000200':
        waypointsUpdated = hex2dec(reponse[8:10])
        print 'waypoints updated', waypointsUpdated
        return waypointsUpdated
    else:
        print 'error uploading waypoints'     