import serial, string, datetime, time, os, sys
from stpy import Template
import xml.dom.minidom

class gh615(object):
    """api for Globalsat GH615"""
    version = 0.1
    serial = ''
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

    def __init__(self):
        """constructor"""
        #print 'Created a class instance'
        self.config = self.readConfig()
               
    def xmlGetText(self,nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc
    
    def readConfig(self):
        #Read configuration data from config.xml
        configXml = xml.dom.minidom.parse(self.getAppPrefix()+'\\config.xml')
        #TODO: assign automatically
        config = dict([('serial', dict())])
        config['serial']['comport']  = str(self.xmlGetText(configXml.getElementsByTagName("comport")[0].childNodes))
        config['serial']['baudrate'] = int(self.xmlGetText(configXml.getElementsByTagName("baudrate")[0].childNodes))
        config['serial']['timeout']  = int(self.xmlGetText(configXml.getElementsByTagName("timeout")[0].childNodes))
        #print 'read configuration successfully', config
        return config
    
    def connectSerial(self):
        """connect via serial interface"""
        try:
            self.serial = serial.Serial(port=self.config['serial']['comport'],baudrate=self.config['serial']['baudrate'],timeout=self.config['serial']['timeout'])
            print self.serial.portstr
        except:
            print "error establishing serial port connection, check settings"
            raise
    
    def writeSerial(self, arg):
        """utility function utilizing the serial object"""
        self.serial.write(self.hex2chr(arg))
        time.sleep(2)
        print 'waiting:', self.serial.inWaiting()
    
    def getAppPrefix(self):
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
    
    def chop(self, s, chunk):
        return [s[i*chunk:(i+1)*chunk] for i in range((len(s)+chunk-1)/chunk)]
    
    def dec2hex(self, n):
        return "%X" % n
     
    def hex2dec(self, s):
        return int(s, 16)
    
    def hex2chr(self, hex):
        out = ''
        debug = ''
        for i in range(0,len(hex),2):
            out += chr(int('0x'+hex[i:i+2],16))
            debug += str(hex[i:i+2])
        #print 'debug hex2chr ', str(debug)
        return out
    
    def chr2hex(self, chr):
        out = ''
        debug = ''
        for i in range(0,len(chr)):
            out += '%(#)02X' % {"#": ord(chr[i])}
            debug += '%(#)02X' % {"#": ord(chr[i])}
        #print 'debug chr2hex ', str(debug)
        return out
    
    def checkersum(self, hex):
        checksum = 0
        for i in range(0,len(hex),2):
            checksum = checksum^int(hex[i:i+2],16)
        return self.dec2hex(checksum)
        
    def parseTrack(self, hex):
        #create here
        return track
    
    def parseTrackInfo(self, hex):
        if len(hex) == 44 or len(hex) == 48:
            trackinfo = {
                'date':        datetime.datetime(2000+self.hex2dec(hex[0:2]), self.hex2dec(hex[2:4]), self.hex2dec(hex[4:6]), self.hex2dec(hex[6:8]), self.hex2dec(hex[8:10]), self.hex2dec(hex[10:12])),
                'duration':    self.hex2dec(hex[12:20]),
                'distance':    self.hex2dec(hex[20:28]),
                'calories':    self.hex2dec(hex[28:32]),
                'topspeed':    self.hex2dec(hex[32:36]),
                'trackpoints': self.hex2dec(hex[36:44])
            } 
            if len(hex) == 48:
                trackinfo['id'] = self.hex2dec(hex[44:48])
            return trackinfo
        else:
            print 'incorrect track length', len(hex)
            print hex
            pass
    
    def parseTrackpoint(self, hex, timeFromStart = False):
        if len(hex) == 30:
            trackpoint = {
                #'latitude':  float(self.hex2dec(hex[0:8]))/float(1000000),
                #'longitude': float(self.hex2dec(hex[8:16]))/float(1000000),
                'latitude':  '%.6f' % (float(self.hex2dec(hex[0:8]))/1000000.0),
                'longitude': '%.6f' % (float(self.hex2dec(hex[8:16]))/1000000.0),
                'altitude':   self.hex2dec(hex[16:20]),
                'speed':      float(self.hex2dec(hex[20:24]))/float(100),
                'heartrate':  self.hex2dec(hex[24:26]),
                'interval':   self.hex2dec(hex[26:30]),
            };
            if timeFromStart != False:
                trackpoint['date'] = timeFromStart + datetime.timedelta(milliseconds=(self.hex2dec(hex[26:30])*100)) 
            return trackpoint
        else:
            print 'incorrect trackpoint length'
            pass
        
    def parseTrackpoints(self, hex):
        global timeFromStart
        
        trackpoints = self.chop(hex,30)
        if (len(trackpoints) > 0):
            #init trackpoints list
            ParsedTrackpoints = list()
            #loop over trackpoints and output
            for trackpoint in trackpoints: 
                parsedTrackpoint = self.parseTrackpoint(trackpoint, timeFromStart)
                ParsedTrackpoints.append(parsedTrackpoint);
                timeFromStart = parsedTrackpoint['date']
            return ParsedTrackpoints
    
    def getTracklist(self):
        try:
            #connect serial connection
            self.connectSerial()
            #write tracklisting command to serial port
            self.writeSerial(self.COMMANDS['getTracklist'])
            tracklist = self.chr2hex(self.serial.read(2070))
            time.sleep(2)
            
            #trim header/teil
            tracklist = tracklist[6:-2]
            #seperate tracks
            tracks = self.chop(tracklist,48)
            #if tracks exist    
            if len(tracks) > 0:    
                tracksParsed = list()
                for track in tracks:
                    tracksParsed.append(self.parseTrackInfo(track));
                print 'number of tracks', len(tracksParsed)
                return tracksParsed 
            #if no tracks exist
            else:
                print "no tracks available"
                pass
        except:
            print "tracklist exception occured"
            raise
        finally:
            self.serial.close()
        
    def getTracks(self, trackIds):
        try:
            global timeFromStart
            for i in range(len(trackIds)):
                trackIds[i] = '%04X' % int(trackIds[i])
            
            #calculate payload
            payload = '%04X' % ((len(trackIds)*512)+896)   
            #number of tracks
            numberOfTracks = '%04X' % len(trackIds)
            #checksum
            checksum = self.checkersum(payload+numberOfTracks+''.join(trackIds))
              
            #connect serial connection
            self.connectSerial()
            #write request to serial port
            self.writeSerial(self.COMMANDS['getTracks'] % {'payload':payload, 'numberOfTracks':numberOfTracks, 'trackIds': ''.join(trackIds), 'checksum':checksum})
            
            '''
            if ser.inWaiting() > 2070:
                print 'initial segment to large, quitting, please retry'
                finished == True
                ser.close()
            '''
            
            tracks = list()
            track = dict([('trackinfo', dict()), ('trackpoints', list())])
            last = -1
            finished = False;
            while finished == False:
                data = self.chr2hex(self.serial.read(2070))
                time.sleep(2)
                if data != '8A000000':
                    #print 'compare', str(last+1)+'/'+str(self.hex2dec(data[50:54]))
                    if (self.hex2dec(data[50:54]) == last+1):
                        #debug
                        print 'getting trackpoints', str(self.hex2dec(data[50:54]))+'-'+str(self.hex2dec(data[54:58]))
                        #check if first segment of track
                        if last == -1:
                            #parse trackinfo
                            track['trackinfo'] = self.parseTrackInfo(data[6:50])
                            timeFromStart = track['trackinfo']['date']
                        #parse trackpoints
                        track['trackpoints'].extend(self.parseTrackpoints(data[58:-2]))
                        #remeber last trackpoint
                        last = self.hex2dec(data[54:58])
                        #check if last segment of track
                        if len(data) < 4140:
                            #init new track
                            print 'initializing new track'
                            tracks.append(track)
                            track = dict([('trackinfo', dict()), ('trackpoints', list())])
                            last = -1
                            timeFromStart = False
                        
                        #request next segment
                        self.writeSerial(self.COMMANDS['requestNextTrackSegment'])
                    else:
                        #re-request last segment again
                        print 're-requesting last segment'
                        self.serial.flushInput()
                        self.writeSerial(self.COMMANDS['requestErrornousTrackSegment'])
                else:
                    #received finished sign
                    finished = True        
            
            print 'number of tracks', len(tracks)
            return tracks
        except:
            print "exception in getTracks"
            raise
        finally:
            self.serial.close()
    
    def exportTracks(self, tracks, format):
        #read template
        fileHandle = open(self.getAppPrefix()+'\\exportTemplates\\'+format+'.txt')
        templateImport = fileHandle.read()
        fileHandle.close() 
        for track in tracks:
            #parse template
            template = Template(templateImport)
            file = template.render(trackinfo = track['trackinfo'], trackpoints = track['trackpoints'])
            #prompt for filename
            #filename = raw_input("Enter a filename: ").strip()
            filename = track['trackinfo']['date'].strftime("%Y-%m-%d_%H-%M-%S")
            filename = self.getAppPrefix()+'\\export\\'+filename+'.'+format
            #write to file
            fileHandle = open(filename,'wt')
            fileHandle.write(file)
            fileHandle.close()
            print 'Successfully wrote', filename
            
    def formatTracks(self):
        try:
            #connect serial connection
            ser = self.connectSerial()
            #write tracklisting command to serial port
            self.writeSerial(self.COMMANDS['formatTracks'])
            #wait for response
            time.sleep(10)
            response = self.chr2hex(self.serial.read(4070))
            self.serial.close()
            
            if response == '79000000':
                return true
            else:
                return false
        except:
            print "exception in formatTracks"
            raise
        finally:
            self.serial.close()
    
    def parseWaypoint(self, hex):
        if len(hex) == 36:
            waypoint = {
                #if float()ed numbers have a stange amount of decimals   
                'latitude' : '%.6f' % (float(self.hex2dec(hex[20:28]))/1000000.0),
                'longitude': '%.6f' % (float(self.hex2dec(hex[28:36]))/1000000.0),
                'altitude' : self.hex2dec(hex[16:20]),
                'title'    : chr(self.hex2dec(hex[0:2]))+chr(self.hex2dec(hex[2:4]))+chr(self.hex2dec(hex[4:6]))+chr(self.hex2dec(hex[6:8]))+chr(self.hex2dec(hex[8:10]))+chr(self.hex2dec(hex[10:12])),
                'type'     : self.hex2dec(hex[24:26])
            };
            return waypoint
        else:
            print 'incorrect waypoint length'
            pass
    
    def getWaypoints(self):
        try:
            #connect serial connection
            self.connectSerial()
            self.writeSerial(self.COMMANDS['getWaypoints'])
            data = self.chr2hex(self.serial.readline())
            
            waypoints = data[6:-2]
            waypoints = self.chop(waypoints,36)
        
            waypointsParsed = list()
            for waypoint in waypoints:
                waypointsParsed.append(self.parseWaypoint(waypoint));
            print 'number of waypoints', len(waypointsParsed)
            return waypointsParsed
        except:
            print "exception in getWaypoints"
            raise
        finally:
            self.serial.close()
    
    def exportWaypoints(self, waypoints):
        #write to file
        fileHandle = open(self.getAppPrefix()+'\\waypoints.txt','wt')
        fileHandle.write(str(waypoints))
        fileHandle.close()
        print 'Successfully wrote waypoints to ', self.getAppPrefix()+'\\waypoints.txt'
    
    def importWaypoints(self, filepath=''):
        #read from file
        filepath = self.getAppPrefix()+'\\waypoints.txt'
        fileHandle = open(filepath)
        waypointsImported = fileHandle.read()
        fileHandle.close()    
        waypoints = eval(waypointsImported)
        print 'Successfully read waypoints', len(waypoints)
        return waypoints
    
    def setWaypoints(self, waypoints):
        try:
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
            
            checksum = self.checkersum(str(payload)+str('76')+str(numberOfWaypoints)+data)
            #print 'checksum', checksum
            #print 'data', data
            
            #connect serial connection
            self.connectSerial()
            #write tracklisting command to serial port
            self.writeSerial(self.COMMANDS['setWaypoints'] % {'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': data, 'checksum':checksum})
            response = self.chr2hex(self.serial.readline())
            time.sleep(2)
            
            if response[:8] == '76000200':
                waypointsUpdated = self.hex2dec(reponse[8:10])
                print 'waypoints updated', waypointsUpdated
                return waypointsUpdated
            else:
                print 'error uploading waypoints'
        except:
            print "exception in setWaypoints"
            raise
        finally:
            self.serial.close()  