#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq2_dpin = 26
mq2_apin = 0

detections = 0

def init():
    GPIO.setwarnings(False)
    GPIO.cleanup() 
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(SPIMOSI, GPIO.OUT)
    GPIO.setup(SPIMISO, GPIO.IN)
    GPIO.setup(SPICLK, GPIO.OUT)
    GPIO.setup(SPICS, GPIO.OUT)
    GPIO.setup(mq2_dpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#     pygame.mixer.init()
#     pygame.mixer.music.load('rickroll.mp3')
#     pygame.mixer.music.play(-0x1)
#     pygame.mixer.music.pause()

# read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)
def readadc(
    adcnum,
    clockpin,
    mosipin,
    misopin,
    cspin,
    ):
    if adcnum > 7 or adcnum < 0:
        return -0x1
    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)  # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3  # we only need to send 5 bits here
    for i in range(5):
        if commandout & 0x80:
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
        commandout <<= 0x1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)

    adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 0x1
        if GPIO.input(misopin):
            adcout |= 0x1

    GPIO.output(cspin, True)

    adcout >>= 0x1  # first bit is 'null' so drop it
    return adcout

def main():
    global detections
    init()
    print ('please wait...')
    time.sleep(1)
    while True:
        COlevel = readadc(mq2_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
        smokeVal = COlevel / 1024. * 3.3
        if smokeVal > .9: detections += 1
        # if smokeVal > 0.7:
        #     print("smoke") # pygame.mixer.music.unpause()
        # else:
        #     pass # pygame.mixer.music.pause()
        smoke = detections > 3
        if smoke: detections = 0
        print (f'[{"X" if smoke else "O"}] {"%.2f" % smokeVal} V (smokeVal:{round(smokeVal)}|COlevel:{COlevel})')
        time.sleep(0.5)

if __name__ == '__main__':
    try:
        main()
        pass
    except KeyboardInterrupt:
        pass

GPIO.cleanup()