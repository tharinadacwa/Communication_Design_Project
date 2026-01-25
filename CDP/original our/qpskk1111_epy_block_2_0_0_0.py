"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import threading
import pmt
import time
import os
from gnuradio import gr

class TextToPDU_StopWait_Addr(gr.basic_block):
    """
    Text to PDU: Stop-and-Wait ARQ + Sync Burst + ADDRESSING.
    
    - Header: [Src Addr, Dest Addr, Sequence ID] (3 Bytes)
    - ACK Format: [0xAA, Src, Dest, Seq]
    - Logic: Sends packet, waits for ACK from specific address, resends on timeout.
    """

    def __init__(self, wait_time=2.0, pkt_size=32, src_address=1, dest_address=2, retry_limit=100, sync_bits=1000):

        gr.basic_block.__init__(
            self,
            name="Text to PDU (Stop-and-Wait Addr)",
            in_sig=[],
            out_sig=[]
        )

        # Parameters
        self._timeout = float(wait_time)
        self._pkt_size = int(pkt_size)
        self._src_addr = int(src_address) & 0xFF  # My Address
        self._dest_addr = int(dest_address) & 0xFF # Target Address
        self._retry_limit = int(retry_limit)
        self._sync_bits = int(sync_bits)

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

    def _send_sync_burst(self):
        """Sends random garbage data to wake up the receiver"""
        if self._sync_bits <= 0:
            return
        sync_data = os.urandom(self._sync_bits)
        vec = pmt.init_u8vector(len(sync_data), list(sync_data))
        pdu = pmt.cons(pmt.PMT_NIL, vec)
        # FIX: Removed special characters from print
        print(f"[StopWait] SYNC BURST sent ({len(sync_data)} bytes)")
        self.message_port_pub(pmt.intern("out"), pdu)

    def _process_text(self, msg):
        try:
            if pmt.is_symbol(msg):
                text_str = pmt.symbol_to_string(msg)
            elif pmt.is_string(msg):
                text_str = pmt.string_to_string(msg)
            else:
                print("[StopWait] Invalid PMT format")
                return

            self._text_data = text_str.encode("utf-8")

            if self._thread is None or not self._thread.is_alive():
                self._stop_event.clear()
                self._thread = threading.Thread(target=self._run)
                self._thread.daemon = True
                self._thread.start()

        except Exception as e:
            print(f"[StopWait] Error processing text: {e}")

    def _run(self):
        raw = self._text_data
        
        # CHANGED: Step is now pkt_size - 3 (3 Bytes for Header: Src, Dest, Seq)
        step = self._pkt_size - 3
        if step <= 0:
            print("[StopWait] Error: Packet size too small for header!")
            return

        blocks = [raw[i:i+step] for i in range(0, len(raw), step)]

        # Choose starting seq
        if self._has_acks:
            self._seq_id = (self._last_ack_seq + 1) & 0xFF
            if self._seq_id == 0: self._seq_id = 1
        else:
            self._seq_id = 1

        print(f"[StopWait] Starting TX at seq=0x{self._seq_id:02X}")

        # Build packets
        self._packets = []
        for block in blocks:
            # CHANGED: Header includes Src and Dest
            packet = bytes([self._src_addr, self._dest_addr, self._seq_id]) + block
            self._packets.append((self._seq_id, packet))

            self._seq_id = (self._seq_id + 1) & 0xFF
            if self._seq_id == 0: self._seq_id = 1

        # End packet (Header only)
        end_packet = bytes([self._src_addr, self._dest_addr, self._seq_id])
        self._packets.append((self._seq_id, end_packet))
        
        print(f"[StopWait] END packet: seq=0x{self._seq_id:02X}")

        self._seq_id = (self._seq_id + 1) & 0xFF
        if self._seq_id == 0: self._seq_id = 1

        # Reset State
        self._base = 0
        self._next_to_send = 0
        self._attempts = 0

        # --- TRANSMISSION LOOP ---
        while self._base < len(self._packets) and not self._stop_event.is_set():

            # 1. SEND
            with self._lock:
                if self._next_to_send == self._base:
                    seq_id, packet = self._packets[self._base]
                    vec = pmt.init_u8vector(len(packet), list(packet))
                    pdu = pmt.cons(pmt.PMT_NIL, vec)
                    self.message_port_pub(pmt.intern("out"), pdu)

                    if len(packet) > 3: # >3 because header is 3 bytes
                        print(f"[StopWait] Sent id=0x{seq_id:02X}")
                    else:
                        print(f"[StopWait] Sent END id=0x{seq_id:02X}")

                    self._next_to_send += 1

            # 2. WAIT
            time.sleep(self._timeout)

            # 3. CHECK STATUS
            with self._lock:
                if self._base < self._next_to_send:
                    self._attempts += 1
                    if self._attempts >= self._retry_limit:
                        print("[StopWait] Retry limit exceeded")
                        self.message_port_pub(pmt.intern("feedback"), pmt.intern("RETRY_LIMIT_EXCEEDED"))
                        self._stop_event.set()
                        break
                    
                    # FIX: Replaced unicode arrow with standard ASCII "->"
                    print("[StopWait] TIMEOUT -> Sync Burst + Resend")
                    self._send_sync_burst()
                    self._next_to_send = self._base

    def _process_ack(self, msg):
        try:
            payload = pmt.cdr(msg)
            if not pmt.is_u8vector(payload): return

            arr = bytearray(pmt.u8vector_elements(payload))
            if len(arr) < 4: return # Needs at least 4 bytes: [AA, Src, Dest, Seq]
            
            # 1. Check Magic Byte
            if arr[0] != 0xAA: return
            
            # 2. Extract Addresses
            ack_src = arr[1]   # Who sent the ACK?
            ack_dest = arr[2]  # Who is the ACK for?
            ack_seq = arr[3]   # Which packet is ACKed?

            # 3. Verify Address Match
            # The ACK must be intended for ME (ack_dest == my src_addr)
            if ack_dest != self._src_addr:
                return 
            
            # The ACK must come from the TARGET (ack_src == my dest_addr)
            if ack_src != self._dest_addr:
                return

            with self._lock:
                if self._base < len(self._packets):
                    current_seq_id, _ = self._packets[self._base]
                    
                    if current_seq_id == ack_seq:
                        self._has_acks = True
                        self._last_ack_seq = ack_seq
                        
                        # Check if End Packet (Length <= 3 because header is 3 bytes)
                        if len(self._packets[self._base][1]) <= 3:
                             self.message_port_pub(pmt.intern("feedback"), pmt.intern("END_ACK_RECEIVED"))
                        else:
                            print(f"[StopWait] Valid ACK received for 0x{ack_seq:02X}")

                        self._base += 1
                        self._attempts = 0

        except Exception as e:
            print(f"[StopWait] ACK error: {e}")