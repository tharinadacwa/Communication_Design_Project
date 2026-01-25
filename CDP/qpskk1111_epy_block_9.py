"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt
import threading
import time

class blk(gr.basic_block):  # Inherit from basic_block for Message passing
    """Text to PDU (Blind Repeater) - Interval in Seconds"""

    def __init__(self, preamble_len=100, repeat_count=5, repeat_interval_seconds=1.0, src_address=1, dest_address=2):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.basic_block.__init__(
            self,
            name='Text to PDU (Blind Repeater)',   # will show up in GRC
            in_sig=None,   # No streaming inputs
            out_sig=None   # No streaming outputs
        )
        
        # --- Parameters ---
        self.preamble_len = int(preamble_len)
        self.repeat_count = int(repeat_count)
        
        # This value is treated as SECONDS (e.g., 1.0 = 1 second, 0.5 = 500ms)
        self.repeat_interval = float(repeat_interval_seconds) 
        
        self.src_address = int(src_address) & 0xFF
        self.dest_address = int(dest_address) & 0xFF

        # --- Message Ports ---
        self.message_port_register_in(pmt.intern("msg_in"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg_input)

        self.message_port_register_out(pmt.intern("pdus"))
        self.message_port_register_out(pmt.intern("status_out"))

        # Threading lock
        self._tx_lock = threading.Lock()

    def handle_msg_input(self, msg):
        """Handler for incoming text messages from GUI"""
        try:
            text_data = pmt.symbol_to_string(msg)
        except:
            print("[BlindTx] Error: Input must be a string symbol")
            return

        if self._tx_lock.locked():
            print("[BlindTx] Busy sending previous message.")
            return

        t = threading.Thread(target=self._process_transmission, args=(text_data,))
        t.daemon = True
        t.start()

    def _process_transmission(self, text_data):
        """Constructs packet and repeats it with user-defined interval in seconds"""
        with self._tx_lock:
            # Update GUI status
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("pending"))
            
            # --- CONSTRUCT THE PACKET ---
            preamble = bytes([0xAA] * self.preamble_len)
            header = bytes([self.src_address, self.dest_address, 0x01])
            payload = text_data.encode('utf-8')
            
            full_data = preamble + header + payload
            
            pdu_vector = pmt.init_u8vector(len(full_data), list(full_data))
            pdu = pmt.cons(pmt.make_dict(), pdu_vector)

            print(f"[BlindTx] Sending {len(full_data)} bytes. Repeats: {self.repeat_count}, Interval: {self.repeat_interval}s")

            # --- SEND LOOP ---
            for i in range(self.repeat_count):
                self.message_port_pub(pmt.intern("pdus"), pdu)
                
                # Sleep in SECONDS
                time.sleep(self.repeat_interval)

            # Update GUI status
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("success"))
            print("[BlindTx] Done.")

    def work(self, input_items, output_items):
        """Not used for Message Blocks"""
        return 0