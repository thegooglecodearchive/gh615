from __future__ import with_statement
import serial, re, string, math, datetime, time, os, sys, glob, ConfigParser, logging, logging.handlers

from decimal import *
from gpxParser import GPXParser
from stpy import Template, TemplateHTML

class Utilities():
    @classmethod
    def dec2hex(self, n, pad = False):
        hex = "%X" % int(n)
        if pad:
            hex = hex.rjust(pad, '0')[:pad]
        return hex
    
    @classmethod
    def hex2dec(self, s):
        return int(s, 16)
    
    @classmethod
    def hex2chr(self, hex):
        out = ''
        for i in range(0,len(hex),2):
            out += chr(self.hex2dec(hex[i:i+2]))
        return out
    
    @classmethod
    def chr2hex(self, chr):
        out = ''
        for i in range(0,len(chr)):
            out += '%(#)02X' % {"#": ord(chr[i])}
        return out
    
    @classmethod
    def coord2hex(self, coord):
        '''takes care of negative coordinates'''
        coord = Decimal(str(coord))
        
        if coord < 0:
            return self.dec2hex((coord * Decimal(1000000) + Decimal(4294967295)),8)
        else:
            return self.dec2hex(coord * Decimal(1000000),8)
    
    @classmethod
    def hex2coord(self, hex):
        '''takes care of negative coordinates'''
        if hex[0:1] == 'F':
            return Decimal(self.hex2dec(hex)/Decimal(1000000)) - Decimal('4294.967295')
        else:
            return Decimal(self.hex2dec(hex)/Decimal(1000000))
    
    @classmethod
    def chop(self, s, chunk):
        return [s[i*chunk:(i+1)*chunk] for i in range((len(s)+chunk-1)/chunk)]
    
    @classmethod 
    def checkersum(self, hex):
        checksum = 0
        
        for i in range(0,len(hex),2):
            checksum = checksum^int(hex[i:i+2],16)
        return self.dec2hex(checksum)
    
    @classmethod 
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


class Track(object):    
    def __init__(self, date = '', duration = 0, distance = 0, calories = 0, topspeed = 0, trackpointCount = 0):
        self.date            = date
        self.duration        = duration
        self.distance        = distance
        self.calories        = calories
        self.topspeed        = topspeed
        self.trackpointCount = trackpointCount
        self.trackpoints     = []
    

    def __hex__(self):
        date = Utilities.dec2hex(self.date.strftime('%y'),2) + Utilities.dec2hex(self.date.strftime('%m'),2) + \
               Utilities.dec2hex(self.date.strftime('%d'),2) + Utilities.dec2hex(self.date.strftime('%H'),2) + \
               Utilities.dec2hex(self.date.strftime('%M'),2) + Utilities.dec2hex(self.date.strftime('%S'),2)
               
        infos = Utilities.dec2hex(self.duration,8) + Utilities.dec2hex(self.distance,8) + \
                Utilities.dec2hex(self.calories,4) + Utilities.dec2hex(self.topspeed,4) + \
                Utilities.dec2hex(len(self.trackpoints),8)
        
        nrOfTrackpoints = self.trackpointCount
        
        #package segments of 136 trackpoints
        chunks = []
        for frome in xrange(0, nrOfTrackpoints, 136):
            to = (nrOfTrackpoints - 1) if (frome + 135 > nrOfTrackpoints) else (frome + 135)
            
            trackpointsConverted = ''.join([hex(trackpoint) for trackpoint in self.trackpoints[frome:to+1]])
            #first segments uses 90, all following 91
            isFirst = ('91','90')[frome == 0]
            payload = Utilities.dec2hex(27 + (15 * ((to-frome) + 1)), 4)                      
            checksum = Utilities.checkersum((Gh615.COMMANDS['setTracks'] % {'payload':payload, 'isFirst':isFirst, 'trackInfo':date+infos, 'from':Utilities.dec2hex(frome,4), 'to':Utilities.dec2hex(to,4), 'trackpoints': trackpointsConverted, 'checksum':'00'})[2:-2])
                       
            chunks.append(Gh615.COMMANDS['setTracks'] % {'payload':payload, 'isFirst':isFirst, 'trackInfo':date+infos, 'from':Utilities.dec2hex(frome,4), 'to':Utilities.dec2hex(to,4), 'trackpoints': trackpointsConverted, 'checksum':checksum})
        return ''.join(chunks)
    
    def __getitem__(self, attr):
        return getattr(self, attr)
    
    def fromHex(self, hex):
        if len(hex) == 44 or len(hex) == 48:
            self.date            = datetime.datetime(2000+Utilities.hex2dec(hex[0:2]), Utilities.hex2dec(hex[2:4]), Utilities.hex2dec(hex[4:6]), Utilities.hex2dec(hex[6:8]), Utilities.hex2dec(hex[8:10]), Utilities.hex2dec(hex[10:12]))
            self.duration        = Utilities.hex2dec(hex[12:20])
            self.distance        = Utilities.hex2dec(hex[20:28])
            self.calories        = Utilities.hex2dec(hex[28:32])
            self.topspeed        = Utilities.hex2dec(hex[32:36])
            self.trackpointCount = Utilities.hex2dec(hex[36:44])
                
            if len(hex) == 48:
                self.id = Utilities.hex2dec(hex[44:48])
            return self
        else:
            raise Gh615ParseException
        
    def addTrackpointsFromHex(self, hex):        
        trackpoints = Utilities.chop(hex,30)
        for trackpoint in trackpoints: 
            parsedTrackpoint = Trackpoint().fromHex(trackpoint)
            
            if not self.trackpoints:
                parsedTrackpoint.calculateDate(self.date)
            else:
                parsedTrackpoint.calculateDate(self.trackpoints[-1].date)
            self.trackpoints.append(parsedTrackpoint)
                                        
    def export(self, format, **kwargs):
        format = ExportFormat(format)
        format.exportTrack(self)
    

