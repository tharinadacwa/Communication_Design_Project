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
            name="Text to PDU ARQ (with Prepend Burst)",
            in_sig=[],
            out_sig=[]
        )

        # ---------------- PARAMETERS ----------------
        self._pkt_size = int(pkt_size)
        self._src = int(src_addr) & 0xFF
        self._dst = int(dst_addr) & 0xFF
        self._sync_len = int(sync_burst_bytes)
        self._timeout = float(timeout)
        self._retry_limit = int(retry_limit)
        # --------------------------------------------

        # Ports
        self.message_port_register_in(pmt.intern("msg_in"))
        self.message_port_register_in(pmt.intern("ack_in"))
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

    # ================================================================
    #  SEND SYNC BURST  (PURE RANDOM BYTES AS A SEPARATE PDU)
    # ================================================================
    def _send_prepend_burst(self):
        if self._sync_len <= 0:
            return

        raw = os.urandom(self._sync_len)
        vec = pmt.init_u8vector(len(raw), list(raw))
        pdu = pmt.cons(pmt.PMT_NIL, vec)

        print(f"[ARQ] PREPEND BURST ({len(raw)} bytes)")
        self.message_port_pub(pmt.intern("pdus"), pdu)

    # ================================================================
    #  HANDLE INPUT TEXT
    # ================================================================
    def _process_text(self, msg):
        try:
            text = pmt.symbol_to_string(msg)
        except:
            # print("[ARQ] Invalid PMT text")
            return

        if self._tx_thread is None or not self._tx_thread.is_alive():
            self._stop.clear()
            self._tx_thread = threading.Thread(target=self._run, args=(text,))
            self._tx_thread.daemon = True
            self._tx_thread.start()

    # ================================================================
    #  MAIN TRANSMISSION (STOP-AND-WAIT)
    # ================================================================
    def _run(self, text):
        data = text.encode("utf-8")
        chunk_size = self._pkt_size - 3
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

        pkt_num = 1
        success = True

        # ---------------- NORMAL PACKETS ----------------
        for chunk in chunks:
            if not self._send_single_packet(chunk, pkt_num):
                success = False
                break

            pkt_num = (pkt_num + 1) & 0xFF
            if pkt_num == 0:
                pkt_num = 1

        # ---------------- TERMINATION PACKET ----------------
        if success and not self._stop.is_set():
            term_size = (self._pkt_size + 1) - 3
            term_payload = bytes([0xFF] * term_size)
            if not self._send_single_packet(term_payload, pkt_num, termination=True):
                success = False

        # ---------------- UPDATE GUI ----------------
        if success:
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("success"))
        else:
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("fail"))

    # ================================================================
    #  SEND ONE PACKET WITH ARQ
    # ================================================================
    def _send_single_packet(self, chunk, pkt_num, termination=False):

        header = bytes([self._src, self._dst, pkt_num])
        full_packet = header + chunk

        vec = pmt.init_u8vector(len(full_packet), list(full_packet))
        pdu = pmt.cons(pmt.PMT_NIL, vec)

        with self._ack_lock:
            self._expected_ack = pkt_num
            self._ack_event.clear()

        retries = 0

        while retries < self._retry_limit and not self._stop.is_set():

            # PREPEND BURST BEFORE EVERY PDU
            self._send_prepend_burst()

            # SEND PACKET
            self.message_port_pub(pmt.intern("pdus"), pdu)
            print(f"[ARQ] Sent packet #{pkt_num:02X}")

            # WAIT FOR ACK
            if self._ack_event.wait(timeout=self._timeout):
                print(f"[ARQ] ACK for #{pkt_num:02X}")
                return True

            retries += 1
            print(f"[ARQ] Timeout → retry {retries}")

        print(f"[ARQ] FAILED packet #{pkt_num:02X}")
        return False

    # ================================================================
    #  ACK HANDLER
    # ================================================================
    def _process_ack(self, msg):
        try:
            data = pmt.cdr(msg)
            if not pmt.is_u8vector(data):
                return

            arr = bytearray(pmt.u8vector_elements(data))
            if len(arr) < 4:
                return
            if arr[0] != 0xAA:
                return

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

