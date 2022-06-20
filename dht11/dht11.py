#!/usr/bin/env python3
from urllib import request
from urllib.parse import quote_plus, urlencode
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
room_ambient_temperature_celsius{{sensor="DHT11", room="Room 1"}} {temperature_c}
# HELP room_ambient_humidity Room ambient humidity
# TYPE room_ambient_humidity gauge
room_ambient_humidity {humidity}
"""

def write_metrics(temperature_c, humidity):
    with open("/var/www/html/metrics/dht11", 'w+', encoding = 'utf-8') as f:
        f.write(metrics.format(temperature_c=temperature_c,humidity=humidity))

def automagic(path = "/", query = {}):
    try: f = request.urlopen(f'http://192.168.2.38:1122/{path}?password=gast&{urlencode(query, quote_via=quote_plus)}', timeout=.5)
    except: pass

detections_temp = 0
detections_humidity = 0
errors = 0
limit_temp_c = 50
limit_humidity = 50
firstrun = True
while True:
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature - 5
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        write_metrics('{:.1f}'.format(temperature_c), humidity)
        heat_alarm = temperature_c > limit_temp_c
        humid_alarm = humidity > limit_humidity
        if heat_alarm or humid_alarm:
            message = "Temp: {:.1f}°C / {:.1f}°F\n\nHumidity: {}% ".format(temperature_f, temperature_c, humidity)
            title = "Alerting "
            if heat_alarm and not detections_temp:
                detections_temp += 1
                buzz(100,50)
                title += "Heat "
            if humid_alarm and not detections_humidity:
                detections_humidity += 1
                buzz(50,100)
                title += "Humidity"
            automagic("screen/on")
            automagic("popup/show", {"title": title, "message": message}) #, "action": "http://automater.pi/metrics"})
            automagic("notification/create", {"title": title, "message": message, "icon": "app.icon://com.android.cellbroadcastreceiver"})
            automagic("vibrate", {"pattern": "1000,1000", "repeat": "2"})
            if firstrun: break
        else:
            detections_temp = 0
            detections_humidity = 0
        errors = 0

    except RuntimeError as error:
        errors += 1
        print(f"[{errors}] {error.args[0]}")
        sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        buzz(1000)
        automagic("notification/create", {"title": "DHT11 SHUT DOWN", "message": f"Too many errors: {errors}\n\n{error.args[0]}", "icon": "app.icon://com.android.cellbroadcastreceiver"})
        raise error
    sleep(1.0)
    firstrun = False