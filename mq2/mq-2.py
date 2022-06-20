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

metrics_file = "/var/www/html/metrics/mq2"
metrics = """
# HELP node_gas_leaking Gas Leak / Smoke Detected
# TYPE node_gas_leaking gauge
node_gas_leaking {gas_leaking}
# HELP node_gas_detections Gas Leak Detections / Smoke Detections in succession
# TYPE node_gas_detections counter
node_gas_detections {gas_detections}
# HELP node_mq2_adc_voltage MQ-2 Gas Detector ADC Voltage
# TYPE node_mq2_adc_voltage gauge
node_mq2_adc_voltage {adc_voltage}
"""

def write_metrics(gas_leaking, gas_detections, adc_voltage):
        with open(metrics_file, 'w+', encoding = 'utf-8') as f:
                f.write(metrics.format(gas_leaking=gas_leaking,gas_detections=gas_detections,adc_voltage=adc_voltage))

def automagic(path = "/", query = {}):
        try: f = request.urlopen(f'http://192.168.2.38:1122/{path}?password=gast&{urlencode(query, quote_via=quote_plus)}', timeout=.5)
        except: pass

def init():
        GPIO.setwarnings(False)
        # GPIO.cleanup()			#clean up at the end of your script
        GPIO.setmode(GPIO.BCM)		#to specify whilch pin numbering system
        # set up the SPI interface pins
        GPIO.setup(SPIMOSI, GPIO.OUT)
        GPIO.setup(SPIMISO, GPIO.IN)
        GPIO.setup(SPICLK, GPIO.OUT)
        GPIO.setup(SPICS, GPIO.OUT)
        GPIO.setup(mq2_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

#read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)	

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)

        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def main():
        init()
        print("please wait...")
        sleep(1)
        # count = 0
        detections = 0
        firstrun = True
        while True:
                # count += 1
                COlevel=readadc(mq2_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
                leaking = not GPIO.input(mq2_dpin)
                voltage = ((COlevel/1024.)*3.3)
                write_metrics(int(leaking), detections, voltage)
                if leaking:
                        detections += 1
                        buzz(50,50)
                        if detections == 1:
                                automagic("screen/on")
                                title = "Gas Leakage or Smoke Detected!"
                                message = f"{'%.2f'%voltage} V ({detections} detections)"
                                automagic("popup/show", {"title": title, "message": message}) #, "action": "http://automater.pi/metrics"})
                                automagic("notification/create", {"title": title, "message": message, "icon": "app.icon://com.android.cellbroadcastreceiver"})
                                automagic("vibrate", {"pattern": "1000,1000", "repeat": "2"})
                                # print(f"{count} > [{'x' if leaking else 0}] ")
                else: sleep(0.25)
                if detections and not leaking: detections = 0
                if firstrun and leaking: break
                firstrun = False

if __name__ =='__main__':
        try:
                main()
                pass
        except KeyboardInterrupt:
                pass

GPIO.cleanup()
if path.exists(metrics_file): remove(metrics_file)