#!/usr/bin/env python
# encoding: utf-8
# Copyright 2014 Xinyu, He <legendmohe@foxmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import argparse
import threading
import time
import json
import subprocess
import urllib, urllib2

import paho.mqtt.client as mqtt

from util.Res import Res
from util.log import *


class mqtt_server_proxy:
    
    NO_HEAD_FLAG = "*"
    BROKER_APP_KEY = "562b490abe17bc415cfbf5a5"

    def __init__(self, address):
        if not address is None:
            INFO("connect to home: %s " % (address))
            self._home_address = address

            settings = Res.init("init.json")
            self._device_id = settings['id'].encode("utf-8")
            self._server_addr = settings['connection']['mqtt_server'].encode("utf-8")
            self._trigger_cmd = settings['command']['trigger'][0].encode("utf-8")
            self._finish_cmd = settings['command']['finish'][0].encode("utf-8")
            INFO("load device id:%s" % self._device_id)
        else:
            ERROR("address is empty")

    def _send_cmd_to_home(self, cmd):
        if not cmd is None and not cmd == "":
            INFO("send cmd %s to home." % (cmd, ))
            if cmd.startswith(mqtt_server_proxy.NO_HEAD_FLAG):
                cmd = cmd[1:]
            else:
                cmd = "%s%s%s" % (self._trigger_cmd, cmd, self._finish_cmd)

            try:
                data = {"cmd": cmd}
                enc_data = urllib.urlencode(data)
                response = urllib2.urlopen(self._home_address,
                                            enc_data,
                                            timeout=5).read()
            except urllib2.HTTPError, e:
                ERROR(e)
                return False
            except urllib2.URLError, e:
                ERROR(e)
                return False
            except Exception, e:
                ERROR(e)
                return False
            else:
                INFO("home response: " + response)
                return True
        else:
            ERROR("cmd is invaild.")
            return False

    def start(self):
        self._fetch_worker()
        # fetch_t = threading.Thread(
        #             target=self._fetch_worker
        #             )
        # fetch_t.daemon = True
        # fetch_t.start()
        # time.sleep(100)

    def _fetch_worker(self):
        INFO("start fetching cmds.")
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_message = self._on_mqtt_message 
        self._mqtt_client.connect(self._server_addr, 1883, 60)
        self._mqtt_client.loop_forever() 

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))  
        client.subscribe(self._device_id)

    def _on_mqtt_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.payload)) 
        payload = str(msg.payload)
        if payload is not None and len(payload) != 0:
            INFO("sending payload to home:%s" % payload)
            try:
                self._send_cmd_to_home(payload)
            except Exception, ex:
                print "exception in _on_mqtt_message:", ex

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='mqtt_server_proxy.py -a address')
    parser.add_argument('-a',
                        action="store",
                        dest="address",
                        default="http://localhost:8000/home/cmd",
                        )
    args = parser.parse_args()
    address = args.address

    INFO("mqtt server proxy is activate.")
    mqtt_server_proxy(address).start()
