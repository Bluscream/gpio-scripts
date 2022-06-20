#!/usr/bin/env python3
import struct
import RPi.GPIO as GPIO
from time import sleep
from urllib import request
from urllib.parse import urlencode, quote_plus
from subprocess import run, PIPE
import smbus2 as smbus
from os import path, remove

GPIO_PORT = 26
I2C_ADDR = 0x36
PLD_PIN = 6

metrics_file = "/var/www/html/metrics/x728"
metrics = """
# HELP node_ac_power A/C Power
# TYPE node_ac_power gauge
node_ac_power {ac_power}
# HELP node_battery_capacity Backup battery capacity
# TYPE node_battery_capacity gauge
node_battery_capacity {battery_capacity}
# HELP node_battery_voltage Backup battery voltage
# TYPE node_battery_voltage gauge
node_battery_voltage {battery_voltage}
# HELP node_cpu_voltage CPU Voltage
# TYPE node_cpu_voltage gauge
node_cpu_voltage {cpu_voltage}
"""

def write_metrics(battery_capacity, battery_voltage, ac_power_loss, cpu_voltage):
    with open(metrics_file, 'w+', encoding = 'utf-8') as f:
        f.write(metrics.format(battery_capacity=battery_capacity,battery_voltage=battery_voltage,ac_power=int(not ac_power_loss),cpu_voltage=cpu_voltage))

def automagic(path = "/", query = {}):
    try: f = request.urlopen(f'http://192.168.2.38:1122/{path}?password=gast&{urlencode(query, quote_via=quote_plus)}', timeout=.5)
    except: pass

BUZZER_PIN = 20
def buzz(duration_ms=200,delay_ms=0):
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.output(BUZZER_PIN, 1)
    sleep(duration_ms/1000)
    GPIO.output(BUZZER_PIN, 0)
    sleep(delay_ms/1000)

def get_cpu_voltage():
    return run(['vcgencmd', 'measure_volts', "core"], stdout=PIPE).stdout.decode('utf-8').replace("volt=","")[:-2]

def readBus(bus, pin):
     read = bus.read_word_data(I2C_ADDR, pin)
     return struct.unpack("<H", struct.pack(">H", read))[0]

def readVoltage(bus):
     return "%5.2f" % (readBus(bus, 2) * 1.25 / 1000 / 16)

def readCapacity(bus):
     return "%5i" % (readBus(bus, 4) / 256 )


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PLD_PIN, GPIO.IN)
GPIO.setup(GPIO_PORT, GPIO.OUT)

bus = smbus.SMBus(1) # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
had_power_loss = False
firstrun = True
while True:
    ac_power_loss = GPIO.input(PLD_PIN)
    battery_capacity = readCapacity(bus).strip()
    battery_voltage = readVoltage(bus).strip()
    cpu_voltage = get_cpu_voltage().strip()
    write_metrics(battery_capacity, battery_voltage, ac_power_loss, cpu_voltage)
    if ac_power_loss == 0 and had_power_loss:
        had_power_loss = False
        print("AC Power OK")
        buzz(50,50)
        buzz(50)
    elif ac_power_loss == 1 and not had_power_loss:
        had_power_loss = True
        print("Power Supply A/C Lost")
        buzz()
        automagic("screen/on")
        title = "EMERGENCY POWER LOSS"
        message = f"Automater A/C power lost!\n\nBattery: {battery_capacity}%\nVoltage: {battery_voltage}V\n\nCPU Voltage: {cpu_voltage}V"
        automagic("popup/show", {"title": title, "message": message}) #, "action": "http://automater.pi/metrics"})
        automagic("notification/create", {"title": title, "message": message, "icon": "app.icon://com.android.cellbroadcastreceiver"})
        automagic("vibrate", {"pattern": "1000,1000", "repeat": "2"})
        sleep(28)
    if firstrun and ac_power_loss: break
    firstrun = False
    sleep(2)

if path.exists(metrics_file): remove(metrics_file)