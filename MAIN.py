import requests
import json
import googlemaps
import datetime
import time
import math
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
import adafruit_mpu6050
import RPi.GPIO as GPIO

import os
from dotenv import set_key
from dotenv import load_dotenv
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime as dt

API_KEY = "AIzaSyBhsnP2E1cf1JYS5UX_7liJSY69PtZeh8I"

# Define global variable AverageSpeed
AverageSpeed = 0

# Define the pins for sensors
REED_PIN = 18
REGEN_PIN = 23
DISCHGPIN = 24

# Define the Slope Limit
SLOPE_LIMIT = 1

# Define the regenerative braking threshold
REGEN_THRESHOLD = -2.5

# Define the wheel rim size(diameter) in inches
WHEEL_SIZE = 26

def getDistance(origin, destination, API_KEY):
    gmaps = googlemaps.Client(key=API_KEY)

    # Make the request for directions
    now = dt.now()
    directions_result = gmaps.directions(origin, destination, mode="driving", departure_time=now)

    # Get the distance from the first route in the result
    distance = directions_result[0]['legs'][0]['distance']['value']

    # Return the distance in meter(s)
    return distance

def getRouteMatrix(origin, destination, num_intermediate_points, API_KEY):
    gmaps = googlemaps.Client(key=API_KEY)

    # Make the request for directions
    now = dt.now()
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
        if(gradient[i] > SLOPE_LIMIT):
            charge_point = AverageSpeed * 200
            
            if((i - charge_point) < 0):
                if not -1 in charge_matrix:
                    charge_matrix.append(-1)
            else:
                try:
                    if not(gradient[i-1] > SLOPE_LIMIT):
                        charge_matrix.append(charge_point)
                except:
                    pass 
    return charge_matrix
    
def getDischargeMatrix(gradient):
    discharge_matrix = []
    
    for i in range(0, len(gradient)):
        
        # If value of gradient exceeds SlopeLimit, then the capacitor needs to be discharged
        if(gradient[i] > SLOPE_LIMIT):
            try:
                if not(gradient[i-1] > SLOPE_LIMIT):
                    discharge_matrix.append(i)
            except:
                pass
                
    return discharge_matrix
    
def getMapData():
    # Set the origin and destination
    origin = input("Origin: ")
    destination = input("Destination: ")
    
    # Get the number of intermediate points
    num_intermediate_points = getDistance(origin, destination, API_KEY)
    print("Number of intermediate points : " + str(num_intermediate_points))
    num_intermediate_points = 10
    print("Number of intermediate points set to 10 due to budget constraints")
    
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
    
    print("Elevation Matrix : ")
    print(elevation)
    print("Gradient Matrix : ")
    print(gradient)
    print("Charge Matrix : ")
    print(charge_matrix)
    print("Discharge Matrix : ")
    print(discharge_matrix)
    
    return charge_matrix, discharge_matrix
    
def control(charge_matrix, discharge_matrix, AverageSpeed):
    # Get the distance travelled per revolution in meters
    DIST_PER_REV = WHEEL_SIZE * 0.0254 * math.pi
    print("Distance Per revolution: " + str(DIST_PER_REV))
    
    # Initialize I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # Initialize MPU6050 sensor
    mpu = adafruit_mpu6050.MPU6050(i2c)

    # Initialize ADS1115 sensor
    ads = ADS.ADS1115(i2c)
    channel0 = AnalogIn(ads, ADS.P0)

    # Set up GPIO mode
    GPIO.setmode(GPIO.BCM)

    # Initialize GPIO pins
    GPIO.setup(REED_PIN, GPIO.IN)
    GPIO.setup(REGEN_PIN, GPIO.OUT)
    GPIO.setup(DISCHGPIN, GPIO.OUT)

    # Set the initial value foe previous time
    PreviousTime = datetime.datetime.now()
    
    # Initialize distance travelled with zero at the beginning
    DistanceTravelled = 0
    
    # Initialize REGEN_FLAG to 0 to prevent system from entering uncontrolled regenerative stage
    REGEN_FLAG = False
    DISCHGFLAG = False
    
    if -1 in charge_matrix:
        GPIO.output(REGEN_PIN, GPIO.HIGH)
        REGEN_FLAG = True
        print("Initial Charge Begin..")
        time.sleep(500)
        GPIO.output(REGEN_PIN, GPIO.LOW)
        REGEN_FLAG = False
        del charge_matrix[0]
        print("Initial Charge End..")

    while True:
        # Get the X-Axis acceleration to compute the slope for regenerative braking
        accel_x, null, null = mpu.acceleration
        
        # Get the input from the reed switch
        ReedIn = GPIO.input(REED_PIN)

        if ReedIn == GPIO.HIGH:
            # Get the time delta to calculate the speed values 
            CurrentTime = datetime.datetime.now()
            DeltaTime = (CurrentTime - PreviousTime).total_seconds()
            
            # Calculate the current speed of the vehicle
            CurrentSpeed = DIST_PER_REV / DeltaTime
            AverageSpeed = ( AverageSpeed + CurrentSpeed ) / 2
            
            #Increase the travel distance
            DistanceTravelled = DistanceTravelled + DIST_PER_REV
            
            # Set the previous time as current time for the next iteration
            PreviousTime = CurrentTime
            
            print("CurrentSpeed: {0:0.2f}".format(CurrentSpeed))
            print("AverageSpeed: {0:0.2f}".format(AverageSpeed))
            print("DistanceTravelled: {0:0.2f}".format(DistanceTravelled))
            
            try: 
                if DistanceTravelled >= charge_matrix[0]:
                    if REGEN_FLAG == False:
                        del charge_matrix[0]
                        REGEN_FLAG = True
                        GPIO.output(REGEN_PIN, GPIO.HIGH)
                        print("Capacitor Bank Charging Start")
                        time.sleep(200)
                        GPIO.output(REGEN_PIN, GPIO.LOW)
                        REGEN_FLAG = False
                        print("Capacitor Bank Charging End")
                    
                if DistanceTravelled >= discharge_matrix[0]:
                    del discharge_matrix[0]
                    DISCHGFLAG = True
                    GPIO.output(DISCHGPIN, GPIO.HIGH)
                    print("Capacitor Bank Discharging Start")
                    capacitor_voltage = channel0.voltage
                    while ((capacitor_voltage * 5.86) > 15):
                        time.sleep(1)
                        # Get voltage reading from the battery and capacitor bank
                        capacitor_voltage = channel0.voltage
                    GPIO.output(DISCHGPIN, GPIO.LOW)
                    DISCHGFLAG = False
                    print("Capacitor Bank Discharging End")
                    
            except:
                pass
                
        if (accel_x <= REGEN_THRESHOLD) and (not(REGEN_FLAG)) and (not(DISCHGFLAG)):
            REGEN_FLAG = True
            GPIO.output(REGEN_PIN, GPIO.HIGH)
            print("REGEN HIGH")
        
        if (accel_x > REGEN_THRESHOLD) and (REGEN_FLAG):
            REGEN_FLAG = False
            GPIO.output(REGEN_PIN, GPIO.LOW)
            print("REGEN LOW")
            
        if not discharge_matrix:
            return AverageSpeed
    
    return AverageSpeed
   
