from typing import List
from fastapi import FastAPI, Response, Request, HTTPException
import httpx
import uuid
import asyncio
import json
from models.DesEvent import  DesEvent
from models.Requests import InitMessage
import networkx as nx 
from iab_manager.lib import Iab

app = FastAPI()

ICS_URL = "http://172.17.0.1:8083"
RAPP_URL = "http://rapp/api"

class Context():
    def __init__(self):
        self.graph = nx.Graph()
        self.iab_graph = nx.Graph()
        self.topology = nx.Graph()
        self.iab_manager = None

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


@app.post("/api/init")
async def init(message: InitMessage):
    try:
        context.iab_manager = Iab(message.reservation_id, message.srn_blacklist)
    except Exception as e:
        return {"status": False, "msg": str(e)}
    await subscribe()
    return {"status": True}

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

@app.post("/api/graphml")
async def set_topology(request: Request):
    content_type = request.headers['Content-Type']
    if content_type == 'application/xml' and context.iab_manager != None:
        body = await request.body()
        context.iab_manager.get_iab_network(body)
        return {"status": True}
    else:
        raise HTTPException(status_code=400, detail=f'Content type {content_type} not supported')


@app.delete("/api/graph")
async def get_graph():
    context.graph = nx.Graph()


@app.post("/api/optimize")
async def optimize_topo():
    pass


def process_des(event: DesEvent):
    match event.event.commonEventHeader.eventId:
        case 'IAB.MT.MeasureReport':
            #Ignore MT / Relay separation
            print(event.event.commonEventHeader.eventId, event.event.commonEventHeader.topo_id, event.event.measField.rnti)
            if event.event.measField.rnti>0:
                context.graph.add_node(event.event.commonEventHeader.topo_id, rnti=event.event.measField.rnti, role='mt')
            #Enforce MT/ Relay separation
            # context.iab_graph.add_edge(event.event.commonEventHeader.sourceName, event.event.measField.cell, rssi = event.event.measField.rssi, type='wirless', distance=-1000/event.event.measField.rssi)
            # context.iab_graph.add_edge(event.event.commonEventHeader.sourceName,event.event.commonEventHeader.sourceName.replace('mt', 'relay'), type='wired', distance=0)
                #print(event)
        case  'IAB.DU.MeasureReport':
            print(event.event.commonEventHeader.eventId, event.event.commonEventHeader.topo_id, event.event.measField.rnti)
            node = [x for x,y in context.graph.nodes(data=True) if y.get('rnti', -1) == event.event.measField.rnti]
            if event.event.measField.rnti>0 and len(node)==1:
                context.graph.add_node(event.event.commonEventHeader.topo_id, role='du')
                context.graph.add_edge(event.event.commonEventHeader.topo_id, node[0], type='wirless')
                context.graph.add_edge(event.event.commonEventHeader.topo_id, event.event.commonEventHeader.topo_id.replace('du', 'mt'), type='wired', distance=0)
        case 'IAB.DU.ULSCH.FailureReport':
            print(event.event.commonEventHeader.eventId)
            pass
        case 'IAB.DU.RRC.FailureReport':
            print(event.event.commonEventHeader.eventId)
            pass
        case default:
            print("Error")
            pass