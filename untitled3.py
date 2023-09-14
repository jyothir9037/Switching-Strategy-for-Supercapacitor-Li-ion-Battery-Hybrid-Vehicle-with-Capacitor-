import RPi.GPIO as GPIO
import time

# LED

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

while True:
    GPIO.output(18, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(18, GPIO.LOW)
    time.sleep(1)

GPIO.cleanup()


# Pot
import RPi.GPIO as GPIO
import time

# Set the pin numbering scheme to BCM
GPIO.setmode(GPIO.BCM)

# Define the pin number for the potentiometer input
potentiometer_pin = 18

# Set up the potentiometer pin as an input
GPIO.setup(potentiometer_pin, GPIO.IN)

# Read the potentiometer input in a loop
try:
    while True:
        # Read the analog value from the potentiometer pin
        value = GPIO.input(potentiometer_pin)
        
        # Print the analog value
        print("Analog Value:", value)
        
        # Wait for a short period before reading the input again
        time.sleep(0.1)

# Clean up the GPIO pins on exit
except KeyboardInterrupt:
    GPIO.cleanup()
