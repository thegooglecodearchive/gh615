import cherrypy, webbrowser
from gh615 import *
from mofo import *

gh615 = gh615()

class Root:
    @cherrypy.expose
    def index(self):
        template = TemplateHTML('index.html')
        return template.render(cherrypy)
    
    @cherrypy.expose
    def exit(self):
        raise SystemExit(0)
    
class Tracks:
    @cherrypy.expose
    def index(self):
        template = TemplateHTML('tracks/index.html')
        return template.render(cherrypy)
    
    @cherrypy.expose
    def importer(self):
        template = TemplateHTML('tracks/import.html')
        files = glob.glob(gh615.getAppPrefix()+"\\import\\*.xml")
        
        return template.render(cherrypy, files = files)
    
    @cherrypy.expose
    def doImport(self, upload = None, file = None):
        def readGpx(id):
            fileHandle = open(glob.glob(gh615.getAppPrefix()+"\\import\\*.xml")[int(id)])
            track = fileHandle.read()
            fileHandle.close()
            return track
            
        tracks = list()
        if file:
            if isinstance(file, str):
                tracks.append(readGpx(file))
            else:
                for id in file:
                    tracks.append(readGpx(id))
        elif upload is not None:
            #print type(upload.file)
            if not isinstance(upload, list):
                tracks.append(upload.file.read())
            else:
                for gpxFile in upload:
                  tracks.append(gpxFile.file.read()) 
            #return out % (size, myFile.filename, myFile.type)
            
        #convert from gpx to globalsat format and upload
        tracks = gh615.importTracks(tracks, 'string')
        #not yet implemented
        #result = gh615.setTracks(tracks);
        return str(tracks)

class Waypoints:
    @cherrypy.expose
    def index(self):
        localWaypoints = gh615.importWaypoints()
        remoteWaypoints = cherrypy.session.get('remoteWaypoints')
        
        template = TemplateHTML('waypoints/index.html')
        return template.render(cherrypy, localWaypoints = localWaypoints, remoteWaypoints = remoteWaypoints)
    
    @cherrypy.expose
    def add(self):        
        template = TemplateHTML('waypoints/add.html')
        return template.render(cherrypy)

    @cherrypy.expose
    def doAdd(self, latitude, longitude, altitude, title, type):
        #load exisiting and add new
        waypoints = gh615.importWaypoints()
        
        waypoints.append({
            'latitude' : latitude,
            'longitude': longitude,
            'altitude' : altitude,
            'title'    : title,
            'type'     : type
        });
        
        results = gh615.exportWaypoints(waypoints)
        #return 'exported Waypoints to', results
        raise cherrypy.HTTPRedirect('/waypoints')
    
    @cherrypy.expose
    def delete(self):    
        waypoints = gh615.importWaypoints()
            
        template = TemplateHTML('waypoints/delete.html')
        return template.render(cherrypy, waypoints = waypoints)
    
    @cherrypy.expose
    def doDelete(self, toBeDeleted):
        waypoints = gh615.importWaypoints()
        
        #if only one waypoint is to be deleted post is string, otherwise list
        if isinstance(toBeDeleted, str):
            del waypoints[int(toBeDeleted)]
        else:
            toBeDeleted.reverse()
            for id in toBeDeleted:
                del waypoints[int(id)]
        results = gh615.exportWaypoints(waypoints)
            
        raise cherrypy.HTTPRedirect('/waypoints')
    
    @cherrypy.expose
    def edit(self, id = 0):    
        waypoints = gh615.importWaypoints()
        waypoint = waypoints[int(id)]
        waypoint['id'] = id
        
        template = TemplateHTML('waypoints/edit.html')
        return template.render(cherrypy, waypoint = waypoint)
    
    @cherrypy.expose
    def doEdit(self, id, latitude, longitude, altitude, title, type):    
        waypoints = gh615.importWaypoints()
        del waypoints[int(id)]

        waypoints.insert(int(id), {
            'latitude' : latitude,
            'longitude': longitude,
            'altitude' : altitude,
            'title'    : title,
            'type'     : type
        });
        results = gh615.exportWaypoints(waypoints)
        
        raise cherrypy.HTTPRedirect('/waypoints')

    @cherrypy.expose
    def doCopyTo(self, toBeCopied):
        #copy from from waypoints.txt to device here
        waypoints = gh615.importWaypoints()
        
        copyMe = list()
        if isinstance(toBeExported, str):
            copyMe.append(remoteWaypoints[int(toBeCopied)])
        else:
            for id in toBeExported:
                copyMe.append(remoteWaypoints[int(id)])
        gh615.setWaypoints(copyMe)
        
        raise cherrypy.HTTPRedirect('/waypoints')

    @cherrypy.expose
    def doCopyFrom(self, toBeCopied):
        #copy from session/temp to waypoints.txt here
        waypoints = gh615.importWaypoints()
        remoteWaypoints = cherrypy.session.get('remoteWaypoints')
        
        if isinstance(toBeCopied, str):
            waypoints.append(remoteWaypoints[int(toBeCopied)])
        else:
            for id in toBeCopied:
                waypoints.append(remoteWaypoints[int(id)])
        results = gh615.exportWaypoints(waypoints)
            
        raise cherrypy.HTTPRedirect('/waypoints')
    
    @cherrypy.expose
    def doGetWaypoints(self):
        #import waypoints from gh615, store in session
        #waypoints = gh615.getWaypoints() 
        #this is a dummy
        fileHandle = open('waypoint_dummy.txt')
        waypointsImported = fileHandle.read()
        fileHandle.close()    
        waypoints = eval(waypointsImported)
        
        cherrypy.session['remoteWaypoints'] = waypoints
        raise cherrypy.HTTPRedirect('/waypoints')

    @cherrypy.expose
    def getWaypointAltitude(self, latitude = 0, longitude = 0):
        import urllib
        f = urllib.urlopen("http://ws.geonames.org/srtm3?lat="+str(latitude)+"&lng="+str(longitude))
        s = f.read()
        return s
    
