import datetime
import time
import math
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_mpu6050
import RPi.GPIO as GPIO

# Define the pins for sensors
REED_PIN = 18
REGEN_PIN = 23

# Define the regenerative braking threshold
REGEN_THRESHOLD = -2.5

# Initialize REGEN_FLAG to 0 to prevent system from entering uncontrolled regenerative stage
REGEN_FLAG = False

# Define the wheel rim size(diameter) in inches
WHEEL_SIZE = 26

# Get the distance travelled per revolution in meters
DIST_PER_REV = WHEEL_SIZE * 0.0254 * math.pi

# Initialize distance travelled with zero at the beginning
DistanceTravelled = 0

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize MPU6050 sensor
mpu = adafruit_mpu6050.MPU6050(i2c)

# Initialize ADS1115 sensor
ads = ADS.ADS1115(i2c)
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Initialize GPIO pins
GPIO.setup(REED_PIN, GPIO.IN)
GPIO.setup(REGEN_PIN, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

# Set the initial value foe previous time
PreviousTime = datetime.datetime.now()

AverageSpeed = 0

# Read data from sensors
while True:
    
    # Get the X-Axis acceleration to compute the slope for regenerative braking
    accel_x, null, null = mpu.acceleration
    
    # Get voltage reading from the battery and capacitor bank
    voltage0 = chan0.voltage
    voltage1 = chan1.voltage
    voltage2 = chan0.value
    
#    print("Acceleration (m/s^2): ({0:0.2f})".format(accel_x))
#    print("Voltage: {0:0.2f}V {0:0.2f}V {0:0.2f}V".format(voltage0, voltage1, voltage2))
    
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
            
    if (accel_x <= REGEN_THRESHOLD) and (not(REGEN_FLAG)):
        print("REGEN HIGH")
        REGEN_FLAG = True
        GPIO.output(REGEN_PIN, GPIO.HIGH)
    if (accel_x > REGEN_THRESHOLD) and (REGEN_FLAG):
        print("REGEN LOW")
        REGEN_FLAG = False
        GPIO.output(REGEN_PIN, GPIO.LOW)
