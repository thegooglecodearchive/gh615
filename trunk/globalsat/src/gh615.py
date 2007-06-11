import serial, string, datetime, time, os, sys, ConfigParser, logging
from stpy import Template

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
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.getAppPrefix()+'\\config.ini')
                
        #setup the logging module http://www.tiawichiresearch.com/?p=31 / http://www.red-dove.com/python_logging.html
        handler = logging.FileHandler(self.getAppPrefix()+'\\gh615.log')
        #TODO: current function in logger
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(lineno)d %(funcName)s %(message)s')
        handler.setFormatter(formatter)
        self.logger = logging.getLogger('gh615')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        if self.config.get("debug", "output"):
            outputHandler = logging.StreamHandler()
            outputHandler.setFormatter(logging.Formatter('%(levelname)s %(funcName)s(%(lineno)d): %(message)s'))
            self.logger.addHandler(outputHandler)
        self.logger.debug("created a class instance")
        #print self.getCurrentFunction()
            
    def connectSerial(self):
        """connect via serial interface"""
        try:
            self.serial = serial.Serial(port=self.config.get("serial", "comport"),baudrate=self.config.get("serial", "baudrate"),timeout=int(self.config.get("serial", "timeout")))
            self.logger.debug("serial port connection on " + self.serial.portstr)
        except:
            self.logger.critical("error establishing serial port connection")
            raise
    
    def writeSerial(self, arg):
        """utility function utilizing the serial object"""
        self.logger.debug("writing to serialport: " + arg)
        self.serial.write(self.hex2chr(arg))
        time.sleep(2)
        self.logger.debug("waiting at serialport: " + str(self.serial.inWaiting()))
    
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
    
    def getCurrentFunction(self):
        return sys._getframe(1).f_code.co_name
    
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
        return out
    
    def checkersum(self, hex):
        checksum = 0
        for i in range(0,len(hex),2):
            checksum = checksum^int(hex[i:i+2],16)
        return self.dec2hex(checksum)
            
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
            self.logger.error('incorrect track length')
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
            self.logger.error('incorrect track length')
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
        self.logger.debug('entered')
        try:
            #connect serial connection
            self.connectSerial()
            #write tracklisting command to serial port
            self.writeSerial(self.COMMANDS['getTracklist'])
            tracklist = self.chr2hex(self.serial.read(2070))
            time.sleep(2)

            if len(tracklist) > 8:
                #trim header/teil
                tracklist = tracklist[6:-2]
                #seperate tracks
                tracks = self.chop(tracklist,48)
                self.logger.info(str(len(tracks))+' tracks found') 
                tracksParsed = list()
                for track in tracks:
                    tracksParsed.append(self.parseTrackInfo(track));
                return tracksParsed 
            else:
                self.logger.info('no tracks found') 
                pass
        except:
            self.logger.exception('exception in getTracklist')
            raise
        finally:
            self.serial.close()
        
    def getTracks(self, trackIds):
        self.logger.debug('entered')
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
                        #print 'getting trackpoints', str(self.hex2dec(data[50:54]))+'-'+str(self.hex2dec(data[54:58]))
                        self.logger.debug('getting trackpoints ' + str(self.hex2dec(data[50:54])) + '-'+str(self.hex2dec(data[54:58])))
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
                            self.logger.debug('initalizing new track')
                            tracks.append(track)
                            track = dict([('trackinfo', dict()), ('trackpoints', list())])
                            last = -1
                            timeFromStart = False
                        
                        #request next segment
                        self.writeSerial(self.COMMANDS['requestNextTrackSegment'])
                    else:
                        #re-request last segment again
                        self.logger.debug('last segment Errornou, re-requesting')
                        self.serial.flushInput()
                        self.writeSerial(self.COMMANDS['requestErrornousTrackSegment'])
                else:
                    #received finished sign
                    finished = True        
            
            self.logger.info('number of tracks ' + str(len(tracks)))
            return tracks
        except:
            self.logger.exception('exception in getTracks')
            raise
        finally:
            self.serial.close()
    
    def exportTracks(self, tracks, format):
        self.logger.debug('entered')
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
            self.logger.info('Successfully wrote ' + filename)
        return len(tracks)
            
    def formatTracks(self):
        self.logger.debug('entered')
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
                self.logger.info('format tracks successful')
                return True
            else:
                self.logger.error('format not successful')
                return False
        except:
            self.logger.exception('exception in formatTracks')
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
            self.logger.error('incorrect waypoint length')
            pass
    
    def getWaypoints(self):
        self.logger.debug('entered')
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
            self.logger.info('number of waypoints ' + str(len(waypointsParsed)))             
            return waypointsParsed
        except:
            self.logger.exception("exception in getWaypoints")
            raise
        finally:
            self.serial.close()
    
    def exportWaypoints(self, waypoints):
        self.logger.debug('entered')
        #write to file
        filepath = self.getAppPrefix()+'\\waypoints.txt'
        fileHandle = open(filepath,'wt')
        fileHandle.write(str(waypoints))
        fileHandle.close()
        self.logger.info('Successfully wrote waypoints to ' + str(self.getAppPrefix()) + '\\waypoints.txt')
        return filepath
    
    def importWaypoints(self, filepath=''):
        self.logger.debug('entered')
        #read from file
        filepath = self.getAppPrefix()+'\\waypoints.txt'
        fileHandle = open(filepath)
        waypointsImported = fileHandle.read()
        fileHandle.close()    
        waypoints = eval(waypointsImported)
        self.logger.info('Successfully read waypoints ' + str(len(waypoints))) 
        return waypoints
    
    def setWaypoints(self, waypoints):
        self.logger.debug('entered')
        try:
            numberOfWaypoints = '%04X' % len(waypoints)
            payload = 3+(12*len(waypoints))
                        
            data = ''
            for waypoint in waypoints:
                chr1 = self.dec2hex(ord(waypoint['title'][0]))
                chr2 = self.dec2hex(ord(waypoint['title'][1]))
                chr3 = self.dec2hex(ord(waypoint['title'][2]))
                chr4 = self.dec2hex(ord(waypoint['title'][3]))
                chr5 = self.dec2hex(ord(waypoint['title'][4]))
                chr6 = self.dec2hex(ord(waypoint['title'][5]))

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
            self.writeSerial(self.COMMANDS['setWaypoints'] % {'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': data, 'checksum':checksum})
            time.sleep(2)
            response = self.chr2hex(self.serial.readline())
            time.sleep(2)
            
            if response[:8] == '76000200':
                waypointsUpdated = self.hex2dec(response[8:10])
                self.logger.info('waypoints updated: ' + str(waypointsUpdated))
                return waypointsUpdated
            else:
                self.logger.error('error uploading waypoints')
        except:
            self.logger.exception("exception in setWaypoints")
            raise
        finally:
            self.serial.close()