
#  ============LICENSE_START===============================================
#  Copyright (C) 2021 Nordix Foundation. All rights reserved.
#  ========================================================================
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ============LICENSE_END=================================================
#

import json
import os
import random
from termios import CSIZE
import requests
import time
import networkx as nx

# Randomly, between 0 and 10 seconds sends a "CUS Link Failure" alarm event to the Message Router. The ID of the O-RU is also
# randomly generated between 0 and 9.
# When the modulo of the ID is 1, a "heartbeat" message will also be sent to MR.


MR_PATH = "/events/unauthenticated.IAB_MEASUREMENTS"
FAULT_ID = "28"

cqiMessage = {
    "event": {
        "commonEventHeader": {
            "domain": "measurements",
            "eventId": "nt:network-topology/nt:topology/nt:node/nt:node-id",
            "eventName": "IAB.measurements",
            "eventType": "MeasurementsReport",
            "sequence": 0,
            "priority": "Normal",
            "reportingEntityId": "SDNR",
            "reportingEntityName": "@controllerName@",
            "sourceId": "",
            "sourceName": "O-RU-ID",
            "startEpochMicrosec": "@timestamp@",
            "lastEpochMicrosec": "@timestamp@",
            "nfNamingCode": "",
            "nfVendorName": "ietf-hardware (RFC8348) /hardware/component[not(parent)][1]/mfg-name",
            "timeZoneOffset": "+00:00",
            "version": "4.1",
            "vesEventListenerVersion": "7.2.1"
        },
        "measField": {
            'cell': '',
            'rssi': 0,
            'snr': 0,
            'rsrq': 0
        }
    }
}

heartBeatMessage = {
    "event": {
        "commonEventHeader": {
            "version": 3.0,
            "domain": "heartbeat",
            "eventName": "Heartbeat\_vIsbcMmc",
            "eventId": "ab305d54-85b4-a31b-7db2fb6b9e546015",
            "sequence": 0,
            "priority": "Normal",
            "reportingEntityId": "cc305d54-75b4-431badb2eb6b9e541234",
            "reportingEntityName": "EricssonOamVf",
            "sourceId": "de305d54-75b4-431b-adb2-eb6b9e546014",
            "sourceName": "ibcx0001vm002ssc001",
            "nfNamingCode": "ibcx",
            "nfcNamingCode": "ssc",
            "startEpochMicrosec": 1413378172000000,
            "lastEpochMicrosec": 1413378172000000
        }
    }
}


class CQISimulator():
    def __init__(self, mr_url):
        self.mr_url = mr_url
        self.graph = nx.read_graphml('test_data/firenze_45_28.graphml')

    def report_cqi(self, src, tgt, e):
        # o_ru_id = "ERICSSON-O-RU-1122" + str(random_time)
        print(f"Sending CQI: {src} receives {tgt} with {e['pathloss']}dB")
        msg_as_json = json.loads(json.dumps(cqiMessage))
        msg_as_json["event"]["commonEventHeader"]["sourceName"] = src
        msg_as_json["event"]["measField"]["cell"] = tgt
        msg_as_json["event"]["measField"]["rssi"] = e['pathloss']
        sendPostRequest(self.mr_url, msg_as_json)

    def start(self):
        while True:
            for src, d in self.graph.nodes.items():
                if d['type'] == 'relay' and d['iab_type'] == 'mt':
                    # For each IAB-mt
                    for tgt in nx.neighbors(self.graph, src):
                        if self.graph.nodes[tgt]['iab_type'] == 'gnb':
                            # For each of its gnb neighors
                            e = self.graph[tgt][src]
                            if e['delay'] > 0:
                                self.report_cqi(src, tgt, e)

            random_time = int(10 * random.random())
            # if (random_time % 3 == 1):
            #     print("Sent heart beat")
            #     sendPostRequest(self.mr_url, heartBeatMessage)

            # o_ru_id = "ERICSSON-O-RU-1122" + str(random_time)
            # print("Sent link failure for O-RAN-RU: " + o_ru_id)
            # msg_as_json = json.loads(json.dumps(linkFailureMessage))
            # msg_as_json["event"]["commonEventHeader"]["sourceName"] = o_ru_id
            # sendPostRequest(self.mr_url, msg_as_json)

            time.sleep(random_time)


def sendPostRequest(url, msg):
    try:
        print(url)
        requests.post(url, json=msg)
    except Exception as e:
        print(type(e))
        print(e.args)
        print(e)


if __name__ == "__main__":
    mr_host = os.getenv("MR-HOST", "http://localhost")
    print("Using MR Host from os: " + mr_host)
    mr_port = os.getenv("MR-PORT", "3904")
    print("Using MR Port from os: " + mr_port)
    mr_url = mr_host + ":" + mr_port + MR_PATH
    CSim = CQISimulator(mr_url)
    CSim.start()
