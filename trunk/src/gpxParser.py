import sys, string
from xml.dom import minidom, Node

#http://the.taoofmac.com/space/blog/2005/10/11/2359
class GPXParser:
  def __init__(self, data, mode = 'file',):
    self.tracks = {}
    try:
      if mode == 'file':
        doc = minidom.parse(data)
      else:
        doc = minidom.parseString(data)
      doc.normalize()
    except:
      raise
      return # handle this properly later
    gpx = doc.documentElement    
    for node in gpx.getElementsByTagName('trk'):
      self.parseTrack(node)

  def parseTrack(self, trk):
    #name = str(trk.getElementsByTagName('name')[0].firstChild.data)
    name = 'gpxtrack'
    if not name in self.tracks:
      self.tracks[name] = {}
    for trkseg in trk.getElementsByTagName('trkseg'):
      for trkpt in trkseg.getElementsByTagName('trkpt'):
        lat = float(trkpt.getAttribute('lat'))
        lon = float(trkpt.getAttribute('lon'))
        ele = float(trkpt.getElementsByTagName('ele')[0].firstChild.data)
        rfc3339 = str(trkpt.getElementsByTagName('time')[0].firstChild.data)
        self.tracks[name][rfc3339]={'lat':lat,'lon':lon,'ele':ele}

  def getTrack(self, name):
    times = self.tracks[name].keys()
    times.sort()
    points = [self.tracks[name][time] for time in times]
        
    return [(point['lat'],point['lon']) for point in points]