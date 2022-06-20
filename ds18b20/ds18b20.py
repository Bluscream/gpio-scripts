#!/usr/bin/env python3
from urllib import request
from urllib.parse import quote_plus, urlencode
import RPi.GPIO as GPIO
from time import sleep
from os import path, remove

silent = False

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq2_dpin = 24
mq2_apin = 0

BUZZER_PIN = 20
def buzz(duration_ms=200,delay_ms=0):
        if not silent:
                GPIO.setup(BUZZER_PIN, GPIO.OUT)
                GPIO.output(BUZZER_PIN, 1)
                sleep(duration_ms/1000)
                GPIO.output(BUZZER_PIN, 0)
        sleep(delay_ms/1000)
metrics_file = "/var/www/html/metrics/ds18b20"
metrics = """
# HELP room_ambient_temperature_celsius Room ambient temperature (Celsius)
# TYPE room_ambient_temperature_celsius gauge
room_ambient_temperature_celsius{{sensor="DS18B20", room="Room 1"}} {temperature_c}
"""

def write_metrics(temperature_c, temperature_f):
        with open(metrics_file, 'w+', encoding = 'utf-8') as f:
                f.write(metrics.format(temperature_c=temperature_c,temperature_f=temperature_f))

from base64 import b64decode as b64d
def automagic(path = "/", query = {}):
        try: request.urlopen(f'http://192.168.2.38:1122/{path}?password={b64d("Z2FzdA")}&{urlencode(query, quote_via=quote_plus)}', timeout=.5)
        except: pass

# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from glob import glob

base_dir = '/sys/bus/w1/devices/'
device_folder = glob(base_dir + '28*')
print(device_folder)
if len(device_folder) < 1:
        if path.exists(metrics_file): remove(metrics_file)
device_file = device_folder[0] + '/w1_slave'

def read_temp_raw():
        lines = []
        with open(device_file, 'r') as f:
                lines = f.readlines()
        return lines

def read_temp():
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
                sleep(0.2)
                lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = (float(temp_string) / 1000.0) - 2
                temp_f = temp_c * 9.0 / 5.0 + 32.0
                return temp_c, temp_f

count = 0

while True:
        count += 1
        temp = read_temp()
        print(temp)
        if count > 1:
                write_metrics(temp[0], temp[1])
                count = 0
        sleep(.5)

if path.exists(metrics_file): remove(metrics_file)