#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import pmt
import time
import os
from gnuradio import gr

class TextToPDU_ARQ(gr.basic_block):
    def __init__(self, pkt_size=32, src_addr=1, dst_addr=2,
                 sync_burst_bytes=10000, timeout=0.1, retry_limit=200):

        gr.basic_block.__init__(
            self,
            name="Text to PDU ARQ (Variable Burst)",
            in_sig=[],
            out_sig=[]
        )

        # ---------------- PARAMETERS ----------------
        self._pkt_size = int(pkt_size)
        self._src = int(src_addr) & 0xFF
        self._dst = int(dst_addr) & 0xFF
        
        # --- BURST SIZES SETUP ---
        self._sync_len_first = int(sync_burst_bytes) # Default: 10000
        self._sync_len_next = 5000                   # Fixed: 160
        
        self._timeouttotal = 0.5
        
        self._timeout = float(timeout)
        self._retry_limit = int(retry_limit)
        # --------------------------------------------

        # Ports
        self.message_port_register_in(pmt.intern("msg_in"))
        self.message_port_register_in(pmt.intern("ack_in"))
        
        # --- NEW PORT FOR GUI ADDRESS UPDATES ---
        self.message_port_register_in(pmt.intern("dest_addr_in"))
        self.set_msg_handler(pmt.intern("dest_addr_in"), self._update_dest_addr)
        
        self.message_port_register_out(pmt.intern("pdus"))
        self.message_port_register_out(pmt.intern("status_out"))

        self.set_msg_handler(pmt.intern("msg_in"), self._process_text)
        self.set_msg_handler(pmt.intern("ack_in"), self._process_ack)

        # State
        self._tx_thread = None
        self._stop = threading.Event()
        self._ack_event = threading.Event()
        self._ack_lock = threading.Lock()
        self._expected_ack = None

    def _update_dest_addr(self, msg):
        """Updates the destination address from the GUI signal."""
        try:
            # GUI sends address as a string symbol (e.g. "2")
            if pmt.is_symbol(msg):
                val_str = pmt.symbol_to_string(msg)
                new_addr = int(val_str)
                self._dst = new_addr & 0xFF
                print(f"[ARQ] Destination set to: {self._dst}")
            elif pmt.is_integer(msg):
                self._dst = pmt.to_long(msg) & 0xFF
        except Exception as e:
            print(f"[ARQ] Error updating address: {e}")

    def _send_prepend_burst(self, length):
        if length <= 0: return
        raw = os.urandom(length)
        vec = pmt.init_u8vector(len(raw), list(raw))
        pdu = pmt.cons(pmt.PMT_NIL, vec)
        self.message_port_pub(pmt.intern("pdus"), pdu)

    def _process_text(self, msg):
        try:
            text = pmt.symbol_to_string(msg)
        except:
            return

        if self._tx_thread is None or not self._tx_thread.is_alive():
            self._stop.clear()
            self._tx_thread = threading.Thread(target=self._run, args=(text,))
            self._tx_thread.daemon = True
            self._tx_thread.start()

    def _run(self, text):
        data = text.encode("utf-8")
        chunk_size = self._pkt_size - 3
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

        pkt_num = 1
        success = True

        # ---------------- NORMAL PACKETS ----------------
        if pkt_num == 0:
            current_burst_len = self._sync_len_first
        else:
            current_burst_len = self._sync_len_next
            
        for chunk in chunks:
            if not self._send_single_packet(chunk, pkt_num, current_burst_len):
                success = False
                break

            pkt_num = (pkt_num + 1) & 0xFF
            if pkt_num == 0:
                pkt_num = 1

        # ---------------- TERMINATION PACKET ----------------
        if success and not self._stop.is_set():
            term_size = (self._pkt_size + 1) - 3
            term_payload = bytes([0xFF] * term_size)
            
            if not self._send_single_packet(term_payload, pkt_num, self._sync_len_next, termination=True):
                success = False

        # ---------------- UPDATE GUI ----------------
        if success:
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("success"))
        else:
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("fail"))

    def _send_single_packet(self, chunk, pkt_num, burst_len, termination=False):
        header = bytes([self._src, self._dst, pkt_num])
        full_packet = header + chunk

        vec = pmt.init_u8vector(len(full_packet), list(full_packet))
        pdu = pmt.cons(pmt.PMT_NIL, vec)

        with self._ack_lock:
            self._expected_ack = pkt_num
            self._ack_event.clear()

        retries = 0

        while retries < self._retry_limit and not self._stop.is_set():
            if self._retry_limit % 10 == 0:
                self._send_prepend_burst(burst_len)

            # SEND PACKET
            self.message_port_pub(pmt.intern("pdus"), pdu)
            print(f"[ARQ] Sent packet #{pkt_num:02X} (Burst: {burst_len})")

            # WAIT FOR ACK
            print(f"waiting for chunk ack")
            if self._ack_event.wait(timeout=self._timeouttotal):
                print(f"[ARQ] ACK for #{pkt_num:02X}")
                return True

            retries += 1
            print(f"[ARQ] Timeout -> retry {retries}")
        
        print(f"[ARQ] FAILED packet #{pkt_num:02X}")
        return False

    def _process_ack(self, msg):
        try:
            data = pmt.cdr(msg)
            if not pmt.is_u8vector(data): return

            arr = bytearray(pmt.u8vector_elements(data))
            if len(arr) < 4: return
            if arr[0] != 0xAA: return

            src = arr[1]
            dst = arr[2]
            ack_id = arr[3]

            if src != self._dst or dst != self._src:
                return

            with self._ack_lock:
                if ack_id == self._expected_ack:
                    self._ack_event.set()
                    
        except Exception as e:
            print(f"[ARQ] ACK error: {e}")