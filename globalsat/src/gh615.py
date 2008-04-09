import serial, re, string, math, datetime, time, os, sys, glob, ConfigParser, logging, logging.handlers
from gpxParser import GPXParser
from stpy import Template, TemplateHTML

class gh615():
    """api for Globalsat GH615"""
    version = 0.1
    serial = ''
    STATUS = ''
    COMMANDS = {
        'getTracklist'                    : '0200017879',
        'setTracks'                       : '02%(payload)s%(isFirst)s%(trackInfo)s%(from)s%(to)s%(trackpoints)s%(checksum)s', 
        'getTracks'                       : '0200%(payload)s%(numberOfTracks)s%(trackIds)s%(checksum)s', 
        'requestNextTrackSegment'         : '0200018180', 
        'requestErrornousTrackSegment'    : '0200018283',
        'formatTracks'                    : '0200037900641E',
        'getWaypoints'                    : '0200017776',
        'setWaypoints'                    : '02%(payload)s76%(numberOfWaypoints)s%(waypoints)s%(checksum)s',
        'unitInformation'                 : '0200018584',
        'unknown'                         : '0200018382'
    }
        
    WAYPOINT_TYPES = {
        0:  'DOT',
        1:  'HOUSE',
        2:  'TRIANGLE',
        3:  'TUNNEL',
        4:  'CROSS',
        5:  'FISH',
        6:  'LIGHT',
        7:  'CAR',
        8:  'COMM',
        9:  'REDCROSS',
        10: 'TREE',
        11: 'BUS',
        12: 'COPCAR',
        13: 'TREES',
        14: 'RESTAURANT',
        15: 'SEVEN',
        16: 'PARKING',
        17: 'REPAIRS',
        18: 'MAIL',
        19: 'DOLLAR',
        20: 'GOVOFFICE',
        21: 'CHURCH',
        22: 'GROCERY',
        23: 'HEART',
        24: 'BOOK',
        25: 'GAS',
        26: 'GRILL',
        27: 'LOOKOUT',
        28: 'FLAG',
        29: 'PLANE',
        30: 'BIRD',
        31: 'DAWN',
        32: 'RESTROOM',
        33: 'WTF',
        34: 'MANTARAY',
        35: 'INFORMATION',
        36: 'BLANK'
    }
    
    def __init__(self):
        #config
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(self.getAppPrefix('config.ini'))                
                
        #logging http://www.tiawichiresearch.com/?p=31 / http://www.red-dove.com/python_logging.html
        logging.STATUS = 15
        logging.addLevelName(logging.STATUS, 'STATUS')
        logging.addLevelName(15, "STATUS")
        
        handler = logging.FileHandler(self.getAppPrefix('gh615.log'))        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(lineno)d %(funcName)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        
        self.logger = logging.getLogger('gh615')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
    
        class InfoFilter(logging.Filter):
            def filter(self, record):
                return record.levelno == 15
                
        ch = logging.FileHandler(self.getAppPrefix('status.log'))  
        ch.setLevel(logging.STATUS)
        ch.addFilter(InfoFilter())
        #ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        #self.logger.log(logging.STATUS, "this is a status")
        
        if self.config.getboolean("debug", "output"):
            outputHandler = logging.StreamHandler()
            outputHandler.setFormatter(logging.Formatter('%(levelname)s %(funcName)s(%(lineno)d): %(message)s'))
            self.logger.addHandler(outputHandler)
    
    def __setStatus(self, msg):
        self.logger.log(15, msg)
        self.STATUS = msg
    
    def __connectSerial(self):
        """connect via serial interface"""
        try:
            self.serial = serial.Serial(port=self.config.get("serial", "comport"),baudrate=self.config.get("serial", "baudrate"),timeout=self.config.getint("serial", "timeout"))
            self.logger.debug("serial connection on " + self.serial.portstr)
        except:
            self.logger.critical("error establishing serial connection")
            raise
    
    def __disconnectSerial(self):
        """disconnect a serial connection"""
        try:
            if self.serial.isOpen():
                self.serial.close()
                self.logger.debug("serial connection closed")
        except:
            self.logger.debug("trying to close non-existent serial connection")
            pass
        
    def __writeSerial(self, arg, sleep = 2):
        self.logger.debug("writing to serialport: " + arg)
        self.serial.write(self.__hex2chr(arg))
        time.sleep(sleep)
        self.logger.debug("waiting at serialport: " + str(self.serial.inWaiting()))
                
    def diagnostic(self):
        """connect via serial interface"""
        try:
            self.__connectSerial()
        except:
            self.logger.info("error establishing serial port connection, please check your config.ini file")
        else:
            self.__disconnectSerial()
            print "connection established successfully"
                    
    def getSerialPort(self, availableOnly = True):
        """utility function for finding the most likely serialport the gh615 is connected to"""
        self.logger.debug('entered')
        
        if os.name == 'nt':
            from serial.serialscan32 import comports
            
            ports = list()
            for port, desc, hwid in comports(availableOnly):
                #print "%-10s: %s (%s)" % (port, desc, hwid)
                portMatch = re.search("Prolific.*\(COM(\d+)\)", desc)
                #portMatch = re.search("Blue.*", desc)
                if portMatch :
                    ports.append(port)
                pass
            return ports
        else:
            return list()
                
    def getAppPrefix(self, *args):
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
        
        if args:
            appPrefix = os.path.join(appPrefix,*args)
            
        return appPrefix
    
    def __chop(self, s, chunk):
        return [s[i*chunk:(i+1)*chunk] for i in range((len(s)+chunk-1)/chunk)]
    
    def __dec2hex(self, n, pad = False):
        hex = "%X" % n
        if pad:
            hex = hex.rjust(pad, '0')
        return hex
     
    def __hex2dec(self, s):
        return int(s, 16)
    
    def __hex2chr(self, hex):
        out = ''
        for i in range(0,len(hex),2):
            out += chr(self.__hex2dec(hex[i:i+2]))
        return out
    
    def __chr2hex(self, chr):
        out = ''
        for i in range(0,len(chr)):
            out += '%(#)02X' % {"#": ord(chr[i])}
        return out
    
    def __coord2hex(self, coord):
        '''takes care of negative coordinates'''
        coord = str(coord)
        
        if coord[0] == '-':
           return self.__dec2hex(int(4294967295 + (float(coord)*1000000)),8)
        else:
            return self.__dec2hex(float(coord)*1000000,8)
        
    def __hex2coord(self, hex):
        '''takes care of negative coordinates'''
        out = '%.6f' % (float(self.__hex2dec(hex))/1000000.0)
        if hex[0:1] == 'F':
            out = float(out) - 4294.9673
        return out
    
    def __checkersum(self, hex):
        checksum = 0
        for i in range(0,len(hex),2):
            checksum = checksum^int(hex[i:i+2],16)
        return self.__dec2hex(checksum)
        
    def getExportFormats(self):
        formats = list()
        
        for format in glob.glob(self.getAppPrefix("exportTemplates","*.txt")):
            (filepath, filename) = os.path.split(format)
            (shortname, extension) = os.path.splitext(filename)
            formats.append(self.getExportFormat(shortname))
                
        return formats
    
    def getExportFormat(self, format):
            if os.path.exists(self.getAppPrefix('exportTemplates',format+'.txt')):
                fileHandle = open(self.getAppPrefix('exportTemplates',format+'.txt'))
                templateImport = fileHandle.read()
                fileHandle.close() 
                
                templateConfig = ConfigParser.SafeConfigParser()

                #setting defaults
                templateConfig.add_section(format)
                templateConfig.set(format, 'filename', format)
                templateConfig.set(format, 'nicename', format)
                templateConfig.set(format, 'extension', format)
                templateConfig.set(format, 'hasMultiple', "false")
                templateConfig.set(format, 'hasPre', "false")
            
                templateConfig.read(self.getAppPrefix('exportTemplates','formats.ini'))   
                                
                format = {
                    'filename':     format,
                    'nicename':     templateConfig.get(format, 'nicename'),
                    'extension':    templateConfig.get(format, 'extension'),
                    'hasMultiple':  templateConfig.getboolean(format, 'hasMultiple'), 
                    'hasPre':       os.path.exists(self.getAppPrefix('exportTemplates','pre',format+'.py')),
                    'template':     templateImport
                }
                return format
                
            else:
                self.logger.error('no such export format')
                return None
            
    def __parseTrackInfo(self, hex):
        if len(hex) == 44 or len(hex) == 48:
            trackinfo = {
                'date':        datetime.datetime(2000+self.__hex2dec(hex[0:2]), self.__hex2dec(hex[2:4]), self.__hex2dec(hex[4:6]), self.__hex2dec(hex[6:8]), self.__hex2dec(hex[8:10]), self.__hex2dec(hex[10:12])),
                'duration':    self.__hex2dec(hex[12:20]),
                'distance':    self.__hex2dec(hex[20:28]),
                'calories':    self.__hex2dec(hex[28:32]),
                'topspeed':    self.__hex2dec(hex[32:36]),
                'trackpoints': self.__hex2dec(hex[36:44])
            } 
            if len(hex) == 48:
                trackinfo['id'] = self.__hex2dec(hex[44:48])
            return trackinfo
        else:
            self.logger.error('incorrect track length')
            pass
    
    def __parseTrackpoint(self, hex, timeFromStart = False):
        if len(hex) == 30:
            trackpoint = {
                #'latitude':  float(self.__hex2dec(hex[0:8]))/float(1000000),
                #'longitude': float(self.__hex2dec(hex[8:16]))/float(1000000),
                'latitude':   self.__hex2coord(hex[0:8]),
                'longitude':  self.__hex2coord(hex[8:16]),
                'altitude':   self.__hex2dec(hex[16:20]),
                'speed':      float(self.__hex2dec(hex[20:24]))/float(100),
                'heartrate':  self.__hex2dec(hex[24:26]),
                'interval':   self.__hex2dec(hex[26:30]),
            };
            if timeFromStart != False:
                trackpoint['date'] = timeFromStart + datetime.timedelta(milliseconds=(self.__hex2dec(hex[26:30])*100)) 
            return trackpoint
        else:
            self.logger.error('incorrect track length')
            pass
        
    def __parseTrackpoints(self, hex):
        global timeFromStart
        
        trackpoints = self.__chop(hex,30)
        if (len(trackpoints) > 0):
            #init trackpoints list
            ParsedTrackpoints = list()
            #loop over trackpoints and output
            for trackpoint in trackpoints: 
                parsedTrackpoint = self.__parseTrackpoint(trackpoint, timeFromStart)
                ParsedTrackpoints.append(parsedTrackpoint);
                timeFromStart = parsedTrackpoint['date']
            return ParsedTrackpoints
    
    def getTracklist(self):
        self.logger.debug('entered')
        try:
            #connect serial connection
            self.__connectSerial()
            #write tracklisting command to serial port
            self.__writeSerial(self.COMMANDS['getTracklist'])
            tracklist = self.__chr2hex(self.serial.read(2070))
            time.sleep(2)

            if len(tracklist) > 8:
                #trim header/teil
                tracklist = tracklist[6:-2]
                #seperate tracks
                tracks = self.__chop(tracklist,48)
                self.logger.info(str(len(tracks))+' tracks found') 
                tracksParsed = list()
                for track in tracks:
                    tracksParsed.append(self.__parseTrackInfo(track));
                return tracksParsed 
            else:
                self.logger.info('no tracks found') 
                pass
        except:
            self.logger.exception('exception in getTracklist')
            raise
        finally:
            self.__disconnectSerial()
    
    def getAllTracks(self):
        allTracks = self.getTracklist()
        ids = list()
        for track in allTracks:
            ids.append(track['id'])

        return self.getTracks(ids)
    
    def getTracks(self, trackIds):
        self.logger.debug('entered')
        try:
            global timeFromStart
            for i in range(len(trackIds)):
                #trackIds[i] = '%04X' % int(trackIds[i])
                trackIds[i] = self.__dec2hex(int(trackIds[i]), 4)
            
            #calculate payload
            #payload = '%04X' % ((len(trackIds)*512)+896) 
            payload = self.__dec2hex((len(trackIds)*512)+896, 4)
            #number of tracks
            #numberOfTracks = '%04X' % len(trackIds)
            numberOfTracks = self.__dec2hex(len(trackIds), 4) 
            #checksum
            checksum = self.__checkersum(payload+numberOfTracks+''.join(trackIds))
              
            #connect serial connection
            self.__connectSerial()
            #write request to serial port
            self.__writeSerial(self.COMMANDS['getTracks'] % {'payload':payload, 'numberOfTracks':numberOfTracks, 'trackIds': ''.join(trackIds), 'checksum':checksum})
            
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
                data = self.__chr2hex(self.serial.read(2070))
                time.sleep(2)
                if data != '8A000000':
                    #print 'compare', str(last+1)+'/'+str(self.__hex2dec(data[50:54]))
                    if (self.__hex2dec(data[50:54]) == last+1):
                        #debug
                        #print 'getting trackpoints', str(self.__hex2dec(data[50:54]))+'-'+str(self.__hex2dec(data[54:58]))
                        self.logger.debug('getting trackpoints ' + str(self.__hex2dec(data[50:54])) + '-'+str(self.__hex2dec(data[54:58])))
                        #check if first segment of track
                        if last == -1:
                            #parse trackinfo
                            track['trackinfo'] = self.__parseTrackInfo(data[6:50])
                            timeFromStart = track['trackinfo']['date']
                        #parse trackpoints
                        track['trackpoints'].extend(self.__parseTrackpoints(data[58:-2]))
                        #remeber last trackpoint
                        last = self.__hex2dec(data[54:58])
                        #check if last segment of track
                        if len(data) < 4140:
                            #init new track
                            self.logger.debug('initalizing new track')
                            tracks.append(track)
                            track = dict([('trackinfo', dict()), ('trackpoints', list())])
                            last = -1
                            timeFromStart = False
                        
                        #request next segment
                        self.__writeSerial(self.COMMANDS['requestNextTrackSegment'])
                    else:
                        #re-request last segment again
                        self.logger.debug('last segment Errornous, re-requesting')
                        self.serial.flushInput()
                        self.__writeSerial(self.COMMANDS['requestErrornousTrackSegment'])
                else:
                    #received finished sign
                    finished = True        
            
            self.logger.info('number of tracks ' + str(len(tracks)))
            return tracks
        except:
            self.logger.exception('exception in getTracks')
            raise
        finally:
            self.__disconnectSerial()
    
    def exportTracks(self, tracks, format, merge = False, **kwargs):
        self.logger.debug('entered')
        #read template 
        exportFormat = self.getExportFormat(format)
        #execute preCalculations
        if exportFormat['hasPre']:
            for track in tracks:
                if os.path.exists(self.getAppPrefix('exportTemplates','pre',format+'.py')):
                    #pre = execfile(self.getAppPrefix()+'/exportTemplates/pre/'+format+'.py')
                    exec open(self.getAppPrefix('exportTemplates','pre',format+'.py')).read()
                    track['pre'] = pre(track)
                
        if 'path' in kwargs:
            path = os.path.join(kwargs['path'])
        else:
            path = self.getAppPrefix('export')
                
        template = Template(exportFormat['template'])
        if merge:
            path = os.path.join(path, tracks[0]['trackinfo']['date'].strftime("%Y-%m-%d_%H-%M-%S")+'.'+exportFormat['extension'])
            file = template.render(tracks = tracks)  
            self.__exportTrack(file, path)
        else:
            for track in tracks:
                #first arg is for compatibility reasons
                path = os.path.join(path, track['trackinfo']['date'].strftime("%Y-%m-%d_%H-%M-%S")+'.'+exportFormat['extension'])
                file = template.render(tracks = [track], track = track)
                self.__exportTrack(file, path)
        return len(tracks)
 
    def __exportTrack(self, content, path):       
        fileHandle = open(path,'wt')
        fileHandle.write(content)
        fileHandle.close()
        self.logger.info('Successfully wrote ' + path)    
    
    def importTracks(self, trackData, **kwargs):
        tracks = list()
        
        if "path" in kwargs:
            path = os.path.join(kwargs['path'])
        else:
            path = self.getAppPrefix('import')
        
        tracks = []
        for track in trackData:
            fileHandle = open(os.path.join(path,track))
            data = fileHandle.read()
            fileHandle.close()
            #MERGE AT THIS POINT
            for s in self.__importTrack(data):
                tracks.append(s)                
        
        #else:
        #    for track in trackData:
        #        tracks.append(self.__importTrack(track))
        
        self.logger.info('imported tracks ' + str(len(tracks)))
        return tracks
    
    def __importTrack(self, track):
        gpx = GPXParser(track)
        return gpx.tracks
    
    def setTracks(self, tracks = None):        
        if tracks:
            self.__connectSerial()
            for track in tracks:
                nrOfTrackpoints = len(track['trackpoints'])
                       
                date = self.__dec2hex(int(track['date'].strftime('%y')),2)+self.__dec2hex(int(track['date'].strftime('%m')),2)+ self.__dec2hex(int(track['date'].strftime('%d')),2)+self.__dec2hex(int(track['date'].strftime('%H')),2)+self.__dec2hex(int(track['date'].strftime('%M')),2)+self.__dec2hex(int(track['date'].strftime('%S')),2)
                trackinfoConverted = date+self.__dec2hex(track['duration'],8)+self.__dec2hex(track['distance'],8)+self.__dec2hex(track['calories'],4)+self.__dec2hex(track['topspeed'],4)+self.__dec2hex(len(track['trackpoints']),8)
                
                trackpointHex = '%(latitude)s%(longitude)s%(altitude)s%(speed)s%(hr)s%(int)s'
                
                #package segments of 136 trackpoints and send
                for frome in xrange(0,nrOfTrackpoints,136):
                    to = (frome+135, nrOfTrackpoints-1)[frome+135 > nrOfTrackpoints]
                    
                    trackpointsConverted = ''
                    for trackpoint in track['trackpoints'][frome:to+1]:
                        trackpointsConverted += trackpointHex % {
                            #timeDiff = datetime.timedelta(milliseconds=(self.__hex2dec(hex[26:30])*100)) 
                            'latitude':   self.__coord2hex(trackpoint['latitude']),
                            'longitude':  self.__coord2hex(trackpoint['longitude']),
                            'altitude':   self.__dec2hex(0,4), #this is alttiude. not being imported atm
                            'speed':      self.__dec2hex(0,4), #this is speed. not being imported atm
                            'hr':         self.__dec2hex(0,2), #this is hr. not being imported atm
                            'int':        self.__dec2hex(0,4) #this is int. not being imported atm
                        }       
                    
                    #first segments uses 90, all following 91
                    isFirst = ('91','90')[frome == 0]
                    
                    payload = self.__dec2hex(27+(15*((to-frome)+1)),4)                      
                    checksum = self.__checkersum((self.COMMANDS['setTracks'] % {'payload':payload, 'isFirst':isFirst, 'trackInfo':trackinfoConverted, 'from':self.__dec2hex(frome,4), 'to':self.__dec2hex(to,4), 'trackpoints': trackpointsConverted, 'checksum':'00'})[2:-2])
                    
                    self.__writeSerial(self.COMMANDS['setTracks'] % {'payload':payload, 'isFirst':isFirst, 'trackInfo':trackinfoConverted, 'from':self.__dec2hex(frome,4), 'to':self.__dec2hex(to,4), 'trackpoints': trackpointsConverted, 'checksum':checksum})
                    response = self.__chr2hex(self.serial.readline()) 
    
                    if response == '9A000000':
                        self.logger.info('successfully uploaded track')
                    elif response == '91000000' or response == '90000000':
                        self.logger.debug('uploaded trackpoints ' + str(frome) + '-' + str(to) + ' of ' + str(nrOfTrackpoints))
                    elif response == '92000000':
                        #this probably means segment was not as expected, should resend previous segment
                        self.logger.debug('wtf')
                        self.__disconnectSerial()
                    else:
                        print 'error uploading track'
                        self.__disconnectSerial()
                        sys.exit()
                        
            self.__disconnectSerial()
            return len(tracks)
        else:
            self.logger.info('no tracks to be uploaded')
            pass

    def formatTracks(self):
        self.logger.debug('entered')
        try:
            #connect serial connection
            self.__connectSerial()
            #write tracklisting command to serial port
            self.__writeSerial(self.COMMANDS['formatTracks'])
            #wait for response
            time.sleep(10)
            response = self.__chr2hex(self.serial.read(4070))
            self.__disconnectSerial()
            
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
            self.__disconnectSerial()
    
    def __parseWaypoint(self, hex):
        if len(hex) == 36:            
            #if hex == 00 chr() converts it to \x00, not to space
            def safeConvert(c):
                if c == '00':
                    return ' '
                else:
                    return chr(self.__hex2dec(c))
            
            waypoint = {
                #if float()ed: numbers have a stange amount of decimals   
                'latitude' : self.__hex2coord(hex[20:28]),
                'longitude': self.__hex2coord(hex[28:36]),
                'altitude' : self.__hex2dec(hex[16:20]),
                'title'    : safeConvert(hex[0:2])+safeConvert(hex[2:4])+safeConvert(hex[4:6])+safeConvert(hex[6:8])+safeConvert(hex[8:10])+safeConvert(hex[10:12]),
                'type'     : self.__hex2dec(hex[12:16])
            };
            return waypoint
        else:
            self.logger.error('incorrect waypoint length')
            pass
    
    def getWaypoints(self):
        self.logger.debug('entered')
        try:
            #connect serial connection
            self.__connectSerial()
            self.__writeSerial(self.COMMANDS['getWaypoints'])
            data = self.__chr2hex(self.serial.readline())
            
            waypoints = data[6:-2]
            waypoints = self.__chop(waypoints,36)
        
            waypointsParsed = list()
            for waypoint in waypoints:
                waypointsParsed.append(self.__parseWaypoint(waypoint));
            self.logger.info('number of waypoints ' + str(len(waypointsParsed)))             
            return waypointsParsed
        except:
            self.logger.exception("exception in getWaypoints")
            raise
        finally:
            self.__disconnectSerial()
    
    def exportWaypoints(self, waypoints, **kwargs):
        self.logger.debug('entered')
        #write to file
        if 'path' in kwargs:
            filepath = os.path.join(kwargs['path'], 'waypoints.txt')
        else:    
            filepath = self.getAppPrefix('waypoints.txt')
                
        fileHandle = open(filepath,'wt')
        fileHandle.write(str(waypoints))
        fileHandle.close()
        self.logger.info('Successfully wrote waypoints to %s' % filepath)
        return filepath
    
    def importWaypoints(self, **kwargs):
        self.logger.debug('entered')
        #read from file
        if 'path' in kwargs:
            filepath = os.path.join(kwargs['path'], 'waypoints.txt')
        else:    
            filepath = self.getAppPrefix('waypoints.txt')
                
        if os.path.exists(filepath):
            fileHandle = open(filepath)
            waypointsImported = fileHandle.read()
            fileHandle.close()    
            waypoints = eval(waypointsImported)
            self.logger.info('Successfully read waypoints ' + str(len(waypoints))) 
            return waypoints
        else:
            self.logger.info('waypoints file does not exist, creating') 
            fileHandle = open(filepath,'wt')
            fileHandle.write('[]')
            fileHandle.close()
            return list()
    
    def setWaypoints(self, waypoints):
        self.logger.debug('entered')
        try:                                    
            data = ''
            for waypoint in waypoints:                
                latitude  = self.__coord2hex(float(waypoint['latitude']))
                longitude = self.__coord2hex(float(waypoint['longitude']))
                alt = self.__dec2hex(int(waypoint['altitude']),4)
                type = self.__dec2hex(int(waypoint['type']),2)
                title = self.__chr2hex(waypoint['title'].ljust(6)[:6])
            
                data += title + str('00') + type + alt + latitude + longitude
            
            #numberOfWaypoints = '%04X' % len(waypoints)
            numberOfWaypoints = self.__dec2hex(len(waypoints),4)
            #payload = self.__dec2hex(3+(18*len(waypoints)))    
            payload = self.__dec2hex(3+(18*len(waypoints)),4) 
            checksum = self.__checkersum(str(payload)+str('76')+str(numberOfWaypoints)+data)
            
            self.__connectSerial()
            self.__writeSerial(self.COMMANDS['setWaypoints'] % {'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': data, 'checksum':checksum})
            response = self.__chr2hex(self.serial.readline())
            print "resposne", response
            
            if response[:8] == '76000200':
                waypointsUpdated = self.__hex2dec(response[8:10])
                self.logger.info('waypoints updated: ' + str(waypointsUpdated))
                return waypointsUpdated
            else:
                self.logger.error('error uploading waypoints')
        except:
            self.logger.exception("exception in setWaypoints")
            raise
        finally:
            self.__disconnectSerial()
    
    def getNmea(self):
        #http://regexp.bjoern.org/archives/gps.html
        def dmmm2dec(degrees,sw):
            deg = math.floor(degrees/100.0) #decimal degrees
            frac = ((degrees/100.0)-deg)/0.6 #decimal fraction
            ret = deg+frac #positive return value
            if ((sw == "S") or (sw == "W")):
                ret=ret*(-1) #flip sign if south or west
            return ret
        
        self.__connectSerial()
        line = ""
        while not line.startswith("$GPGGA"):
            line = self.serial.readline()
        self.__disconnectSerial()
        
        # calculate our lat+long
        tokens = line.split(",")
        lat = dmmm2dec(float(tokens[2]),tokens[3]) #[2] is lat in deg+minutes, [3] is {N|S|W|E}
        lng = dmmm2dec(float(tokens[4]),tokens[5]) #[4] is long in deg+minutes, [5] is {N|S|W|E}
    
    def __parseUnitInformation(self, hex):
        if len(hex) == 180:
            unit = {
                'device_name'      : self.__hex2chr(hex[4:20]),
                'version'          : self.__hex2dec(hex[50:52]),
                #'dont know'       : self.__hex2dec(response[52:56]),
                'firmware'         : self.__hex2chr(hex[56:88]),
                'name'             : self.__hex2chr(hex[90:110]),
                'sex'              : ('male', 'female')[self.__hex2chr(hex[112:114]) == '\x01'],
                'age'              : self.__hex2dec(hex[114:116]),
                'weight_pounds'    : self.__hex2dec(hex[116:120]),
                'weight_kilos'     : self.__hex2dec(hex[120:124]),
                'height_inches'      : self.__hex2dec(hex[124:128]),
                'height_centimeters' : self.__hex2dec(hex[128:132]),
                'waypoint_count'   : self.__hex2dec(hex[132:134]),
                'trackpoint_count' : self.__hex2dec(hex[134:136]),
                'birth_year'       : self.__hex2dec(hex[138:142]),
                'birth_month'      : self.__hex2dec(hex[142:144])+1,
                'birth_day'        : self.__hex2dec(hex[144:146])
            }
            return unit
        else:
            self.logger.error('incorrect unitInformation length')
            pass
    
    def getUnitInformation(self):
            self.__connectSerial()
            self.__writeSerial(self.COMMANDS['unitInformation'])
            response = self.__chr2hex(self.serial.readline())
            self.__disconnectSerial()

            unit = self.__parseUnitInformation(response)
            
            return unit
    
    def unknown(self):
        self.__connectSerial()
        self.__writeSerial(self.COMMANDS['check1'])
        response = self.__chr2hex(self.serial.readline())
        self.__disconnectSerial()
        print response
        
    def test(self):
        for i in range(10):
            print 'test: ', i
            self.__setStatus(i)
            time.sleep(1)
        self.__setStatus('success')
        return 'success'