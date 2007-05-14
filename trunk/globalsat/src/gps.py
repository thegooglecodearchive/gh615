import serial, os, string, math
# GPS-based Google Maps search; example finds sandwich nearby
# Bjoern Hartmann, 10/06/2006
# requires: pySerial (pyserial.sourceforge.net), pywin32 on Windows (sourceforge.net/projects/pywin32/) 

# Execute a local application on system path- see http://effbot.org/librarybook/os.htm
def run(program, *args):
    for path in string.split(os.environ["PATH"], os.pathsep):
        file = os.path.join(path, program) + ".exe"
        try:
            return os.spawnv(os.P_NOWAIT, file, (program,) + args)
        except os.error:
            pass
    raise os.error, "cannot find executable"

# convert from degree+minutes to decimal degrees (see http://hamlib.sourceforge.net/manuals/1.2.2/html/API-reference/locator_8c.html)
def dmmm2dec(degrees,sw):
    deg= math.floor(degrees/100.0) #decimal degrees
    frac= ((degrees/100.0)-deg)/0.6 #decimal fraction
    ret = deg+frac #positive return value
    if ((sw=="S") or (sw=="W")):
        ret=ret*(-1) #flip sign if south or west
    return ret

# open a connection to NMEA-compatible GPS device at 4800bps8N1 (in this case COM2)
ser = serial.Serial(port='COM1',baudrate=4800,bytesize=8, parity='N', stopbits=1,timeout=3)

# read lines until we find one with the GPS position in it
line = ""
while not(line.startswith("$GPGGA")):
    line= ser.readline()
ser.close()

# calculate our lat+long
tokens = line.split(",")
lat = dmmm2dec(float(tokens[2]),tokens[3]) #[2] is lat in deg+minutes, [3] is {N|S|W|E}
lng = dmmm2dec(float(tokens[4]),tokens[5]) #[4] is long in deg+minutes, [5] is {N|S|W|E}

# build query string and load it in a new browser
query = "sandwiches"
url = r'"http://maps.google.com/maps?f=l&hl=en&q='+query+'&near='+str(lat)+','+str(lng)+'&ie=UTF8&z=12&om=1"';
run("firefox",url)