#! /usr/bin/python3
# -*- coding: utf-8 -*-
'''
hydroponic controller
monitors water level, air temp, light, humidity and controls water pump
'''

import sys
import os
import time
import datetime
import socket
import paho.mqtt.client as mqtt
import traceback
from threading import Timer
from smbus2 import SMBus
from lib_oled96 import ssd1306
import image
from PIL import ImageFont

#our own modules
from hydro_logger import my_logger
from hydro_globals import SERIAL, MQTTSERVER
import hydro_globals
from bme280 import readBME280All
from bh1750 import readLight
from hydro_gpio import GpioInterface

mqtt_disconnect_timestamp = None

def internet(host="8.8.8.8", port=53, timeout=3):
   """
   Host: 8.8.8.8 (google-public-dns-a.google.com)
   OpenPort: 53/tcp
   Service: domain (DNS/TCP)
   https://stackoverflow.com/questions/3764291/checking-network-connection
   """
   try:
     socket.setdefaulttimeout(timeout)
     socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
     return True
   except Exception as ex:
     my_logger.critical(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ' Network Error ' + ex)
     return False


def on_mqtt_connect(client, userdata, flags, rc):
    global mqtt_disconnect_timestamp
    #print("Connected with result code "+str(rc))
    my_logger.debug(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + " MQTT Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("iot/Hydroponic/wateronminutes")
    client.subscribe("iot/Hydroponic/wateroffminutes")
    mqtt_disconnect_timestamp = None


def on_mqtt_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    my_logger.debug(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + " " + msg.topic+" "+str(msg.payload))
    if msg.topic == "iot/Hydroponic/wateronminutes":
        userdata["on"] = int(msg.payload)
        if userdata["on"] < 2:
             userdata["on"] = 2
    if msg.topic == "iot/Hydroponic/wateroffminutes":
        userdata["off"] = int(msg.payload)
        if userdata["off"] < 30:
             userdata["off"] = 30


def on_mqtt_disconnect(client, userdata, rc):
    global mqtt_disconnect_timestamp
    if rc != 0:
        my_logger.debug(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + " MQTT unexpected disconnect with resultcode " + str(rc))
        mqtt_disconnect_timestamp = datetime.datetime.now()


watertimer = Timer(0,None)
waterison = False
watertime = {"on":2, "off":1}
nextwateron = None
nextwateroff = None
def operatewatertimer(waterswitchfunc):
    global watertimer
    global waterison
    global watertime #in minutes
    global nextwateron
    global nextwateroff

    if watertimer.is_alive():
        return

    waterison = not waterison

    watertimer = Timer(watertime["on"] * 60 if waterison else watertime["off"] * 60, waterswitchfunc, [not waterison])
    watertimer.start()
    nextwateron = datetime.datetime.now()+datetime.timedelta(minutes=watertime["off"]) if not waterison else None
    nextwateroff = datetime.datetime.now()+datetime.timedelta(minutes=watertime["on"]) if waterison else None


def displayInit(oled):
    oled.cls()
    oled.display()
    font = ImageFont.truetype('FreeSans.ttf', 20)
    draw = oled.canvas
    draw.text((12, 10), "Hydroponic", font=font, fill=1)
    draw.text((20, 35), "Controller", font=font, fill=1)
    oled.display()


def showValues(oled, temp, humidity, info):
    oled.cls()
    oled.display()
    draw = oled.canvas
    font = ImageFont.truetype('FreeSans.ttf', 18)
    draw.text((5, 1), "Temp: {:.1f}°C".format(temp), font=font, fill=1)
    draw.text((5, 25), "Hum:  {:.0f} %".format(humidity), font=font, fill=1)
    font = ImageFont.truetype('FreeSerif.ttf', 12)
    draw.text((5, 50), info, font=font, fill=1)
    oled.display()


def main():
    global mqtt_disconnect_timestamp
    global nextwateron
    global nextwateroff
    global waterison
    ''' main
    '''
    my_logger.debug('Start Debug Log hydroponic controller')

    #wait for network. run on after some retries, so that temp control is working anyhow
    for _ in range(20):
        if internet() is True:
            break
        else:
            time.sleep(30)

    mqttclient = mqtt.Client(SERIAL, transport="tcp")
    mqttclient.on_connect = on_mqtt_connect
    mqttclient.on_message = on_mqtt_message
    mqttclient.on_disconnect = on_mqtt_disconnect
    mqttclient.enable_logger()
    mqttclient.will_set("iot/Hydroponic/Disconnect", "lost connection", retain=True)
    mqttclient.reconnect_delay_set(min_delay=1, max_delay=120)

    gpio = GpioInterface()
    i2cbus = SMBus(1)
    oled = ssd1306(i2cbus)
    displayInit(oled)

    try:
        mqttclient.user_data_set(watertime)
        mqttclient.loop_start()
        mqttclient.connect(MQTTSERVER, 1883)

        #initially, switch water on
        gpio.setwaterpump(True)

        loopcnt = 0
        minute2action = False
        while(hydro_globals.keep_running):
            minute = int(time.strftime('%M'))
            time.sleep(1)

            #every second
            if gpio.isshutdownpressed():
                msg = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ': Shutdown button pressed'
                my_logger.info(msg)
                mqttclient.publish("iot/Hydroponic/Shutdown", msg, retain=True).wait_for_publish()
                mqttclient.disconnect()
                os.system("shutdown now -h")
                exit(0)

            gpio.setheartbeatled( not gpio.getheartbeatled())
            loopcnt += 1

            #every 10 secs
            if loopcnt % 10 == 0:
                operatewatertimer(gpio.setwaterpump)

                temp, press, hum = readBME280All()
                mqttclient.publish("iot/Hydroponic/AirTemp", temp, retain=True)
                mqttclient.publish("iot/Hydroponic/AirPress", press, retain=True)
                mqttclient.publish("iot/Hydroponic/AirRelHum", hum, retain=True)

                lux = readLight()
                mqttclient.publish("iot/Hydroponic/Lux", lux, retain=True)

                mqttclient.publish("iot/Hydroponic/WaterPump", "1" if gpio.getwaterpump() else "0")

                if waterison:
                    info = "Wasser AUS in " + str((((nextwateroff-datetime.datetime.now()).seconds)//60)%60) + " min"
                else:
                    info = "Wasser AN in " + str((((nextwateron-datetime.datetime.now()).seconds)//60)%60) + " min"

                showValues(oled, temp, hum, info)

            if minute%2 == 0 and not minute2action:
                #every other minute
                minute2action = True

                if mqtt_disconnect_timestamp is not None:
                    span = datetime.datetime.now() - mqtt_disconnect_timestamp
                    if span.seconds > 600:
                        mqttclient.reconnect()

            #reset done-flags after a minute is over
            if minute != int(time.strftime('%M')):
                minute2action = False

        mqttclient.publish("iot/Hydroponic/Shutdown", msg, retain=True).wait_for_publish()
        mqttclient.disconnect()
        mqttclient.loop_stop()

    except KeyboardInterrupt:
        return
    except:
        my_logger.error(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ' Hydroponic Controller: Unexpected error: ' + traceback.format_exc())
        raise
        #return
    finally:
        hydro_globals.keep_running = False
        my_logger.info(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + ' Hydroponic Controller: main loop ended')


if __name__ == '__main__':
    main()