class Trackpoint(Utilities):    
    def __init__(self, latitude = 0, longitude = 0, altitude = 0, speed = 0, heartrate = 0, interval = 1, date = datetime.datetime.now()):
        self.latitude    = Decimal(latitude)
        self.longitude   = Decimal(longitude)
        self.altitude    = altitude
        self.speed       = speed
        self.heartrate   = heartrate
        self.interval    = interval
        self.date        = date
        
    def __str__(self):
        return "(%f, %f, %i, %i, %i, %i)" % (self.latitude, self.longitude, self.altitude, self.speed, self.heartrate, self.interval)
    
    def __hex__(self):        
        return "%(latitude)s%(longitude)s%(altitude)s%(speed)s%(heartrate)s%(interval)s" % {
            'latitude':   Utilities.coord2hex(self.latitude),
            'longitude':  Utilities.coord2hex(self.longitude),
            'altitude':   Utilities.dec2hex(self.altitude,4),
            'speed':      Utilities.dec2hex(self.speed,4),
            'heartrate':  Utilities.dec2hex(self.heartrate,2),
            'interval':   Utilities.dec2hex(self.interval,4)
        }
    
    def __getitem__(self, attr):
        return getattr(self, attr)
    
    def fromHex(self, hex, timeFromStart = False):
        if len(hex) == 30:
            self.latitude  = Utilities.hex2coord(hex[0:8])
            self.longitude = Utilities.hex2coord(hex[8:16])
            self.altitude  = Utilities.hex2dec(hex[16:20])
            self.speed     = Utilities.hex2dec(hex[20:24])/100
            self.heartrate = Utilities.hex2dec(hex[24:26])
            self.interval  = Utilities.hex2dec(hex[26:30])
            
            return self
        else:
            raise Gh615ParseException
    
    def calculateDate(self, date):
        self.date = date + datetime.timedelta(milliseconds = (self.interval * 100)) 


