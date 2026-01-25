"""
Embedded Python Blocks:
"""

import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    """
    BitLimiter (fixed byte count):
    - Wait for tag with name tag_key
    - When seen, forward exactly packet_bytes bytes
    """

    def __init__(self, tag_key="packet_start", packet_bytes=32):
        gr.sync_block.__init__(
            self,
            name="BitLimiterBytes",
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )

        self.tag_key = pmt.intern(tag_key)
        self.packet_bytes = int(packet_bytes)

        # State
        self.active = False
        self.bytes_remaining = 0

    def work(self, input_items, output_items):

        inp = input_items[0]
        out = output_items[0]

        n_in = len(inp)
        out_index = 0

        # ---- Detect tag ----
        tags = self.get_tags_in_window(0, 0, n_in)

        for t in tags:
            if t.key == self.tag_key:
                # Start forwarding packet_bytes bytes
                self.bytes_remaining = self.packet_bytes
                self.active = True

        # ---- Forward data ----
        for i in range(n_in):

            if self.active and self.bytes_remaining > 0:
                out[out_index] = inp[i]
                out_index += 1
                self.bytes_remaining -= 1

                if self.bytes_remaining == 0:
                    self.active = False

        return out_index

