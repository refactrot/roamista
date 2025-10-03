from collections import defaultdict

class Itinerary:
    def __init__(self, pois : list):
        self.pois = pois
        if len(pois) == 0:
            self.length = "None"
        else:
            dur = pois[len(pois) - 1].day
            self.length = dur if dur != 0 else "any"
    
    def group_pois_by_day(self):
        grouped_pois = defaultdict(dict)

        for poi in self.pois:
            grouped_pois[poi.day][poi.name] = {
                "desc": poi.desc,
                "lat": poi.lat,
                "lon": poi.lon,
                "dur": poi.dur
            }

        return {"pois": dict(grouped_pois)}