'''
Author: your name
Date: 2020-12-28 00:02:08
LastEditTime: 2020-12-28 01:38:25
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /BLE/src/ble_lightsensor.py
'''

#File：ble_lightsensor.py
import bluetooth
import struct
import time
from ble_advertising import advertising_payload

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)

_ADV_SERVICE_DATA_UUID = 0xFE95
_SERVICE_UUID_ENV_SENSE = 0x181A
_CHAR_UUID_AMBIENT_LIGHT = 'FEC66B35-937E-4938-9F8D-6E44BBD533EE'

# Service environmental sensing
_ENV_SENSE_UUID = bluetooth.UUID(_SERVICE_UUID_ENV_SENSE)
# Characteristic ambient light density
_AMBIENT_LIGHT_CHAR = (
    bluetooth.UUID(_CHAR_UUID_AMBIENT_LIGHT),
    _FLAG_READ | _FLAG_NOTIFY ,
)
_ENV_SENSE_SERVICE = (
    _ENV_SENSE_UUID,
    (_AMBIENT_LIGHT_CHAR,),
)

# https://specificationrefs.bluetooth.com/assigned-values/Appearance%20Values.pdf
_ADV_APPEARANCE_GENERIC_AMBIENT_LIGHT = const(1344)

class BLELightSensor:
    def __init__(self, ble, name='Nodemcu'):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle,),) = self._ble.gatts_register_services((_ENV_SENSE_SERVICE,))
        self._connections = set()
        time.sleep_ms(500)
        self._payload = advertising_payload(
            name=name, services=[_ENV_SENSE_UUID], appearance=_ADV_APPEARANCE_GENERIC_AMBIENT_LIGHT
        )
        self._sd_adv = None
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data

    def set_light(self, light_den, notify=False):
        self._ble.gatts_write(self._handle, struct.pack("!h", int(light_den)))
        self._sd_adv = self.build_mi_sdadv(light_den)
        self._advertise()
        if notify:
            for conn_handle in self._connections:
                if notify:
                    # Notify connected centrals.
                    self._ble.gatts_notify(conn_handle, self._handle)

    def build_mi_sdadv(self, density):
        
        uuid = 0xFE95
        fc = 0x0010
        pid = 0x0002
        fcnt = 0x01
        mac = self._ble.config('mac')
        objid = 0x1007
        objlen = 0x03
        objval = density

        service_data = struct.pack("<3HB",uuid,fc,pid,fcnt)+mac+struct.pack("<H2BH",objid,objlen,0,objval)
        print("Service Data:",service_data)
        
        return advertising_payload(service_data=service_data)
        
    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)
        time.sleep_ms(100)

        print("sd_adv",self._sd_adv)
        if self._sd_adv is not None:
            print("sdddd_adv",self._sd_adv)
            self._ble.gap_advertise(interval_us, adv_data=self._sd_adv)