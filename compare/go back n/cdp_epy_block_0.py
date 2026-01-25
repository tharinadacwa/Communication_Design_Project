#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pmt
from gnuradio import gr

class address_add(gr.basic_block):
    """
    Block to prepend a dynamic address byte to a PDU payload.
    
    This block has no GRC parameters. It relies entirely on the 'addr_in' 
    port to set the destination address.
    """
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="address_add",
            in_sig=[],
            out_sig=[]
        )
        # Default internal state (will be overwritten by GUI immediately)
        self.address = 0x00
        
        # Port for the Text Payload
        self.message_port_register_in(pmt.intern("in"))
        # Port for the Address Update
        self.message_port_register_in(pmt.intern("addr_in"))
        
        # Output Port
        self.message_port_register_out(pmt.intern("out"))
        
        # Register handlers
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)
        self.set_msg_handler(pmt.intern("addr_in"), self.handle_address_update)

    def handle_address_update(self, msg):
        """
        Receives the address from the GUI (Symbol or Int) 
        and updates the internal state.
        """
        try:
            # GUI sends address as a String Symbol (e.g. "255")
            if pmt.is_symbol(msg):
                str_val = pmt.symbol_to_string(msg)
                self.address = int(str_val)
            
            # If standard int/long is sent
            elif pmt.is_integer(msg) or pmt.is_uint64(msg):
                self.address = pmt.to_long(msg)
                
            # print(f"[address_add] Active Address set to: {self.address}")
                
        except ValueError:
            pass

    def handle_msg(self, msg):
        """
        Prepend the currently active 'self.address' to the message.
        """
        meta = pmt.make_dict()
        payload = bytearray()

        # 1. Parse Input
        if pmt.is_pair(msg):
            meta = pmt.car(msg)
            payload = bytearray(pmt.u8vector_elements(pmt.cdr(msg)))
        elif pmt.is_symbol(msg):
            text_data = pmt.symbol_to_string(msg)
            payload = bytearray(text_data, 'utf-8')
        else:
            return

        # 2. Prepend Address
        safe_addr = self.address & 0xFF
        payload.insert(0, safe_addr)

        # 3. Publish
        out_msg = pmt.cons(meta, pmt.init_u8vector(len(payload), payload))
        self.message_port_pub(pmt.intern("out"), out_msg)
