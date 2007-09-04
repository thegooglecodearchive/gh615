import serial, string, math, datetime, time, os, sys, glob, ConfigParser, logging, logging.handlers
from gpxParser import GPXParser
from stpy import Template, TemplateHTML

class gh615():
    """api for Globalsat GH615"""
    version = 0.1
    serial = ''
    STATUS = ''
    COMMANDS = {
        'getTracklist'                    : '0200017879',
        'getTracks'                       : '0200%(payload)s%(numberOfTracks)s%(trackIds)s%(checksum)s', 
        'setTracks'                       : '02%(payload)s%(isFirst)s%(trackInfo)s%(from)s%(to)s%(trackpoints)s%(checksum)s', 
        'requestNextTrackSegment'         : '0200018180', 
        'requestErrornousTrackSegment'    : '0200018283',
        'formatTracks'                    : '0200037900641E',
        'getWaypoints'                    : '0200017776',
        'setWaypoints'                    : '0200%(payload)s76%(numberOfWaypoints)s%(waypoints)s%(checksum)s',
        'unitInformation'                 : '0200018584'
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
        self.config.read(self.getAppPrefix()+'/config.ini')                
                
        #logging http://www.tiawichiresearch.com/?p=31 / http://www.red-dove.com/python_logging.html
        logging.STATUS = 15
        logging.addLevelName(logging.STATUS, 'STATUS')
        logging.addLevelName(15, "STATUS")
        
        handler = logging.FileHandler(self.getAppPrefix()+'/gh615.log')        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(lineno)d %(funcName)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        
        self.logger = logging.getLogger('gh615')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
    
        class InfoFilter(logging.Filter):
            def filter(self, record):
                return record.levelno == 15
                
        ch = logging.FileHandler(self.getAppPrefix()+'\\status.log')  
        ch.setLevel(logging.STATUS)
        ch.addFilter(InfoFilter())
        #ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        #self.logger.log(logging.STATUS, "this is a status")
        
        if self.config.getboolean("debug", "output"):
            outputHandler = logging.StreamHandler()
            outputHandler.setFormatter(logging.Formatter('%(levelname)s %(funcName)s(%(lineno)d): %(message)s'))
            self.logger.addHandler(outputHandler)
    
        self.logger.debug("created a class instance")
    
    def setStatus(self, msg):
        self.logger.log(15, msg)
        self.STATUS = msg
    
    def connectSerial(self):
        """connect via serial interface"""
        try:
            self.serial = serial.Serial(port=self.config.get("serial", "comport"),baudrate=self.config.get("serial", "baudrate"),timeout=self.config.getint("serial", "timeout"))
            self.logger.debug("serial connection on " + self.serial.portstr)
        except:
            self.logger.critical("error establishing serial connection")
            raise
    
    def disconnectSerial(self):
        """disconnect a serial connection"""
        try:
            if self.serial.isOpen():
                self.serial.close()
                self.logger.debug("serial connection closed")
        except:
            self.logger.debug("trying to close non-existent serial connection")
            pass
                
    def diagnostic(self):
        """connect via serial interface"""
        try:
            self.connectSerial()
        except:
            self.logger.info("error establishing serial port connection, please check your config.ini file")
        else:
            self.disconnectSerial()
            print "connection established successfully"
            
    def writeSerial(self, arg, sleep = 2):
        self.logger.debug("writing to serialport: " + arg)
        self.serial.write(self.hex2chr(arg))
        time.sleep(sleep)
        self.logger.debug("waiting at serialport: " + str(self.serial.inWaiting()))
        
    def getSerialPort(self, availableOnly = True):
        """utility function for finding the most likely serialport the gh615 is connected to"""
        self.logger.debug('entered')
        
        if os.name == 'nt':
            from serial.serialscan32 import *
            
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
    
    def dec2hex(self, n, pad = False):
        hex = "%X" % n
        if pad:
            hex = hex.rjust(pad, '0')
        return hex
     
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
        return out
    
    def __coord2hex(self, coord):
        '''takes care of negative coordinates'''
        
        #this is nasty, fix it
        coord = str(coord)
        
        if coord[0] == '-':
           return self.dec2hex(int(4294967295 + (float(coord)*1000000)),8)
        else:
            return self.dec2hex(float(coord)*1000000,8)
        
    def __hex2coord(self, hex):
        '''takes care of negative coordinates'''
        out = '%.6f' % (float(self.hex2dec(hex))/1000000.0)
        if hex[0:1] == 'F':
            out = float(out) - 4294.9673
        return out
    
    def checkersum(self, hex):
        checksum = 0
        for i in range(0,len(hex),2):
            checksum = checksum^int(hex[i:i+2],16)
        return self.dec2hex(checksum)
    
    def localizedLength(self, x, printUnit = False):
        unit = config.get('measurement','unit')
        
        if unit == 'imperial':
            out = x*3.2808399
        else: 
            out = x
            
        if printUnit:
            out += unit
        return out
    
    def getExportFormats(self):
        formats = list()
        
        for format in glob.glob(self.getAppPrefix()+"/exportTemplates/*.txt"):
            (filepath, filename) = os.path.split(format)
            (shortname, extension) = os.path.splitext(filename)
            formats.append(self.getExportFormat(shortname))
                
        return formats
    
    def getExportFormat(self, format):
            if os.path.exists(self.getAppPrefix()+'/exportTemplates/'+format+'.txt'):
                fileHandle = open(self.getAppPrefix()+'/exportTemplates/'+format+'.txt')
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
            
                templateConfig.read(self.getAppPrefix()+'/exportTemplates/formats.ini')   
                                
                format = {
                    'filename': format,
                    'nicename': templateConfig.get(format, 'nicename'),
                    'extension': templateConfig.get(format, 'extension'),
                    'hasMultiple': templateConfig.getboolean(format, 'hasMultiple'), 
                    'hasPre': os.path.exists(self.getAppPrefix()+'/exportTemplates/pre/'+format+'.py'),
                    'template': templateImport
                }
                return format
                
            else:
                self.logger.error('no such export format')
                return None
            
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
            self.disconnectSerial()
        
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
                        self.logger.debug('last segment Errornous, re-requesting')
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
            self.disconnectSerial()
    
    def exportTracks(self, tracks, format, merge = False):
        self.logger.debug('entered')
        #read template
        
        exportFormat = self.getExportFormat(format)
                
        #execute preCalculations
        if exportFormat['hasPre']:
            for track in tracks:
                if os.path.exists(self.getAppPrefix()+'/exportTemplates/pre/'+format+'.py'):
                    #pre = execfile(self.getAppPrefix()+'/exportTemplates/pre/'+format+'.py')
                    exec open(self.getAppPrefix()+'/exportTemplates/pre/'+format+'.py').read()
                    track['pre'] = pre(track)
        
        if merge:
            self.exportTracksMerged(tracks, exportFormat)  
        else:
            for track in tracks:
                self.exportTrack(track, exportFormat)

        return len(tracks)
    
    def exportTracksMerged(self, tracks, exportFormat):
        template = Template(exportFormat['template'])
        file = template.render(tracks = tracks)
        
        filename = str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))+"_combo"
        filename = self.getAppPrefix()+'/export/'+filename+'.'+exportFormat['extension']
        #write to file
        fileHandle = open(filename,'wt')
        fileHandle.write(file)
        fileHandle.close()
        self.logger.info('Successfully combine-wrote ' + filename)
    
    def exportTrack(self, track, exportFormat):
        template = Template(exportFormat['template'])
        #first arg is for compatibility reasons
        file = template.render(tracks = [track], track = track)
        
        filename = track['trackinfo']['date'].strftime("%Y-%m-%d_%H-%M-%S")
        filename = self.getAppPrefix()+'/export/'+filename+'.'+exportFormat['extension']
        #write to file
        fileHandle = open(filename,'wt')
        fileHandle.write(file)
        fileHandle.close()
        self.logger.info('Successfully wrote ' + filename)    
    
    def importTracks(self, trackData, mode = 'file'):
        tracks = list()
        for track in trackData:
            tracks.append(self.importTrack(track, mode))
        return tracks
    
    def importTrack(self, track, mode = "file"):
        gpx = GPXParser(track, mode)
        return gpx.getTrack('gpxtrack')
    
    def setTracks(self, tracks = None):        
        trackpoints = self.importTrack('C:\\Users\\till\\Desktop\\globalsat\\dummy.gpx')
        nrOfTrackpoints = len(trackpoints)
                
        #date of first waypoint
        date = datetime.datetime.strptime(trackpoints[0][2],'%Y-%m-%dT%H:%M:%SZ')
        trackinfo = {
            'date':        self.dec2hex(int(date.strftime('%y')),2)+self.dec2hex(int(date.strftime('%m')),2)+ self.dec2hex(int(date.strftime('%d')),2)+self.dec2hex(int(date.strftime('%H')),2)+self.dec2hex(int(date.strftime('%M')),2)+self.dec2hex(int(date.strftime('%S')),2),
            'duration':    '00000000',
            'distance':    '00000000',
            'calories':    '0000',
            'topspeed':    '0000',
            'trackpoints': self.dec2hex(nrOfTrackpoints,8)
        }
        trackinfoConverted = trackinfo['date']+trackinfo['duration']+trackinfo['distance']+trackinfo['calories']+trackinfo['topspeed']+trackinfo['trackpoints']
        
        
        #package segments of 136 trackpoints and send
        trackpointHex = '%(latitude)s%(longitude)s%(altitude)s%(speed)s%(hr)s%(int)s'
        
        self.connectSerial()
        for frome in xrange(0,nrOfTrackpoints,136):
            to = (frome+135, nrOfTrackpoints-1)[frome+135 > nrOfTrackpoints]
            
            trackpointsConverted = ''
            for trackpoint in trackpoints[frome:to+1]:
                trackpointsConverted += trackpointHex % {
                    #timeDiff = datetime.timedelta(milliseconds=(self.hex2dec(hex[26:30])*100)) 
                    'latitude':   self.__coord2hex(trackpoint[0]),
                    'longitude':  self.__coord2hex(trackpoint[1]),
                    'altitude':   self.dec2hex(0,4), #this is alttiude. not being imported atm
                    'speed':      self.dec2hex(0,4), #this is speed. not being imported atm
                    'hr':         self.dec2hex(0,2), #this is hr. not being imported atm
                    'int':        self.dec2hex(0,4) #this is int. not being imported atm
                }       
            
            #first segments uses 90, all following 91
            isFirst = ('91','90')[frome == 0]
            
            payload = self.dec2hex(27+(15*((to-frome)+1)),4)                      
            checksum = self.checkersum((self.COMMANDS['setTracks'] % {'payload':payload, 'isFirst':isFirst, 'trackInfo':trackinfoConverted, 'from':self.dec2hex(frome,4), 'to':self.dec2hex(to,4), 'trackpoints': trackpointsConverted, 'checksum':'00'})[2:-2])
            
            self.writeSerial(self.COMMANDS['setTracks'] % {'payload':payload, 'isFirst':isFirst, 'trackInfo':trackinfoConverted, 'from':self.dec2hex(frome,4), 'to':self.dec2hex(to,4), 'trackpoints': trackpointsConverted, 'checksum':checksum})
            response = self.chr2hex(self.serial.readline()) 
            #self.disconnectSerial()

            if response == '9A000000':
                self.logger.info('successfully uploaded track')
            elif response == '91000000' or response == '90000000':
                self.logger.debug('uploaded trackpoints ' + str(frome) + '-' + str(to) + ' of ' + str(nrOfTrackpoints))
            elif response == '92000000':
                #this probably means segment was not as expected, should resend previous segment
                self.logger.debug('wtf')
                self.disconnectSerial()
            else:
                print 'error uploading track'
                self.disconnectSerial()

        self.disconnectSerial()
        return

    def formatTracks(self):
        self.logger.debug('entered')
        try:
            #connect serial connection
            self.connectSerial()
            #write tracklisting command to serial port
            self.writeSerial(self.COMMANDS['formatTracks'])
            #wait for response
            time.sleep(10)
            response = self.chr2hex(self.serial.read(4070))
            self.disconnectSerial()
            
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
            self.serial.disconnectSerial()
    
    def parseWaypoint(self, hex):
        if len(hex) == 36:
            
            #latitude: determine if north or south orientation
            latitude = self.__hex2coord(hex[20:28])  
            longitude = self.__hex2coord(hex[28:36])
            
            #if hex eq 00 chr() converts it to \x00 no to space
            def safeConvert(c):
                if c == '00':
                    return ' '
                else:
                    return chr(self.hex2dec(c))
            
            waypoint = {
                #if float()ed: numbers have a stange amount of decimals   
                'latitude' : '%.6f' % float(latitude),
                'longitude': '%.6f' % float(longitude),
                'altitude' : self.hex2dec(hex[16:20]),
                'title'    : safeConvert(hex[0:2])+safeConvert(hex[2:4])+safeConvert(hex[4:6])+safeConvert(hex[6:8])+safeConvert(hex[8:10])+safeConvert(hex[10:12]),
                'type'     : self.hex2dec(hex[12:16])
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
            self.disconnectSerial()
    
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
            numberOfWaypoints = '%04X' % len(waypoints)
            payload = self.dec2hex(3+(18*len(waypoints)))
                                    
            data = ''
            for waypoint in waypoints:                
                latitude  = self.__coord2hex(waypoint['latitude'])
                longitude = self.__coord2hex(waypoint['longitude'])
                
                alt = self.dec2hex(int(waypoint['altitude']),4)
                type = self.dec2hex(int(waypoint['type']),2)
                
                waypoint['title'] = waypoint['title'].ljust(6)
                titleChr = ''
                for i in range(6):
                    titleChr += self.dec2hex(ord(waypoint['title'][i]))
            
                data += titleChr+str('00')+str('01')+alt+latitude+longitude
                
            checksum = self.checkersum(str(payload)+str('76')+str(numberOfWaypoints)+data)
            
            self.connectSerial()
            self.writeSerial(self.COMMANDS['setWaypoints'] % {'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': data, 'checksum':checksum})
            response = self.chr2hex(self.serial.readline())
            time.sleep(1)
            
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
            self.disconnectSerial()
    
    def getNmea(self):
        #http://regexp.bjoern.org/archives/gps.html
        def dmmm2dec(degrees,sw):
            deg = math.floor(degrees/100.0) #decimal degrees
            frac = ((degrees/100.0)-deg)/0.6 #decimal fraction
            ret = deg+frac #positive return value
            if ((sw=="S") or (sw=="W")):
                ret=ret*(-1) #flip sign if south or west
            return ret
        
        self.connectSerial()
        line = ""
        while not(line.startswith("$GPGGA")):
            line = self.serial.readline()
        self.disconnectSerial()
        
        # calculate our lat+long
        tokens = line.split(",")
        lat = dmmm2dec(float(tokens[2]),tokens[3]) #[2] is lat in deg+minutes, [3] is {N|S|W|E}
        lng = dmmm2dec(float(tokens[4]),tokens[5]) #[4] is long in deg+minutes, [5] is {N|S|W|E}
    
    def test(self):
        for i in range(10):
            print 'test: ', i
            self.setStatus(i)
            time.sleep(1)
        self.setStatus('success')
        return 'success'