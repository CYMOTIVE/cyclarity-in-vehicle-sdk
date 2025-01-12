from typing import Optional
from pydantic import BaseModel, Field

class DOIP_VEHICLE_IDENTIFICATION(BaseModel):
    vin: str
    target_address: int
    eid: str
    gid: str
    further_action_required: int
    vin_gid_sync_status: Optional[int]

    def __str__(self):
        vin_gid_sync_status_str = f", vin gid sync status: {self.vin_gid_sync_status}" if self.vin_gid_sync_status else ""
        return (f"Vehicle identification:\nvin: {self.vin}, eid: {self.eid},"
                f" gid: {self.gid}, target logical address: {hex(self.target_address)},"
                f" further action required: {self.further_action_required}{vin_gid_sync_status_str}\n")


class DOIP_ROUTING_ACTIVATION(BaseModel):
    source_logical_address: int
    response_code: int
    src_addr_range_desc: str

    def __str__(self):
        return (f"Routing activation for source logical address: {hex(self.source_logical_address)}\n"
                f"response code: {hex(self.response_code)}" +
                f"\ndescription of used source address range: {self.src_addr_range_desc}\n")


class DOIP_ENTITY_STATUS(BaseModel):
    node_type: int
    max_concurrent_sockets: int
    currently_open_sockets: int
    max_data_size: int

    def __str__(self):
        return (f"Entity status:\n"
                f"node type: {hex(self.node_type)}, "
                f"max concurrent sockets: {self.max_concurrent_sockets}, "
                f"currently open sockets: {self.currently_open_sockets}, "
                f"max data size: {hex(self.max_data_size)}\n")


class DOIP_TARGET(BaseModel):
    target_ip: str
    source_ip: str
    source_port: int
    destination_port: int
    routing_vehicle_id_response: DOIP_VEHICLE_IDENTIFICATION
    entity_status_response: Optional[DOIP_ENTITY_STATUS] = None
    routing_activation_response: Optional[DOIP_ROUTING_ACTIVATION] = None

    def __str__(self):
        return (f"DoIP target identified:\n"
                f"source: {self.source_ip}:{self.source_port}, "
                f"target: {self.target_ip}:{self.destination_port}, \n"
                f"{str(self.routing_vehicle_id_response)}"
                f"{str(self.routing_activation_response) if self.routing_activation_response else ''}"
                f"{str(self.entity_status_response) if self.entity_status_response else ''}"
                )