class Waypoint():
    TYPES = {
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
    
    def __init__(self, latitude = 0, longitude = 0, altitude = 0, title = '', type = 0):
        self.latitude = Decimal(latitude)
        self.longitude = Decimal(longitude)
        self.altitude = altitude
        self.title = title
        self.type = type
                
    def __str__(self):
        return "%s (%f,%f)" % (self.title, self.latitude, self.longitude)
        
    def __hex__(self):
        return "%(title)s00%(type)s%(altitude)s%(latitude)s%(longitude)s" % {
            'latitude'  : Utilities.coord2hex(self.latitude),
            'longitude' : Utilities.coord2hex(self.longitude),
            'altitude'  : Utilities.dec2hex(self.altitude,4),
            'type'      : Utilities.dec2hex(self.type,2),
            'title'     : Utilities.chr2hex(self.title.ljust(6)[:6])
        }
        
    def toDict(self):        
        return {
            'latitude'  : str(self.latitude),
            'longitude' : str(self.longitude),
            'altitude'  : self.altitude,
            'type'      : self.type,
            'title'     : self.title
        }

    def fromHex(self, hex):
        if len(hex) == 36:            
            def safeConvert(c):
                #if hex == 00 chr() converts it to space, not \x00
                if c == '00':
                    return ' '
                else:
                    return Utilities.hex2chr(c)
                
            self.latitude = Utilities.hex2coord(hex[20:28])
            self.longitude = Utilities.hex2coord(hex[28:36])
            self.altitude = Utilities.hex2dec(hex[16:20])
            self.title = safeConvert(hex[0:2])+safeConvert(hex[2:4])+safeConvert(hex[4:6])+safeConvert(hex[6:8])+safeConvert(hex[8:10])+safeConvert(hex[10:12])
            self.type = Utilities.hex2dec(hex[12:16])
            
            return self
        else:
            raise Gh615ParseException
    

class ExportFormat():    
    def __init__(self, format):
        if os.path.exists(Utilities.getAppPrefix('exportTemplates', '%s.txt' % format)):
            templateImport = open(Utilities.getAppPrefix('exportTemplates', '%s.txt' % format)).read()
            
            templateConfig = ConfigParser.SafeConfigParser()
            #setting defaults
            templateConfig.add_section(format)
            templateConfig.set(format, 'filename', format)
            templateConfig.set(format, 'nicename', format)
            templateConfig.set(format, 'extension', format)
            templateConfig.set(format, 'hasMultiple', "false")
            templateConfig.set(format, 'hasPre', "false")
        
            templateConfig.read(Utilities.getAppPrefix('exportTemplates','formats.ini'))   
            
            self.filename = format
            self.nicename = templateConfig.get(format, 'nicename')
            self.extension = templateConfig.get(format, 'extension')
            self.hasMultiple = templateConfig.getboolean(format, 'hasMultiple')
            #self.hasPre = os.path.exists(Utilities.getAppPrefix('exportTemplates', 'pre', '%s.py' % format)),
            self.hasPre = False
            self.template = Template(templateImport)
        else:
            self.logger.error('no such export format')
            return None
    
    def __str__(self):
        return "%s" % self.filename
    
    def exportTrack(self, track):
        self.__export([track])
    
    def exportTracks(self, tracks, merge = False):
        if merge:
            self.__export(tracks)
        else:
            for track in tracks:
                self.__export(track)
    
    def __export(self, tracks, **kwargs):
        if self.hasPre:
            exec open(Utilities.getAppPrefix('exportTemplates', 'pre', '%s.py' % self.filename)).read()
            self.pre = pre(track)
                
        if 'path' in kwargs:
            path = os.path.join(kwargs['path'])
        else:
            path = Utilities.getAppPrefix('export')
          
        path = os.path.join(path, "%s.%s" % (tracks[0].date.strftime("%Y-%m-%d_%H-%M-%S"), self.extension))
        #first arg is for compatibility reasons
        #content = self.template.render(tracks = [track.toDict() for track in tracks], track = tracks[0].toDict())
        content = self.template.render(tracks = [tracks], track = tracks[0])

        with open(path, 'wt') as f:
            f.write(content)


class Gh615Exception():
    pass

class Gh615SerialException(Gh615Exception):
    pass

class Gh615ParseException(Gh615Exception):
    pass


def serial_required(function):
    def serial_required_wrapper(x, *args, **kw):
        try:
            x._connectSerial()
            return function(x, *args, **kw)
        except Gh615SerialException, e:
            raise
        except:
            raise
        finally:
            x._disconnectSerial()
    return serial_required_wrapper


class SerialInterface():
    COMMANDS = {
        'getTracklist'                    : '0200017879',
        'setTracks'                       : '02%(payload)s%(isFirst)s%(trackInfo)s%(from)s%(to)s%(trackpoints)s%(checksum)s', 
        'getTracks'                       : '0200%(payload)s%(numberOfTracks)s%(trackIds)s%(checksum)s', 
        'requestNextTrackSegment'         : '0200018180', 
        'requestErrornousTrackSegment'    : '0200018283',
        'formatTracks'                    : '0200037900641E',
        'getWaypoints'                    : '0200017776',
        'setWaypoints'                    : '02%(payload)s76%(numberOfWaypoints)s%(waypoints)s%(checksum)s',
        'formatWaypoints'                 : '0200037500642',
        'unitInformation'                 : '0200018584',
        'whoAmI'                          : '020001BFBE',
        'unknown'                         : '0200018382'
    }
    
    def _connectSerial(self):
        """connect via serial interface"""
        try:
            self.serial = serial.Serial(port=self.config.get("serial", "comport"), 
                                        baudrate=self.config.get("serial", "baudrate"),
                                        timeout=self.config.getint("serial", "timeout"))
            self.logger.debug("serial connection on " + self.serial.portstr)
        except serial.SerialException:
            self.logger.critical("error establishing serial connection")
            raise Gh615SerialException
    
    def _disconnectSerial(self):
        """disconnect the serial connection"""
        self.serial.close()
        self.logger.debug("serial connection closed")

    
    def _writeSerial(self, command, *args, **kwargs):
        #try:
            if command in self.COMMANDS:
                hex = self.COMMANDS[command] % kwargs
            else:
                hex = command
            
            self.logger.debug("writing to serialport: " + hex)
            self.serial.write(Utilities.hex2chr(hex))
            #self.serial.sendBreak(2)
            time.sleep(2)
            self.logger.debug("waiting at serialport: " + str(self.serial.inWaiting()))
        #except:
        #    raise Gh615SerialException
        
    def _querySerial(self, command, *args, **kwargs):
        self._writeSerial(command, *args, **kwargs)
        return Utilities.chr2hex(self.serial.read(2070))
        
    def _diagnostic(self):
        """check if a connection can be established"""
        try:
            self._connectSerial()
            self._disconnectSerial()
            print "connection established successfully"
            return True
        except Gh615SerialException:
            self.logger.info("error establishing serial port connection, please check your config.ini file")
            return False
        
    def _getLikelyPort(self, availableOnly = True):
        """utility function for finding the most likely serialport the gh615 is connected to"""
        
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
            return []


class Gh615(SerialInterface):
    """api for Globalsat GH615"""
    version = 0.1
            
    def __init__(self):
        #config
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(Utilities.getAppPrefix('config.ini'))                
                
        #logging http://www.tiawichiresearch.com/?p=31 / http://www.red-dove.com/python_logging.html
        
        handler = logging.FileHandler(Utilities.getAppPrefix('gh615.log'))        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(lineno)d %(funcName)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        
        self.logger = logging.getLogger('gh615')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
                    
        ch = logging.FileHandler(Utilities.getAppPrefix('status.log'))  
        #ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        if self.config.getboolean("debug", "output"):
            outputHandler = logging.StreamHandler()
            outputHandler.setFormatter(logging.Formatter('%(levelname)s %(funcName)s(%(lineno)d): %(message)s'))
            self.logger.addHandler(outputHandler)
                                                                        
    def getExportFormats(self):
        formats = []
        
        for format in glob.glob(Utilities.getAppPrefix("exportTemplates", "*.txt")):
            (filepath, filename) = os.path.split(format)
            (shortname, extension) = os.path.splitext(filename)
            e = ExportFormat(shortname)
            formats.append(e)
        return formats
        
    @serial_required
    def getTracklist(self):
        tracklist = self._querySerial('getTracklist')

        if len(tracklist) > 8:
            tracks = Utilities.chop(tracklist[6:-2],48)#trim header, wtf?
            self.logger.info('%i tracks found' % len(tracks))    
            return [Track().fromHex(track) for track in tracks]    
        else:
            self.logger.info('no tracks found') 
            pass
    
    def getAllTracks(self):
        allTracks = self.getTracklist()
        ids = [track.id for track in allTracks]
        return self.getTracks(ids)
    
    @serial_required
    def getTracks(self, trackIds):
        trackIds = [Utilities.dec2hex(id, 4) for id in trackIds ]
        payload = Utilities.dec2hex((len(trackIds) * 512) + 896, 4)
        numberOfTracks = Utilities.dec2hex(len(trackIds), 4) 
        checksum = Utilities.checkersum("%s%s%s" % (payload, numberOfTracks, ''.join(trackIds)))
          
        #self._connectSerial()
        self._writeSerial('getTracks', **{'payload':payload, 'numberOfTracks':numberOfTracks, 'trackIds': ''.join(trackIds), 'checksum':checksum})
                    
        tracks = []
        last = -1
        
        while True:
            data = Utilities.chr2hex(self.serial.read(2070))
            time.sleep(2)
            
            if data != '8A000000':
                if (Utilities.hex2dec(data[50:54]) == last + 1):
                    self.logger.debug('getting trackpoints %d-%d' % (Utilities.hex2dec(data[50:54]), Utilities.hex2dec(data[54:58])))
                    #check if first segment of track
                    if last == -1:
                        self.logger.debug('initalizing new track')
                        track = Track().fromHex(data[6:50])
                    #parse trackpoints
                    track.addTrackpointsFromHex(data[58:-2])
                    #remeber last trackpoint
                    last = Utilities.hex2dec(data[54:58])
                    #check if last segment of track
                    if len(data) < 4140:
                        #init new track
                        tracks.append(track)
                        last = -1
                    #request next segment
                    self._writeSerial('requestNextTrackSegment')
                else:
                    #re-request last segment again
                    self.logger.debug('last segment Errornous, re-requesting')
                    self.serial.flushInput()
                    self._writeSerial('requestErrornousTrackSegment')
            else:
                break        
        
        self.logger.info('number of tracks %d' % len(tracks))
        return tracks
    
    def importTracks(self, files, **kwargs):        
        if "path" in kwargs:
            path = os.path.join(kwargs['path'])
        else:
            path = Utilities.getAppPrefix('import')
        
        tracks = []
        for file in files:
            with open(os.path.join(path,file)) as f:
                data = f.read()
                tracks.extend(self.__parseGpxTrack(data))
        
        self.logger.info('imported tracks ' + str(len(tracks)))
        return tracks
    
    def __parseGpxTrack(self, track):
        gpx = GPXParser(track)
        return gpx.tracks
    
    @serial_required
    def setTracks(self, tracks):
        #TODO: There is currently a problem with uploading tracks with less than 10 trackpoints !?                
        for track in tracks:
            chunks = Utilities.chop(hex(track), 4142)
            for i, chunk in enumerate(chunks):
                response = self._querySerial(chunk)

                if response == '9A000000':
                    self.logger.info('successfully uploaded track')
                elif response == '91000000' or response == '90000000':
                    self.logger.debug("uploaded chunk %i of %i" % (i+1, len(chunks)))
                elif response == '92000000':
                    #this probably means segment was not as expected, should resend previous segment?
                    self.logger.debug('wtf')
                else:
                    print 'error uploading track'
                    raise
        return len(tracks)

    @serial_required
    def formatTracks(self):
        self._writeSerial('formatTracks')
        #wait for response
        time.sleep(10)
        response = Utilities.chr2hex(self.serial.read(4070))
        
        if response == '79000000':
            self.logger.info('format tracks successful')
            return True
        else:
            self.logger.error('format not successful')
            return False
        
    @serial_required
    def getWaypoints(self):
        response = self._querySerial('getWaypoints')            
        waypoints = Utilities.chop(response[6:-2], 36)#trim junk
        return [Waypoint().fromHex(waypoint) for waypoint in waypoints] 

    def exportWaypoints(self, waypoints, **kwargs):
        if 'path' in kwargs:
            filepath = os.path.join(kwargs['path'], 'waypoints.txt')
        else:    
            filepath = Utilities.getAppPrefix('waypoints.txt')
                
        with open(filepath,'wt') as f:
            f.write(str([waypoint.toDict() for waypoint in waypoints]))
            
        self.logger.info('Successfully wrote waypoints to %s' % filepath)
        return filepath
    
    def importWaypoints(self, **kwargs):
        if 'path' in kwargs:
            filepath = os.path.join(kwargs['path'], 'waypoints.txt')
        else:    
            filepath = Utilities.getAppPrefix('waypoint_dummy.txt')
                
        with open(filepath) as f:
            importedWaypoints = f.read()
    
        waypoints = []
        for waypoint in eval(importedWaypoints):
            waypoints.append(Waypoint(waypoint['latitude'], waypoint['longitude'], waypoint['altitude'], waypoint['title'], waypoint['type']))
            
        self.logger.info('Successfully read waypoints %i' % len(waypoints)) 
        return waypoints
    
    @serial_required
    def setWaypoints(self, waypoints):                               
        waypointsConverted = ''.join([hex(waypoint) for waypoint in waypoints])
        numberOfWaypoints = Utilities.dec2hex(len(waypoints), 4)
        payload =  Utilities.dec2hex(3 + (18 * len(waypoints)), 4)
        checksum = Utilities.checkersum("%s76%s%s" % (str(payload), str(numberOfWaypoints), waypointsConverted))
        
        response = self._querySerial('setWaypoints', **{'payload':payload, 'numberOfWaypoints':numberOfWaypoints, 'waypoints': waypointsConverted, 'checksum':checksum})
        
        if response[:8] == '76000200':
            waypointsUpdated = Utilities.hex2dec(response[8:10])
            self.logger.info('waypoints updated: %i' % waypointsUpdated)
            return waypointsUpdated
        else:
            self.logger.error('error uploading waypoints')

    @serial_required
    def formatWaypoints(self):
        self._writeSerial('formatWaypoints')
        time.sleep(10)
        response = Utilities.chr2hex(self.serial.read(4070))
        
        if response == '75000000':
            self.logger.info('deleted all waypoints')
            return True
        else:
            self.logger.error('deleting all waypoints failed')
            return False
            

    @serial_required
    def getNmea(self):
        #http://regexp.bjoern.org/archives/gps.html
        def dmmm2dec(degrees,sw):
            deg = math.floor(degrees/100.0) #decimal degrees
            frac = ((degrees/100.0)-deg)/0.6 #decimal fraction
            ret = deg+frac #positive return value
            if ((sw == "S") or (sw == "W")):
                ret=ret*(-1) #flip sign if south or west
            return ret
        
        line = ""
        while not line.startswith("$GPGGA"):
            line = self.serial.readline()
        
        # calculate our lat+long
        tokens = line.split(",")
        lat = dmmm2dec(float(tokens[2]),tokens[3]) #[2] is lat in deg+minutes, [3] is {N|S|W|E}
        lng = dmmm2dec(float(tokens[4]),tokens[5]) #[4] is long in deg+minutes, [5] is {N|S|W|E}
    
    @serial_required
    def getUnitInformation(self):
        response = self._querySerial('unitInformation')
        
        if len(response) == 180:
            unit = {
                'device_name'      : Utilities.hex2chr(response[4:20]),
                'version'          : Utilities.hex2dec(response[50:52]),
                #'dont know'       : self.__hex2dec(response[52:56]),
                'firmware'         : Utilities.hex2chr(response[56:88]),
                'name'             : Utilities.hex2chr(response[90:110]),
                'sex'              : 'male' if (Utilities.hex2chr(response[112:114]) == '\x01') else 'female',
                'age'              : Utilities.hex2dec(response[114:116]),
                'weight_pounds'    : Utilities.hex2dec(response[116:120]),
                'weight_kilos'     : Utilities.hex2dec(response[120:124]),
                'height_inches'      : Utilities.hex2dec(response[124:128]),
                'height_centimeters' : Utilities.hex2dec(response[128:132]),
                'waypoint_count'   : Utilities.hex2dec(response[132:134]),
                'trackpoint_count' : Utilities.hex2dec(response[133:138]),
                'birth_year'       : Utilities.hex2dec(response[138:142]),
                'birth_month'      : Utilities.hex2dec(response[142:144])+1,
                'birth_day'        : Utilities.hex2dec(response[144:146])
            }
            return unit
        else:
            raise Gh615ParseException
    
    @serial_required
    def getProductVersion(self):
        response = self._querySerial('whoAmI')
        watch = Utilities.hex2chr(response[6:-4])
        product, version = watch[:-1], watch[-1:]
        return product

class TrackWithLaps(Track):
    def __init__(self, date = '', duration = 0, distance = 0, calories = 0, topspeed = 0, trackpointCount = 0, lapCount = 0):
        self.lapsCount = lapCount
        self.laps = []
        super(TrackWithLaps, self).__init__(date, duration,distance, calories, topspeed, trackpointCount)
    
    def fromHex(self, hex):
        if len(hex) == 58 or len(hex) == 62:            
            self.date            = datetime.datetime(2000+Utilities.hex2dec(hex[0:2]), Utilities.hex2dec(hex[2:4]), Utilities.hex2dec(hex[4:6]), Utilities.hex2dec(hex[6:8]), Utilities.hex2dec(hex[8:10]), Utilities.hex2dec(hex[10:12]))
            self.lapCount        = Utilities.hex2dec(hex[12:14])
            self.duration        = Utilities.hex2dec(hex[14:22])
            self.distance        = Utilities.hex2dec(hex[22:30])
            self.calories        = Utilities.hex2dec(hex[30:34])
            self.topspeed        = Utilities.hex2dec(hex[34:38])
            #self.unknown         = Utilities.hex2dec(hex[38:42])
            self.trackpointCount = Utilities.hex2dec(hex[42:50])
            #self.unknown2        = Utilities.hex2dec(hex[50:54])
            #self.unknown3        = Utilities.hex2dec(hex[54:58])
                
            if len(hex) == 62:
                self.id = Utilities.hex2dec(hex[58:62])
            return self
        else:
            raise Gh615ParseException
        
    def addLapsFromHex(self, hex):
        laps = Utilities.chop(hex,44)
        for lap in laps: 
            parsedLap = Lap().fromHex(lap)
            parsedLap.calculateDate(self.date)
            self.laps.append(parsedLap)


class Lap():
    def __init__(self, start = datetime.datetime.now(), stop = datetime.datetime.now(), duration = datetime.timedelta(), distance = 0, calories = 0):
        self.start    = start
        self.start    = stop
        self.duration = duration
        self.distance = distance
        self.calories = calories

    def fromHex(self, hex):
        if len(hex) == 44:
            self.__until    = Utilities.hex2dec(hex[:8])
            self.__duration = Utilities.hex2dec(hex[8:16])
            self.distance = Utilities.hex2dec(hex[16:24])
            self.calories = Utilities.hex2dec(hex[24:28])
 
            return self
        else:
            raise Gh615ParseException
        
    def calculateDate(self, date):
        self.stop = date + datetime.timedelta(milliseconds = (self.__until * 100))
        self.start = self.stop - datetime.timedelta(milliseconds = (self.__duration * 100))
        self.duration = self.stop - self.start
        
    
class Gh625(Gh615):
    @serial_required
    def getTracklist(self):
        tracklist = self._querySerial('getTracklist')

        if len(tracklist) > 8:
            tracks = Utilities.chop(tracklist[6:-2],62)#trim header, wtf?
            self.logger.info('%i tracks found' % len(tracks))    
            return [TrackWithLaps().fromHex(track) for track in tracks]    
        else:
            self.logger.info('no tracks found') 
            pass
        
    @serial_required
    def getTracks(self, trackIds):
        trackIds = [Utilities.dec2hex(id, 4) for id in trackIds ]
        payload = Utilities.dec2hex((len(trackIds) * 512) + 896, 4)
        numberOfTracks = Utilities.dec2hex(len(trackIds), 4) 
        checksum = Utilities.checkersum("%s%s%s" % (payload, numberOfTracks, ''.join(trackIds)))
          
        self._writeSerial('getTracks', **{'payload':payload, 'numberOfTracks':numberOfTracks, 'trackIds': ''.join(trackIds), 'checksum':checksum})
                    
        tracks = []
        last = -1
        initializeNewTrack = True
        
        while True:
            data = Utilities.chr2hex(self.serial.read(2070))
            time.sleep(2)
            
            if data != '8A000000':
                #shoud new track be initialized?
                if initializeNewTrack:
                    self.logger.debug('initalizing new track')
                    track = TrackWithLaps().fromHex(data[6:64])
                
                if data[60:64] == "FFFF":
                    self.logger.debug('adding laps')
                    track.addLapsFromHex(data[68:-2])
                    initializeNewTrack = False
                    self._writeSerial('requestNextTrackSegment')
                
                elif Utilities.hex2dec(data[60:64]) == last + 1:
                    self.logger.debug('adding trackpoints %d-%d' % (Utilities.hex2dec(data[60:64]), Utilities.hex2dec(data[64:68])))
                    track.addTrackpointsFromHex(data[68:-2])
                    last = Utilities.hex2dec(data[64:68])
                    initializeNewTrack = False
                    #check if last segment of track
                    if len(data) < 4140:
                        tracks.append(track)
                        last = -1
                        initializeNewTrack = True
                    self._writeSerial('requestNextTrackSegment')
                
                else:
                    #re-request last segment again
                    self.logger.debug('last segment Errornous, re-requesting')
                    self.serial.flushInput()
                    self._writeSerial('requestErrornousTrackSegment')
            else:
                break        
        
        self.logger.info('number of tracks %d' % len(tracks))
        return tracks