import googlemaps
from datetime import datetime

API_KEY = "AIzaSyBhsnP2E1cf1JYS5UX_7liJSY69PtZeh8I"

def get_route(start, end, num_points):
    # Replace the API key with your own
    gmaps = googlemaps.Client(key=API_KEY)

    # Make the request for directions
    now = datetime.now()
    directions_result = gmaps.directions(start, end, mode="driving", departure_time=now)

    # Get the polyline from the first route in the result
    route = directions_result[0]['overview_polyline']['points']

    # Decode the polyline to get the coordinates
    coordinates = googlemaps.convert.decode_polyline(route)

    # Calculate the number of steps based on the number of points requested
    num_steps = int(len(coordinates) / num_points)

    # Return the requested number of intermittent points
    lat = []
    lng = []
    for i in range(0, num_points):
        point = coordinates[i * num_steps]
        lat.append(point['lat'])
        lng.append(point['lng'])

    return lat,lng

# Example usage
start = 'New York, NY'
end = 'Los Angeles, CA'
num_points = 5

lat,lng = get_route(start, end, num_points)
print(lat)
print(lng)