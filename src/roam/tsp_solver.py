import math
from opencage.geocoder import OpenCageGeocode
import os
from dotenv import load_dotenv

class TSPSolver:
    @staticmethod
    def _haversine(coord1, coord2):
        """Calculate great-circle distance between two (lat, lon) points in km."""
        R = 6371  # Earth radius in km
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

    @staticmethod
    def _nearest_neighbor(points):
        """Nearest neighbor heuristic for TSP."""
        if not points:
            return []

        unvisited = points[:]
        tour = [unvisited.pop(0)]  # start at first point

        while unvisited:
            last = tour[-1]
            nearest = min(unvisited, key=lambda p: TSPSolver._haversine(last, p))
            tour.append(nearest)
            unvisited.remove(nearest)

        return tour

    @staticmethod
    def _two_opt(route):
        """2-opt optimization to improve TSP route."""
        best = route
        improved = True
        while improved:
            improved = False
            for i in range(1, len(best) - 2):
                for j in range(i + 1, len(best)):
                    if j - i == 1:
                        continue
                    new_route = best[:]
                    new_route[i:j] = best[j-1:i-1:-1]  # reverse segment
                    if TSPSolver._route_distance(new_route) < TSPSolver._route_distance(best):
                        best = new_route
                        improved = True
            route = best
        return best

    @staticmethod
    def _route_distance(route):
        return sum(TSPSolver._haversine(route[i], route[i+1]) for i in range(len(route)-1))
    
    @staticmethod
    def _to_lat_lon(pois):
        load_dotenv()
        geocoder = OpenCageGeocode(os.getenv("OPENCAGE_API_KEY"))
        new_dict = {}
        for day, locs in pois.items():
            new_locs = []
            for loc in locs:
                result = geocoder.geocode(loc)
                tup = (result[0]['geometry']['lat'], result[0]['geometry']['lng'])
                new_locs.append(tup)
            new_dict[day] = new_locs
        return new_dict

    @staticmethod
    def _to_text(pois):
        """
        Convert {day: [(lat, lon), ...]} into {day: ["landmark/POI name", ...]}
        using reverse geocoding. Prioritizes famous places / attractions.
        """
        load_dotenv()
        geocoder = OpenCageGeocode(os.getenv("OPENCAGE_API_KEY"))
        new_dict = {}

        for day, coords in pois.items():
            new_locs = []
            for lat, lon in coords:
                result = geocoder.reverse_geocode(lat, lon, no_annotations=1)
                if result and len(result) > 0:
                    components = result[0].get("components", {})

                    # Try to pick the most landmark-like field
                    place = (
                        components.get("attraction")
                        or components.get("tourism")
                        or components.get("building")
                        or components.get("theatre")
                        or components.get("museum")
                        or components.get("historic")
                        or components.get("stadium")
                        or components.get("park")
                        or components.get("city")
                        or result[0].get("formatted")  # fallback
                    )
                else:
                    place = f"{lat}, {lon}"  # fallback if nothing found

                new_locs.append(place)
            new_dict[day] = new_locs

        return new_dict
    
    @staticmethod
    def rearrange_pois(itinerary : dict):
        geocoder = OpenCageGeocode(os.getenv("OPENCAGE_API_KEY"))
        new_dict = {}
        for day, locs in itinerary.items():
            new_locs = []
            for loc in locs:
                result = geocoder.geocode(loc)
                tup = (result[0]['geometry']['lat'], result[0]['geometry']['lng'])
                new_locs.append(tup)
            new_dict[day] = new_locs
        
        return new_dict

    @staticmethod
    def reorder(data):
        """Rearrange points in each dict key using TSP heuristic."""
        converted_data = TSPSolver._to_lat_lon(data)
        reordered = {}
        for k, points in converted_data.items():
            nn_path = TSPSolver._nearest_neighbor(points)
            optimized = TSPSolver._two_opt(nn_path)
            reordered[k] = optimized
        return reordered, TSPSolver._to_text(reordered)
