class Poi:
    def __init__(self, name, lat, lon, desc, dur, day):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.desc = desc
        self.dur = dur
        self.day = day
    
    def __str__(self):
        return self.name + " at (" + str(self.lat) + ", " + str(self.lon) + ") on day " + str(self.day) + " of duration " + str(self.dur) + " hours with description "  #+ self.desc