
```
<<?= str('?') ?>xml version="1.0" encoding="UTF-8"?>
<gpx version="1.0"
	creator="GH615 Supertool"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns="http://www.topografix.com/GPX/1/0"
	xsi:schemaLocation="http://www.topografix.com/GPX/1/0
						http://www.topografix.com/GPX/1/0/gpx.xsd">

<time><?= trackinfo['date'].strftime("%Y-%m-%dT%H:%M:%SZ") ?></time>
 
<trk>
	<trkseg>
	<? for trackpoint in trackpoints: ?>
		<trkpt lat="<?= trackpoint['latitude'] ?>" lon="<?= trackpoint['longitude'] ?>">
			<ele><?= trackpoint['altitude'] ?></ele>
			<speed><?= trackpoint['speed'] ?></speed>
			<time><?= trackpoint['date'].strftime("%Y-%m-%dT%H:%M:%SZ") ?></time>
		</trkpt>
	<? end ?>
	</trkseg>
</trk>

</gpx>
```