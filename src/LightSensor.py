'''
Author: your name
Date: 2020-12-26 23:42:51
LastEditTime: 2020-12-26 23:45:26
LastEditors: your name
Description: In User Settings Edit
FilePath: /BLE/src/LightSensor.py
'''

from machine import ADC
from machine import Pin

class LightSensor():

    def __init__(self, pin):
        self.light = ADC(Pin(pin))

    def value(self):
        value = self.light.read()
        print("Light ADC value:",value)
        return int(value/4095*6000)