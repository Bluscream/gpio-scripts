#!/usr/bin/env python3
from urllib import request
from time import sleep
import board
import adafruit_dht
import RPi.GPIO as GPIO
 
# Initial the dht device, with data pin connected to:
# dhtDevice = adafruit_dht.DHT22(board.D4)
 
# you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
dhtDevice = adafruit_dht.DHT11(board.D4, use_pulseio=False)

BUZZER_PIN = 20
def buzz(duration_ms=200,delay_ms=0):
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.output(BUZZER_PIN, 1)
    sleep(duration_ms/1000)
    GPIO.output(BUZZER_PIN, 0)
    sleep(delay_ms/1000)

metrics = """
# HELP room_ambient_temperature_celsius Room ambient temperature (Celsius)
# TYPE room_ambient_temperature_celsius gauge
room_ambient_temperature_celsius {temperature_c}
# HELP room_ambient_temperature_fahrenheit Room ambient temperature (Fahrenheit)
# TYPE room_ambient_temperature_fahrenheit gauge
room_ambient_temperature_fahrenheit {temperature_f}
# HELP room_ambient_humidity Room ambient humidity
# TYPE room_ambient_humidity gauge
room_ambient_humidity {humidity}
"""

def write_metrics(temperature_c, temperature_f, humidity):
    with open("/var/www/html/metrics/dht11", 'w+', encoding = 'utf-8') as f:
        f.write(metrics.format(temperature_c=temperature_c,temperature_f=temperature_f,humidity=humidity))

def automagic(path = "/", query = {}):
    try: f = request.urlopen(f'http://192.168.2.38:1122/{path}?password=buffalo911&{urlencode(query, quote_via=quote_plus)}', timeout=.5)
    except: pass

while True:
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        print(
            "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                temperature_f, temperature_c, humidity
            )
        )
 
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error
 
    time.sleep(1.0)