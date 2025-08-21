"""
TSP Solver using Google OR-Tools
================================
This module implements the Travelling Salesman Problem (TSP) solver
for the FindMyRoute project. It takes a list of tourist attractions
(lat/lon) and computes the most efficient visiting order.

Currently:
- Distance is computed using the Haversine formula (straight-line).
- OR-Tools is used to solve the TSP.
- Returns the optimal route order and total distance (km).

Future improvements:
- Replace Haversine distance with real travel times from OSM road network.
- Allow user preferences (cafés, POIs, etc.) to be integrated.
"""

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import math


def haversine_distance(coord1, coord2):
    """Compute distance (km) between two lat/lon points using Haversine formula."""
    R = 6371  # Earth radius in km
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def create_distance_matrix(locations):
    """Create a 2D distance matrix for the given list of locations."""
    size = len(locations)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = int(haversine_distance(locations[i], locations[j]) * 1000)  # meters
    return matrix


def solve_tsp(locations, start_index=0):
    """
    Solve the TSP for a list of locations.
    
    Args:
        locations (list): List of (lat, lon) tuples.
        start_index (int): Index of starting point (default=0).
    
    Returns:
        route (list): Ordered list of indices for visiting.
        total_distance (float): Total distance of route in km.
    """
    # Build distance matrix
    distance_matrix = create_distance_matrix(locations)

    # Create routing index manager
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, start_index)

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Distance callback
    def distance_callback(from_index, to_index):
        return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Set arc cost
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # First solution strategy
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        raise ValueError("No solution found for TSP!")

    # Extract route
    index = routing.Start(0)
    route = []
    total_distance = 0
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)

    # Convert meters → km
    return route, total_distance / 1000.0


if __name__ == "__main__":
    # Example run
    attractions = [
        (47.8095, 13.0550),  # Salzburg city center
        (47.8021, 13.0415),  # Mirabell Palace
        (47.7972, 13.0465),  # Salzburg Cathedral
        (47.8005, 13.0430),  # Mozart's Birthplace
    ]
    route, dist = solve_tsp(attractions)
    print("Optimized visiting order (by index):", route)
    print("Total distance (km):", round(dist, 2))
