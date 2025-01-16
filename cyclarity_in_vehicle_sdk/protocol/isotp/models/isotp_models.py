from pydantic import Field, BaseModel
from typing import Optional

class ISOTP_PAIR(BaseModel):
    rxid: int
    txid: int
    support_uds: bool
    def __str__(self):
        return f"[rxid: {hex(self.rxid)}, txid: {hex(self.txid)}]" + (" UDS supported" if self.support_uds else str())
