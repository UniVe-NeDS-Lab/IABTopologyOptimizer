from __future__ import annotations
from typing import List
from pydantic import BaseModel


class CommonEventHeader(BaseModel):
    sourceId: str
    startEpochMicrosec: str
    eventId: str
    timeZoneOffset: str
    reportingEntityId: str
    eventType: str
    priority: str
    version: str
    nfVendorName: str
    reportingEntityName: str
    sequence: int
    domain: str
    lastEpochMicrosec: str
    eventName: str
    vesEventListenerVersion: str
    sourceName: str
    nfNamingCode: str


class MeasField(BaseModel):
    rssi: float
    rsrq: int
    snr: int
    cell: str


class Event(BaseModel):
    commonEventHeader: CommonEventHeader
    measField: MeasField


class DesEvent(BaseModel):
    event: Event


