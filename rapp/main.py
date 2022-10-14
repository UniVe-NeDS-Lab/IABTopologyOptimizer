from typing import List
from fastapi import FastAPI
import httpx
import uuid
import asyncio
import json
from models.DesEvent import  DesEvent
import networkx as nx 

app = FastAPI()

ICS_URL = "http://172.17.0.1:8083"
RAPP_URL = "http://rapp/api"

class Context():
    def __init__(self):
        self.graph = nx.Graph()

context = Context()

@app.on_event('startup')
async def startup():
    print("Starting Up!!")

@app.get("/api/status")
async def status():
    return {"status": "healthy"}


async def subscribeICS(client):
    task_id = str(uuid.uuid4())
    body = {
        "info_type_id": "IAB_MEASUREMENTS",
        "job_result_uri": f'{RAPP_URL}/des_event',
        "job_owner": "OR2AN2G IAB Optimizer",
        "job_definition": {}
        }
    print(json.dumps(body))
    response = await client.put(f'{ICS_URL}/data-consumer/v1/info-jobs/f{task_id}', json=body)
    return response


@app.get("/api/subscribe")
async def subscribe():
    print("Test")
    async with httpx.AsyncClient() as client:
        print("test2")
        result = await asyncio.gather(subscribeICS(client))
        return {"status": True}

@app.post("/api/des_event")
async def des_event(events_str: List[str]):
    events = [DesEvent.parse_raw(e) for e in events_str]
    for e in events:
        process_des(e)

@app.get("/api/graph")
async def get_graph():
    graph_json = nx.node_link_data(context.graph)
    return graph_json


def process_des(event: DesEvent):
    if event.event.measField.rssi > -80:
        context.graph.add_edge(event.event.commonEventHeader.sourceName.split('_')[0], event.event.measField.cell.split('_')[0], rssi = event.event.measField.rssi, type='wirless', distance=-1000/event.event.measField.rssi)
    # context.graph.add_edge(event.event.commonEventHeader.sourceName,event.event.commonEventHeader.sourceName.replace('mt', 'relay'), type='wired', distance=0)
