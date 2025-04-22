from typing import Optional
from pydantic import BaseModel, Field

class DOIP_VEHICLE_IDENTIFICATION(BaseModel):
    """Model containing information regarding DoIP vehicle announcement/identification message
    """
    vin: str = Field(description="the vehicle's VIN")
    target_address: int = Field(description="This is the logical address that is assigned to the responding DoIP entity")
    eid: str = Field("This is a unique identification of the DoIP entity")
    gid: str = Field(description="This is a unique identification of a group of DoIP entity")
    further_action_required: int = Field(description="Further action required")
    vin_gid_sync_status: Optional[int] = Field(description="VIN/GID sync. status")

    def __str__(self):
        vin_gid_sync_status_str = f", vin gid sync status: {self.vin_gid_sync_status}" if self.vin_gid_sync_status else ""
        return (f"Vehicle identification:\nvin: {self.vin}, eid: {self.eid},"
                f" gid: {self.gid}, target logical address: {hex(self.target_address)},"
                f" further action required: {self.further_action_required}{vin_gid_sync_status_str}\n")


class DOIP_ROUTING_ACTIVATION(BaseModel):
    """Model containing information regarding a DoIP routing activation response
    """
    source_logical_address: int = Field(description="Logical address of client DoIP entity")
    response_code: int = Field(description="Routing activation response code")
    src_addr_range_desc: str = Field(description="Description of the source address")

    def __str__(self):
        return (f"Routing activation for source logical address: {hex(self.source_logical_address)}\n"
                f"response code: {hex(self.response_code)}" +
                f"\ndescription of used source address range: {self.src_addr_range_desc}\n")


class DOIP_ENTITY_STATUS(BaseModel):
    """Model containing information regarding a DoIP entity status response
    """
    node_type: int = Field(description="Node type - DoIP node or a DoIP gateway")
    max_concurrent_sockets: int = Field(description="Max. concurrent sockets")
    currently_open_sockets: int = Field(description="Currently open sockets")
    max_data_size: int = Field(description="Max. data size")

    def __str__(self):
        return (f"Entity status:\n"
                f"node type: {hex(self.node_type)}, "
                f"max concurrent sockets: {self.max_concurrent_sockets}, "
                f"currently open sockets: {self.currently_open_sockets}, "
                f"max data size: {hex(self.max_data_size)}\n")


class DOIP_TARGET(BaseModel):
    """Model containing information regarding a DoIP entity
    """
    target_ip: str = Field(description="IP address of the server DoIP entity")
    source_ip: str = Field(description="IP address of the client DoIP entity")
    source_port: int = Field(description="source port")
    destination_port: int = Field(description="target port")
    routing_vehicle_id_response: DOIP_VEHICLE_IDENTIFICATION = Field(
        description="DoIP vehicle announcement/identification message")
    entity_status_response: Optional[DOIP_ENTITY_STATUS] = Field(
        default=None,
        description="DoIP entity status response")
    routing_activation_response: Optional[DOIP_ROUTING_ACTIVATION] = Field(
        default=None,
        description="DoIP routing activation response")

    def __str__(self):
        return (f"DoIP target identified:\n"
                f"source: {self.source_ip}:{self.source_port}, "
                f"target: {self.target_ip}:{self.destination_port}, \n"
                f"{str(self.routing_vehicle_id_response)}"
                f"{str(self.routing_activation_response) if self.routing_activation_response else ''}"
                f"{str(self.entity_status_response) if self.entity_status_response else ''}"
                )
