#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import pmt
import time
import os
from gnuradio import gr

class pdu_text_gui(gr.basic_block):
    """
    Custom block: QT GUI Message Entry -> PDU sender with Go-Back-N ARQ.
    NOW SUPPORTS:
    - sync_bits : number of random bytes transmitted before each retransmission.
    - Sync burst has NO headers, NO packetization. It is PURE RANDOM BYTE STREAM.
    """

    def __init__(self, wait_time=2.0, pkt_size=32, address=0x01,
                 retry_limit=100, window_size=4, sync_bits=1000):

        gr.basic_block.__init__(
            self,
            name="GUI Text to PDU with Go-Back-N ARQ + Sync Burst",
            in_sig=[],
            out_sig=[]
        )

        # Parameters
        self._timeout = float(wait_time)
        self._pkt_size = int(pkt_size)
        self._address = int(address) & 0xFF
        self._retry_limit = int(retry_limit)
        self._window_size = int(window_size)
        self._sync_bits = int(sync_bits)   # NEW PARAMETER

        # Seq/ACK control
        self._seq_id = 1
        self._last_ack_seq = 0
        self._has_acks = False

        # Register message ports
        self.message_port_register_out(pmt.intern("out"))
        self.message_port_register_out(pmt.intern("feedback"))
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_in(pmt.intern("ack_in"))

        self.set_msg_handler(pmt.intern("in"), self._process_text)
        self.set_msg_handler(pmt.intern("ack_in"), self._process_ack)

        # Thread control
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Data buffers
        self._text_data = b""
        self._packets = []
        self._base = 0
        self._next_to_send = 0
        self._attempts = 0
        self._end_seq_id = 0

    # -------------------------------------------------
    # Sync Burst Sender (PURE RANDOM BYTES)
    # -------------------------------------------------
    def _send_sync_burst(self):
        if self._sync_bits <= 0:
            return

        # Pure random bytes, no header
        sync_data = os.urandom(self._sync_bits)

        vec = pmt.init_u8vector(len(sync_data), list(sync_data))
        pdu = pmt.cons(pmt.PMT_NIL, vec)

        print(f"[pdu_text_gui] SYNC BURST sent ({len(sync_data)} bytes)")
        self.message_port_pub(pmt.intern("out"), pdu)

    # -------------------------------------------------
    # Handle input text
    # -------------------------------------------------
    def _process_text(self, msg):
        try:
            if pmt.is_symbol(msg):
                text_str = pmt.symbol_to_string(msg)
            elif pmt.is_string(msg):
                text_str = pmt.string_to_string(msg)
            else:
                print("[pdu_text_gui] Invalid PMT format")
                return

            self._text_data = text_str.encode("utf-8")

            if self._thread is None or not self._thread.is_alive():
                self._stop_event.clear()
                self._thread = threading.Thread(target=self._run)
                self._thread.daemon = True
                self._thread.start()

        except Exception as e:
            print(f"[pdu_text_gui] Error processing text: {e}")

    # -------------------------------------------------
    # Main ARQ loop
    # -------------------------------------------------
    def _run(self):
        raw = self._text_data
        step = self._pkt_size - 2
        blocks = [raw[i:i+step] for i in range(0, len(raw), step)]

        # Choose starting seq
        if self._has_acks:
            self._seq_id = (self._last_ack_seq + 1) & 0xFF
            if self._seq_id == 0:
                self._seq_id = 1
        else:
            self._seq_id = 1

        print(f"[pdu_text_gui] Starting TX at seq=0x{self._seq_id:02X}")

        # Build packets
        self._packets = []
        for block in blocks:
            packet = bytes([self._address, self._seq_id]) + block
            self._packets.append((self._seq_id, packet))

            self._seq_id = (self._seq_id + 1) & 0xFF
            if self._seq_id == 0:
                self._seq_id = 1

        # End packet
        end_packet = bytes([self._address, self._seq_id])
        self._packets.append((self._seq_id, end_packet))
        self._end_seq_id = self._seq_id

        print(f"[pdu_text_gui] END packet: seq=0x{self._seq_id:02X}")

        self._seq_id = (self._seq_id + 1) & 0xFF
        if self._seq_id == 0:
            self._seq_id = 1

        # Reset window
        self._base = 0
        self._next_to_send = 0
        self._attempts = 0

        # --------------------------------------------------
        # ARQ LOOP
        # --------------------------------------------------
        while self._base < len(self._packets) and not self._stop_event.is_set():

            # Try sending packets in window
            with self._lock:
                while self._next_to_send < self._base + self._window_size and \
                      self._next_to_send < len(self._packets):

                    seq_id, packet = self._packets[self._next_to_send]

                    vec = pmt.init_u8vector(len(packet), list(packet))
                    pdu = pmt.cons(pmt.PMT_NIL, vec)
                    self.message_port_pub(pmt.intern("out"), pdu)

                    if len(packet) > 2:
                        print(f"[pdu_text_gui] Sent id=0x{seq_id:02X}")
                    else:
                        print(f"[pdu_text_gui] Sent END id=0x{seq_id:02X}")

                    self._next_to_send += 1

            # Wait for ACK
            time.sleep(self._timeout)

            # Timeout -> Retransmit window
            with self._lock:
                if self._base < self._next_to_send:

                    self._attempts += 1
                    if self._attempts >= self._retry_limit:
                        print("[pdu_text_gui] Retry limit exceeded")
                        self.message_port_pub(pmt.intern("feedback"),
                                              pmt.intern("RETRY_LIMIT_EXCEEDED"))
                        self._stop_event.set()
                        break

                    print("[pdu_text_gui] TIMEOUT → Sync Burst + Retransmit window")

                    # 🔥 SEND RAW SYNC BURST FIRST
                    self._send_sync_burst()

                    # retransmit packets
                    for i in range(self._base, self._next_to_send):
                        seq_id, packet = self._packets[i]

                        vec = pmt.init_u8vector(len(packet), list(packet))
                        pdu = pmt.cons(pmt.PMT_NIL, vec)
                        self.message_port_pub(pmt.intern("out"), pdu)

                        if len(packet) > 2:
                            print(f"[pdu_text_gui] Retransmit id=0x{seq_id:02X}")
                        else:
                            print(f"[pdu_text_gui] Retransmit END id=0x{seq_id:02X}")

    # -------------------------------------------------
    # ACK handler
    # -------------------------------------------------
    def _process_ack(self, msg):
        try:
            payload = pmt.cdr(msg)
            if not pmt.is_u8vector(payload):
                return

            arr = bytearray(pmt.u8vector_elements(payload))
            if len(arr) < 2:
                return
            if arr[0] != 0xAA:
                return

            ack_id = arr[1]

            with self._lock:
                for i in range(self._base, self._next_to_send):
                    seq_id, _ = self._packets[i]

                    if seq_id == ack_id:
                        self._has_acks = True
                        self._last_ack_seq = ack_id

                        if len(self._packets[i][1]) > 2:
                            print(f"[pdu_text_gui] ACK for 0x{ack_id:02X}")
                        else:
                            print(f"[pdu_text_gui] ACK END 0x{ack_id:02X}")
                            self.message_port_pub(pmt.intern("feedback"),
                                                  pmt.intern("END_ACK_RECEIVED"))

                        self._base = i + 1
                        self._attempts = 0
                        break

        except Exception as e:
            print(f"[pdu_text_gui] ACK error: {e}")

