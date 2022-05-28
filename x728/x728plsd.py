#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time



GPIO.setmode(GPIO.BCM)
GPIO.setup(6, GPIO.IN)
GPIO.setup(26, GPIO.OUT)
GPIO.setwarnings(False)

def readVoltage(bus):

     address = I2C_ADDR
     read = bus.read_word_data(address, 2)
     swapped = struct.unpack("<H", struct.pack(">H", read))[0]
     voltage = swapped * 1.25 /1000/16
     return voltage

def readCapacity(bus):

     address = I2C_ADDR
     read = bus.read_word_data(address, 4)
     swapped = struct.unpack("<H", struct.pack(">H", read))[0]
     capacity = swapped/256
     return capacity

def my_callback(channel):
    if GPIO.input(6):     # if port 6 == 1
        print ("---AC Power Loss OR Power Adapter Failure---")
        print ("Shutdown in 5 seconds")
        time.sleep(5)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(3)
        GPIO.output(26, GPIO.LOW)

#time.sleep(2)

    else:                  # if port 6 != 1
        print ("---AC Power OK,Power Adapter OK---")

GPIO.add_event_detect(6, GPIO.BOTH, callback=my_callback)
input("Testing Started")

