from typing import Optional
from pydantic import BaseModel, Field

class DOIP_VEHICLE_IDENTIFICATION(BaseModel):
    vin: str
    target_address: int
    eid: str
    gid: str
    further_action_required: int
    vin_gid_sync_status: Optional[int]
    def __repr__(self):
        vin_gid_sync_status_str = f", vin gid sync status: {self.vin_gid_sync_status}" if self.vin_gid_sync_status else ""
        return f"vin: {self.vin}, eid: {self.eid}, gid: {self.gid}, logical address: {hex(self.target_address)}, further action required: {self.further_action_required}{vin_gid_sync_status_str}"


class DOIP_ROUTING_ACTIVATION(BaseModel):
    response_code: int
    src_addr_range_desc: Optional[str] = None
    def __repr__(self):
        return f"response code: {hex(self.response_code)}" + f"\ndescription of used source address range: {self.src_addr_range_desc}" if self.src_addr_range_desc else ""


class DOIP_ENTITY_STATUS(BaseModel):
    node_type: int
    max_concurrent_sockets: int
    currently_open_sockets: int
    max_data_size: int
    def __repr__(self):
        return f"node type: {hex(self.node_type)}, max concurrent sockets: {self.max_concurrent_sockets}, currently open sockets: {self.currently_open_sockets}, max data size: {hex(self.max_data_size)}"

class DOIP_DATA(BaseModel):
    routing_vehicle_id_response: Optional[DOIP_VEHICLE_IDENTIFICATION] = None
    routing_activation_responses: Optional[dict[int, DOIP_ROUTING_ACTIVATION]] = (
        None  # src_addr: routing_activation_data
    )
    entity_status_response: Optional[DOIP_ENTITY_STATUS] = None
    def __repr__(self):
        vehicle_id_str = f"Vehicle identification:\n{repr(self.routing_vehicle_id_response)}\n" if self.routing_vehicle_id_response else ""
        entity_status_str = f"Entity status:\n{repr(self.entity_status_response)}\n" if self.entity_status_response else ""
        routing_activation_str = ""
        if self.routing_activation_responses:
            for logical_address, routing_activation in self.routing_activation_responses.items():
                routing_activation_str += f"Routing activation for logical address: {hex(logical_address)}: {repr(routing_activation)}\n"
        return vehicle_id_str + entity_status_str + routing_activation_str

class DOIP_TARGET(BaseModel):
    target_ip: str
    source_ip: str
    source_port: int
    destination_port: int
    target_address: int
    doip_data: DOIP_DATA = Field(default_factory=DOIP_DATA)  # {ip: data}

    def __repr__(self):
        base_target_str = f"DoIP target identified:\nsource: {self.source_ip}:{self.source_port}, target: {self.target_ip}:{self.destination_port}, logical address: {hex(self.target_address)}\n"

        return f"{base_target_str}\n{repr(self.doip_data)}"
