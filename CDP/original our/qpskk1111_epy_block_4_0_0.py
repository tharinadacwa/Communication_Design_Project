#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pmt
import zlib
import time
import os
from gnuradio import gr

class crc_forwarder(gr.basic_block):
    """
    CRC32 Checker + Dedup + Forwarder (Message Reassembler)
    - Input : [sender_addr | seq_id | payload | crc32]
    - Output: [sender_addr | full_message] (only when END marker)
    - END marker = valid packet with empty payload
    - Batch ACK: Sends 'sync_len' random bytes followed by a batch of ACKs.
    """

    def __init__(self, retry_limit=1, ack_batch_size=5, sync_len=1000):
        gr.basic_block.__init__(
            self,
            name="CRC32 Dedup + Forwarder",
            in_sig=[],
            out_sig=[]
        )

        self.retry_limit = max(1, int(retry_limit))
        self.ack_batch_size = max(1, int(ack_batch_size))
        self.sync_len = int(sync_len)  # Number of sync bytes
        
        self.received_ids = set()
        self.buffers = {}
        self.ack_queue = [] 

        # Ports
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))
        self.message_port_register_out(pmt.intern("ack_out"))

        self.set_msg_handler(pmt.intern("in"), self._handle_msg)

        print(f"[CRC32] Receiver init (retries={self.retry_limit}, batch={self.ack_batch_size}, sync_len={self.sync_len})")

    def _flush_ack_queue(self):
        """Sends sync bytes (if any), then flushes all queued ACKs."""
        if not self.ack_queue:
            return

        print(f"[ACK] Batch threshold reached. Flushing {len(self.ack_queue)} ACKs...")

        # 1. Send Synchronization/Wake-up Bytes (if configured)
        if self.sync_len > 0:
            noise_data = os.urandom(self.sync_len)
            noise_vec = pmt.init_u8vector(len(noise_data), list(noise_data))
            noise_pdu = pmt.cons(pmt.PMT_NIL, noise_vec)
            
            self.message_port_pub(pmt.intern("ack_out"), noise_pdu)
            
            # Small delay to ensure sync bytes clear before ACKs follow
            time.sleep(0.01) 

        # 2. Send all queued ACKs
        for ack_pdu in self.ack_queue:
            # Respect the retry limit for every ACK in the queue
            for i in range(self.retry_limit):
                self.message_port_pub(pmt.intern("ack_out"), ack_pdu)
                # minimal sleep to prevent internal PDU congestion
                time.sleep(0.005) 
        
        # Clear the queue
        self.ack_queue = []
        print("[ACK] Batch flush complete.")

    def _handle_msg(self, msg):
        if not pmt.is_pair(msg):
            return
        vec = pmt.cdr(msg)
        if not pmt.is_u8vector(vec):
            return

        data = bytearray(pmt.u8vector_elements(vec))
        if len(data) < 6:
            print("[CRC32] Frame too short")
            return

        sender_addr = data[0]
        pkt_id = data[1]
        payload = data[2:-4]
        recv_crc = int.from_bytes(data[-4:], "big")

        calc_crc = zlib.crc32(bytes([sender_addr, pkt_id]) + payload) & 0xFFFFFFFF

        if calc_crc != recv_crc:
            print(f"[CRC32] FAIL (Addr=0x{sender_addr:02X}, ID={pkt_id})")
            return

        print(f"[CRC32] OK (Addr=0x{sender_addr:02X}, ID={pkt_id})")

        # --- Build ACK & Queue It ---
        ack_data = bytearray([sender_addr, 0xAA, pkt_id])
        ack_crc = zlib.crc32(ack_data) & 0xFFFFFFFF
        ack_data += ack_crc.to_bytes(4, 'big')

        ack_vec = pmt.init_u8vector(len(ack_data), list(ack_data))
        ack_pdu = pmt.cons(pmt.PMT_NIL, ack_vec)

        self.ack_queue.append(ack_pdu)
        print(f"[ACK] Queued ({len(self.ack_queue)}/{self.ack_batch_size})")

        # Check threshold
        if len(self.ack_queue) >= self.ack_batch_size:
            self._flush_ack_queue()

        # Dedup
        if (sender_addr, pkt_id) in self.received_ids:
            print(f"[Forward] Duplicate packet ID={pkt_id}, ignored")
            return
        self.received_ids.add((sender_addr, pkt_id))

        # END MARKER
        if len(payload) == 0:
            if sender_addr in self.buffers and self.buffers[sender_addr]:
                full_payload = b''.join(self.buffers[sender_addr])
                forward_bytes = bytes([sender_addr]) + full_payload

                out_vec = pmt.init_u8vector(len(forward_bytes), list(forward_bytes))
                out_msg = pmt.cons(pmt.PMT_NIL, out_vec)
                self.message_port_pub(pmt.intern("out"), out_msg)

                print(f"[Forward] Reassembled {len(full_payload)} bytes")

            else:
                print(f"[Forward] END marker received but no data")

            self.buffers[sender_addr] = []
            return

        # Buffering
        if sender_addr not in self.buffers:
            self.buffers[sender_addr] = []

        self.buffers[sender_addr].append(payload)
        total_len = sum(len(p) for p in self.buffers[sender_addr])
        print(f"[Buffer] Addr 0x{sender_addr:02X}, ID {pkt_id}, +{len(payload)} bytes (total {total_len})")