def getAverageSpeed():
    load_dotenv()
    AverageSpeed = os.getenv('AverageSpeed')
    AverageSpeed = float(AverageSpeed)
    return AverageSpeed

def setAverageSpeed(AverageSpeed):
    with open(".env", "w") as f:
        f.write("AverageSpeed = " + str(AverageSpeed))

def RUKA_CHAN():
    AverageSpeed = getAverageSpeed()
    print("Current Average Speed: " + str(AverageSpeed))
    charge_matrix, discharge_matrix = getMapData()
    AverageSpeed = control(charge_matrix, discharge_matrix, AverageSpeed)
    setAverageSpeed(AverageSpeed)
    
def initializeRUKA():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[;31m ███████████  ███████████      ███████          █████ ██████████   █████████  ███████████           ███████████   █████  █████ █████   ████   █████████    ")
    print("░░███░░░░░███░░███░░░░░███   ███░░░░░███       ░░███ ░░███░░░░░█  ███░░░░░███░█░░░███░░░█          ░░███░░░░░███ ░░███  ░░███ ░░███   ███░   ███░░░░░███  ")
    print(" ░███    ░███ ░███    ░███  ███     ░░███       ░███  ░███  █ ░  ███     ░░░ ░   ░███  ░            ░███    ░███  ░███   ░███  ░███  ███    ░███    ░███  ")
    print(" ░██████████  ░██████████  ░███      ░███       ░███  ░██████   ░███             ░███               ░██████████   ░███   ░███  ░███████     ░███████████  ")
    print(" ░███░░░░░░   ░███░░░░░███ ░███      ░███       ░███  ░███░░█   ░███             ░███               ░███░░░░░███  ░███   ░███  ░███░░███    ░███░░░░░███  ")
    print(" ░███         ░███    ░███ ░░███     ███  ███   ░███  ░███ ░   █░░███     ███    ░███               ░███    ░███  ░███   ░███  ░███ ░░███   ░███    ░███  ")
    print(" █████        █████   █████ ░░░███████░  ░░████████   ██████████ ░░█████████     █████    █████████ █████   █████ ░░████████   █████ ░░████ █████   █████ ")
    print("░░░░░        ░░░░░   ░░░░░    ░░░░░░░     ░░░░░░░░   ░░░░░░░░░░   ░░░░░░░░░     ░░░░░    ░░░░░░░░░ ░░░░░   ░░░░░   ░░░░░░░░   ░░░░░   ░░░░ ░░░░░   ░░░░░  ")
    print(" ")
    print("\033[;7m \033[1;36m v3.1.0                                           \033[0;34m  A Project By Team DEVIANTS                  \033[;7m \033[1;36m by  KANNAPPI, INDIAN_BOBAN, POOMBATTA, THE_JOULE_THIEF ")
    print("\033[0;0m")

if __name__ == "__main__":
    initializeRUKA()
    RUKA_CHAN()
