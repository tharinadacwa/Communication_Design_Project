"""
Embedded Python Block: Idle + Packet Injector
"""

import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    """
    Continuous stream block with idle bytes 0xAA.
    Injects packets from input stream (Tagged Stream Mux) whenever available.
    """
    def __init__(self, idle_byte=0xAA):
        gr.sync_block.__init__(
            self,
            name="IdlePacketInjector",
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )

        self.idle_byte = idle_byte
        self.packet_buffer = []

    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        n_out = len(out)
        in_len = len(inp)
        out_index = 0

        # ---- Append input bytes to internal buffer ----
        if in_len > 0:
            self.packet_buffer.extend(inp.tolist())

        # ---- Fill output ----
        while out_index < n_out:

            if len(self.packet_buffer) > 0:
                # Pop from buffer
                out[out_index] = self.packet_buffer.pop(0)
            else:
                # Output idle
                out[out_index] = self.idle_byte

            out_index += 1

        return n_out
