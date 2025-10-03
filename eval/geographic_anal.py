import networkx as nx
import itertools
import openrouteservice
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import great_circle, geodesic
from opencage.geocoder import OpenCageGeocode
from dotenv import load_dotenv
import os

class Geographic_Anal:
    def __init__(self, rag_itinerary : dict, other1 : dict, other2=None):
        """
        Parameters:
        dict rag_itinerary: the RAG-generated {day : [POI1, POI2, POI3]} dictionary with city already appended at the end of each POI
        dict other1: the deepseek {day : [POI1, POI2, POI3]} dictionary with city already appended at the end of each POI
        dict other2: the openai {day : [POI1, POI2, POI3]} dictionary with city already appended at the end of each POI
        """
        load_dotenv()
        self.geocoder = OpenCageGeocode(os.getenv("OPENCAGE_API_KEY"))
        self.rag_itinerary = self.get_lat_lon(rag_itinerary)
        self.other1 = self.get_lat_lon(other1)
        # self.other2 = self.get_lat_lon(other2)
        self.densities = {}
        self.backtracking = {}
        self.densities["rag_itinerary"] = self._compute_cluster_density(self.rag_itinerary)
        self.densities["deepseek_itinerary"] = self._compute_cluster_density(self.other1)
        # self.densities["openai_itinerary"] = self._compute_cluster_density(self.other2)
        self.backtracking["rag_itinerary"] = self.calculate_backtracking(self.rag_itinerary)
        self.backtracking["deepseek_itinerary"] = self.calculate_backtracking(self.other1)
        # self.backtracking["openai_itinerary"] = self.calculate_backtracking(self.other2)

    def get_lat_lon(self, itinerary):
        new_dict = {}
        for day, locs in itinerary.items():
            new_locs = []
            for loc in locs:
                result = self.geocoder.geocode(loc)
                tup = (result[0]['geometry']['lat'], result[0]['geometry']['lng'])
                new_locs.append(tup)
            new_dict[day] = new_locs
        print(new_dict)
        return new_dict

    def _compute_cluster_density(self, itinerary):
        """
        Compute the density of itinerary points by clustering per day and averaging distances within clusters.
        
        itinerary: Dictionary with keys as days and values as lists of (lat, lon) tuples.
        Returns: Average density score across all days.
        """
        densities = []
        for day, pois in itinerary.items():
            if len(pois) < 2:
                continue  # Skip days with single POI
            
            pois_array = np.array(pois)  # Convert list of tuples to NumPy array
            
            # Determine the number of clusters (usually sqrt(n) is a reasonable heuristic)
            num_clusters = max(1, int(np.sqrt(len(pois))))
            
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(pois_array)

            # Compute intra-cluster density
            cluster_densities = []
            for cluster in range(num_clusters):
                cluster_points = pois_array[labels == cluster]
                if len(cluster_points) > 1:
                    distances = [
                        great_circle(tuple(cluster_points[i]), tuple(cluster_points[j])).kilometers
                        for i in range(len(cluster_points)) for j in range(i + 1, len(cluster_points))
                    ]
                    avg_distance = np.mean(distances)
                    cluster_densities.append(avg_distance)

            if cluster_densities:
                densities.append(np.mean(cluster_densities))  # Average density for the day

        return 1/(np.mean(densities) if densities else float('inf'))
    
    def calculate_backtracking(self, itinerary):
        for pois in itinerary.values():
            G = nx.DiGraph()

            # Assign weights (distances in km)
            for i, poi1 in enumerate(pois):
                for j, poi2 in enumerate(pois):
                    if i != j:  # No self-loops
                        distance_km = geodesic(poi1, poi2).km
                        G.add_edge(i, j, weight=distance_km)

            # Detect backtracking cycles
            cycles = list(nx.simple_cycles(G))

            # Compute extra distance due to backtracking
            def total_path_distance(path, pois):
                """Compute total travel distance for a given path."""
                distance = 0
                for i in range(len(path) - 1):
                    distance += geodesic(pois[path[i]], pois[path[i + 1]]).km
                return distance

            # Find the optimal Hamiltonian path (TSP-style shortest path visiting all POIs)
            best_distance = float('inf')
            best_order = None

            for perm in itertools.permutations(range(len(pois))):
                dist = total_path_distance(perm, pois)
                if dist < best_distance:
                    best_distance = dist
                    best_order = perm

            # Compute actual itinerary distance
            actual_distance = total_path_distance(list(G.nodes), pois)

            # Calculate backtracking score: extra travel over the optimal path
            backtracking_score = actual_distance - best_distance

            # Print results
            return backtracking_score