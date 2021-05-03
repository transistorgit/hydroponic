#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mai  1 11:35:42 2021

@author: bernd
"""

import time
import RPi.GPIO as GPIO

#our own modules
from hydro_logger import my_logger
import hydro_globals

__all__ = ['GpioInterface']

class GpioInterface():
    """interfaces digital i/o and spi"""
    HEARTBEATLED = 12 #binary output for led blinking
    SHUTDOWNBUTTON = 36 #binary input for user shutdown request
    WATERPUMPOUTPUT = 15
    WATERTANKLEVELINPUT = 16
    WATERLEVELRETURNINPUT = 18
    STATUS1LED = 28
    STATUS2LED = 27
    BUTTONUP = 7
    BUTTONDOWN = 29
    BUTTONOK = 26
    BUTTONCANCEL = 24



    def __init__(self):
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(GpioInterface.HEARTBEATLED, GPIO.OUT)
            GPIO.setup(GpioInterface.SHUTDOWNBUTTON, GPIO.IN)
            GPIO.setup(GpioInterface.WATERPUMPOUTPUT, GPIO.OUT)
            GPIO.setup(GpioInterface.WATERTANKLEVELINPUT, GPIO.IN)
            GPIO.setup(GpioInterface.WATERLEVELRETURNINPUT, GPIO.IN)
            #GPIO.setup(GpioInterface.STATUS1LED, GPIO.OUT)
            #GPIO.setup(GpioInterface.STATUS2LED, GPIO.OUT)
            GPIO.setup(GpioInterface.BUTTONUP, GPIO.IN)
            GPIO.setup(GpioInterface.BUTTONDOWN, GPIO.IN)
            GPIO.setup(GpioInterface.BUTTONOK, GPIO.IN)
            GPIO.setup(GpioInterface.BUTTONCANCEL, GPIO.IN)

            GPIO.output(GpioInterface.WATERPUMPOUTPUT, GPIO.LOW)
            #GPIO.output(GpioInterface.STATUS1LED, GPIO.LOW)
            #GPIO.output(GpioInterface.STATUS2LED, GPIO.LOW)

        except Exception as e:
            my_logger.critical("gpio init error " + str(e))
            exit(1)


    def isshutdownpressed(self):
        '''poll shutdown pin'''
        try:
            if GPIO.input(GpioInterface.SHUTDOWNBUTTON):
                return False
            else:
                return True
        except Exception:
            return False


    def setheartbeatled(self, state):
        '''set heartbeat led pin'''
        try:
            GPIO.output(GpioInterface.HEARTBEATLED, GPIO.HIGH if state else GPIO.LOW)
        except Exception:
            pass


    def getheartbeatled(self):
        '''get heartbeat led pin, usefull for pin toggling'''
        try:
            return GPIO.input(GpioInterface.HEARTBEATLED)
        except Exception:
            pass


    def setstatus1led(self, state):
        raise Exception("reserved pin")
        try:
            GPIO.output(GpioInterface.STATUS1LED, GPIO.HIGH if state else GPIO.LOW)
        except Exception:
            pass


    def setstatus2led(self, state):
        raise Exception("reserved pin")
        try:
            GPIO.output(GpioInterface.STATUS2LED, GPIO.HIGH if state else GPIO.LOW)
        except Exception:
            pass


    def setwaterpump(self, state):
        '''set water pump relais pin'''
        try:
            if state:
                my_logger.debug(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ' Water on')
                GPIO.output(GpioInterface.WATERPUMPOUTPUT, GPIO.HIGH)
            else:
                my_logger.debug(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ' Water off')
                GPIO.output(GpioInterface.WATERPUMPOUTPUT, GPIO.LOW)
        except Exception:
            my_logger.error(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ' Water switching error')


    def getwaterpump(self):
        try:
            return GPIO.input(GpioInterface.WATERPUMPOUTPUT)
        except Exception:
            return false


    def isshutdownpressed(self):
        '''poll shutdown pin'''
        try:
            if GPIO.input(GpioInterface.SHUTDOWNBUTTON):
                return False
            else:
                return True
        except Exception:
            return False


def main():
    gpio = GpioInterface()


    gpio.setwaterpump(False)
    time.sleep(1)
    gpio.setheartbeatled(False)
    time.sleep(1)
    gpio.setwaterpump(True)
    time.sleep(1)
    gpio.setheartbeatled(True)

if __name__=="__main__":
   main()


















