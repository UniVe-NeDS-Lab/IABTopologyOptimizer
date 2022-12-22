from typing import List
from fastapi import FastAPI, Response, Request, HTTPException
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
        self.iab_graph = nx.Graph()
        self.topology = nx.Graph()

context = Context()

@app.on_event('startup')
async def startup():
    print("Starting Up!!")
    # await asyncio.wait(10)
    # async with httpx.AsyncClient() as client:
    #     result = await asyncio.gather(subscribeICS(client))    
    #     print("Subscribed to ICS")

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
    async with httpx.AsyncClient() as client:
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

@app.get("/api/graphml")
async def get_topology():
    graphml = '\n'.join(nx.generate_graphml(context.graph, prettyprint=True))
    return Response(content=graphml, media_type='application/xml')

@app.delete("/api/graph")
async def get_graph():
    context.graph = nx.Graph()


def process_des(event: DesEvent):
    print(event)
    match event.event.commonEventHeader.eventId:
        case 'IAB.MT.MeasureReport':
            pass
        case default:
            pass