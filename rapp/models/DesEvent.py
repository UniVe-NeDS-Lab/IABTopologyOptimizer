from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class CommonEventHeader(BaseModel):
    eventId: str
    sourceName: str
    ts: str
    domain: str
    topo_id: str
    role: str


class MeasField(BaseModel):
    rnti: int
    imsi: Optional[str]
    mcs: Optional[int]
    rx_power_avg: Optional[int]
    rx_power_tot: Optional[int]
    n0_power_avg: Optional[int]
    rx_rssi_dBm: Optional[int]
    ssb_rsrp_dBm: Optional[int]
    avg_rsrp: Optional[int]
    srs_wide_band_snr: Optional[float]
    dlsch_mcs: Optional[int]
    ulsch_mcs: Optional[int]
    cqi: Optional[int]
    dlsch_bler: Optional[float]
    ulsch_bler: Optional[float]
    failure: Optional[int]

class Event(BaseModel):
    commonEventHeader: CommonEventHeader
    measField: MeasField


class DesEvent(BaseModel):
    event: Event


