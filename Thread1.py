import requests
import json
import googlemaps
from datetime import datetime

API_KEY = "AIzaSyBhsnP2E1cf1JYS5UX_7liJSY69PtZeh8I"

AverageSpeed = 6.94444
SlopeLimit = 1

def getDistance(origin, destination, API_KEY):
    gmaps = googlemaps.Client(key=API_KEY)

    # Make the request for directions
    now = datetime.now()
    directions_result = gmaps.directions(origin, destination, mode="driving", departure_time=now)

    # Get the distance from the first route in the result
    distance = directions_result[0]['legs'][0]['distance']['value']

    # Return the distance in meter(s)
    return distance

def getRouteMatrix(origin, destination, num_intermediate_points, API_KEY):
    gmaps = googlemaps.Client(key=API_KEY)

    # Make the request for directions
    now = datetime.now()
    directions_result = gmaps.directions(origin, destination, mode="driving", departure_time=now)

    # Get the polyline from the first route in the result
    route = directions_result[0]['overview_polyline']['points']

    # Decode the polyline to get the coordinates
    coordinates = googlemaps.convert.decode_polyline(route)

    # Calculate the number of steps based on the number of points requested
    num_steps = int(len(coordinates) / num_intermediate_points)

    # Return the requested number of intermittent points
    lat = []
    lng = []
    for i in range(0, num_intermediate_points):
        point = coordinates[i * num_steps]
        lat.append(point['lat'])
        lng.append(point['lng'])

    return lat,lng

def getElevationVector(latitude, longitude, API_KEY):
    # Define the API endpoint
    endpoint = "https://maps.googleapis.com/maps/api/elevation/json?"
    
    # Define the API parameters
    params = {
        "locations": f"{latitude},{longitude}",
        "key": API_KEY
    }
    
    # Send the API request and retrieve the response
    response = requests.get(endpoint, params=params)
    data = json.loads(response.text)
    
    # Extract the elevation from the API response
    elevation = data["results"][0]["elevation"]
    
    # Return the elevation
    return elevation

def getGradient(elevation):
    gradient = []
    
    # Get the slope/delta of elevation vector
    for i in range(0, (len(elevation)-1)):
        slope = elevation[i+1] - elevation[i]
        gradient.append(slope)    
    return gradient

def getChargeTime(gradient, AverageSpeed): 
    charge_matrix = []
    
    for i in range(0, len(gradient)):
        
        # If value of gradient exceeds SlopeLimit, then the capacitor needs to be charged
        if(gradient[i] > SlopeLimit):
            charge_point = AverageSpeed * 200
            
            if((i - charge_point) < 0):
                if not -1 in charge_matrix:
                    charge_matrix.append(-1)
            else:
                try:
                    if not(gradient[i-1] > SlopeLimit):
                        charge_matrix.append(charge_point)
                except:
                    pass 
    return charge_matrix
    
def getDischargeMatrix(gradient):
    discharge_matrix = []
    
    for i in range(0, len(gradient)):
        
        # If value of gradient exceeds SlopeLimit, then the capacitor needs to be discharged
        if(gradient[i] > SlopeLimit):
            try:
                if not(gradient[i-1] > SlopeLimit):
                    discharge_matrix.append(i)
            except:
                pass
                
    return discharge_matrix
    
def getID():
    # Set the origin and destination
    origin = input("Origin: ")
    destination = input("Destination: ")
    
    # Get the number of intermediate points
    num_intermediate_points = getDistance(origin, destination, API_KEY)
    print(num_intermediate_points)
    num_intermediate_points = 10
    
    # Get the latitude and longitude of intermediate points
    lat, lng = getRouteMatrix(origin, destination, num_intermediate_points, API_KEY)
    
    # Get the elevation of intermediate points
    elevation = []
    for i in range(0, len(lat)):
        elevation.append(getElevationVector(lat[i], lng[i], API_KEY))
    
    # Get the slope of intermediate points
    gradient = getGradient(elevation)
        
    # Get the charge matrix
    charge_matrix = getChargeTime(gradient, AverageSpeed)
    discharge_matrix = getDischargeMatrix(gradient)
    
    print(elevation)
    print(gradient)
    print(charge_matrix)
    print(discharge_matrix)
    
getID()