class Settings:
    @cherrypy.expose
    def index(self):
        gh615Config = {}
        for section in gh615.config.sections():
            if not section in gh615Config:
                gh615Config[section] = {}
            for item, value in gh615.config.items(section):
                gh615Config[section][item] = value
        
        fileHandle = open('gh615.log')
        log = fileHandle.read()
        fileHandle.close()    

        template = TemplateHTML('settings/index.html')
        return template.render(cherrypy, gh615Config = gh615Config, log = log)    
    
    @cherrypy.expose
    def doUpdate(self, **kwargs):
        for arg in kwargs:
            (section, option) = arg.split('/')
            value = kwargs[arg]
            gh615.config.set(section, option, value)
        
        f = open("config.ini","w")
        try:
            gh615.config.write(f)
        finally:
            f.close()

        cherrypy.session['flash'] = 'settings updated successfully'
        raise cherrypy.HTTPRedirect('/settings')
    
    @cherrypy.expose
    def test(self):
        mofo = gh615Thread(gh615,'test')
        mofo.start()

        template = TemplateHTML('global/wait.html')
        return template.redirect(cherrypy, '/settings', 'test successful')  

    @cherrypy.expose
    def status(self):
        return str(gh615.STATUS)

#SITEMAP
root = Root()
root.waypoints = Waypoints()
root.tracks = Tracks()
root.settings = Settings()

if __name__ == '__main__':    
    cherrypy.config.update('cherrypy.conf')
    
    cherrypy.config.update({
        'tools.sessions.storage_path': gh615.getAppPrefix()+'\\gui\\_tmp',
        '/static/mootools.js': {'tools.staticfile.on': True,
                                'tools.staticfile.filename': gh615.getAppPrefix()+'/gui/static/mootools.js'},
        '/static/style.css': {'tools.staticfile.on': True,
                              'tools.staticfile.filename': gh615.getAppPrefix()+'/gui/static/style.css'}
    })
    
    cherrypy.quickstart(root,'',config="app.conf")