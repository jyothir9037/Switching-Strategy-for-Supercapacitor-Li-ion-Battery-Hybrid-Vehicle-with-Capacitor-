from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS
import board
import busio
import RPi.GPIO as GPIO
import time

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
channel0 = AnalogIn(ads, ADS.P0)

while True:
	capacitor_voltage = channel0.voltage
	print("MES V IN : " + str(capacitor_voltage))
	print("CAP VOLT : " + str(capacitor_voltage * 5.86))
	time.sleep(1)
