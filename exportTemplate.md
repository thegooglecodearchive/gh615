# Export Templates #

If you wish to share your export templates with other users, feel free to do so here

**Changes for the 1.0 release**
The Template-API has changed. The new syntax is outlined below
  * Accesing track/trackpoint attributes is now done like so `trackpoint.latitude`, the old syntax `trackpoint['latitude']` can still be used
  * There is no `trackinfo` anymore, it is now part of the track. So `track['trackinfo']['date']` becomas `track.date`  or `track['date']`

## Template Syntax ##

```
$variable
$variable.attribute[item](some, function)(calls)
${expression} or <%py print expression %>
```

```
<% for item in seq %>
            ...
<% endfor %>
```

```
<% if expression %>
            ...
<% elif expression %>
            ...
<% else %>
            ...
<% endif %>
```

## Information available within the templates ##
### Track ###
For a track, the following information is available:

  * 'date': the time the track recording started, python datetime object
  * 'duration': the duration of the track, timedelta object
  * 'distance': the distance traveled, int, meter
  * 'calories': calories burned, int
  * 'topspeed': the top speed during the track, float, km/h
  * 'trackpointCount': the number of trackpoints the track consists of, int
  * 'trackpoints': the trackpoints the track consists of, list of `Trackpoint`
  * '**lapCount**' : the number of laps the track consits of, int (**Firmware V2 only**)
  * '**laps**' : the laps the track consits of, list of `Lap` (**Firmware V2 only**)

access these values like this: `$track.duration`

### Trackpoint ###
For a trackpoint, the following information is available:

  * 'latitude': the latitude of the trackpoint, decimal
  * 'longitude': the longitude of the trackpoint, decimal
  * 'altitude': the altitude of the trackpoint, int, meter
  * 'speed': the speed at the time of the trackpoint, float, km/h
  * 'heartrate': the heartrate at the time of the trackpoint, int, bpm
  * 'interval': the time from the previous treackpoint, python timedelta object
  * 'date': the time of the trackpoint recording, python datetime object

access to these values: `$trackpoints[i].latitude` or within a for-loop `$trackpoint.latitude`

### Lap ###

**available only with Firmware V2**

  * 'start': the time this lap starts, python datetime object
  * 'end': the time this lap ends, python datetime object
  * 'elapsed': the duration of this laps, python timedelta object
  * 'distance': the distance traveled during this lap, int, meter
  * 'calories': calories burned during this lap, int
  * 'startPoint': approximation of the Coordinate where this lap was started, Coordinate (has latitude and longitude)
  * 'endPoint':  approximation of the Coordinate where this lap was started, Coordinate (has latitude and longitude)

to format the date, see [the python strftime reference page](http://docs.python.org/lib/module-time.html), for example `$trackinfo.date.strftime("%Y-%m-%dT%H:%M:%SZ")` for ISO 8601

# templates available #

please check the [svn repository](http://gh615.googlecode.com/svn/trunk/globalsat/src/exportTemplates/) for the latest version of the exportTemplates