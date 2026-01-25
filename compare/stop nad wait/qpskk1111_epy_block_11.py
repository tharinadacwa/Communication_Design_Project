import pmt
import os
import threading
import time
from gnuradio import gr

class TextToPDU_ARQ(gr.basic_block):
    def __init__(self, max_packet_size=32, src_address=1, dest_address=2):
        gr.basic_block.__init__(
            self,
            name="Text to PDU (ARQ Logic + 10000 Bytes Prepend)",
            in_sig=[],
            out_sig=[]
        )
        
        # --- CONFIGURATION ---
        self.interval = 0.1
        self.max_packet_size = int(max_packet_size)
        self.src_address = int(src_address) & 0xFF
        self.dest_address = int(dest_address) & 0xFF
        self._sync_bits = 0  # FIXED: Disable pre-packet sync burst (was corrupting demod)
        # -------------------

        # Hardcoded 10000 bytes (example: repeating pattern 0x12..0xF0)
        base = [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]
        self.prepend_bytes = (base * 10000)[:10000]
        print("prepend ready")

        # Message ports
        self.message_port_register_out(pmt.intern("pdus"))
        self.message_port_register_in(pmt.intern("ack_bits"))
        self.set_msg_handler(pmt.intern("ack_bits"), self.handle_ack_bits)

        self.message_port_register_in(pmt.intern("msg_in"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg_input)
        self.message_port_register_out(pmt.intern("status_out"))

        # Threading / state
        self._stop_event = threading.Event()
        self._ack_event = threading.Event()
        self._ack_lock = threading.Lock()
        self._expected_ack = None
        self._tx_lock = threading.Lock()

    def stop(self):
        self._stop_event.set()
        self._ack_event.set()
        return super().stop()

    def handle_msg_input(self, msg):
        text_data = pmt.symbol_to_string(msg)
        if self._tx_lock.locked():
            return
        t = threading.Thread(target=self._process_transmission, args=(text_data,))
        t.daemon = True
        t.start()
    
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
        self.message_port_pub(pmt.intern("pdus"), pdu)

    def _process_transmission(self, text_data):
        with self._tx_lock:
            self.message_port_pub(pmt.intern("status_out"), pmt.intern("pending"))
            
            data = text_data.encode('utf-8')
            chunk_size = self.max_packet_size - 3
            chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

            packet_number = 1
            success = True

            # --- SEND NORMAL PACKETS ---
            for chunk in chunks:
                if self._stop_event.is_set():
                    success = False
                    break

                # prepend 10000 bytes
                full_packet = bytes([self.src_address, self.dest_address, packet_number]) + chunk
                payload = pmt.init_u8vector(len(full_packet), list(full_packet))
                #pdu = pmt.cons(pmt.make_dict(), payload)
                
                self._send_sync_burst()
                pdu = pmt.cons(pmt.PMT_NIL, payload)

                with self._ack_lock:
                    self._expected_ack = packet_number
                    self._ack_event.clear()

                retry_count = 0
                max_retries = 200
                chunk_sent_successfully = False

                while not self._stop_event.is_set() and retry_count < max_retries:
                    self.message_port_pub(pmt.intern("pdus"), pdu)

                    ack_received = self._ack_event.wait(timeout=self.interval)
                    if ack_received:
                        chunk_sent_successfully = True
                        break
                    else:
                        retry_count += 1

                if not chunk_sent_successfully:
                    print(f"[ARQ] Failed to send packet #{packet_number:02X}")
                    success = False
                    break

                packet_number = (packet_number + 1) & 0xFF
                if packet_number == 0x00:
                    packet_number = 0x01

            # --- SEND TERMINATION PACKET ---
            if success and not self._stop_event.is_set():
                term_packet_number = packet_number
                term_payload_len = (self.max_packet_size + 1) - 3
                term_payload = bytes([0xFF] * term_payload_len)

                full_packet = bytes([self.src_address, self.dest_address, term_packet_number]) + term_payload
                payload = pmt.init_u8vector(len(full_packet), list(full_packet))
                #pdu = pmt.cons(pmt.make_dict(), payload)
                
                self._send_sync_burst()
                pdu = pmt.cons(pmt.PMT_NIL, payload)

                with self._ack_lock:
                    self._expected_ack = term_packet_number
                    self._ack_event.clear()


                retry_count = 0
                max_retries = 200
                term_success = False

                while not self._stop_event.is_set() and retry_count < max_retries:
                    self.message_port_pub(pmt.intern("pdus"), pdu)

                    ack_received = self._ack_event.wait(timeout=self.interval)
                    if ack_received:
                        term_success = True
                        break
                    else:
                        print(f"[ARQ] Timeout waiting for TERMINATION ACK #{term_packet_number:02X}")
                        retry_count += 1

                if not term_success:
                    print(f"[ARQ] Failed to send TERMINATION packet #{term_packet_number:02X}")
                    success = False

            # Update GUI
            if success:
                self.message_port_pub(pmt.intern("status_out"), pmt.intern("success"))
            else:
                self.message_port_pub(pmt.intern("status_out"), pmt.intern("fail"))

    def handle_ack_bits(self, msg):
        try:
            data = pmt.cdr(msg)
            if not pmt.is_u8vector(data):
                return

            byte_data = bytearray(pmt.u8vector_elements(data))
            if len(byte_data) < 4:
                return
            
            if byte_data[0] != 0xAA:
                return

            ack_src_addr = byte_data[1]
            ack_dest_addr = byte_data[2]
            ack_packet_num = byte_data[3]

            if ack_dest_addr != self.src_address:
                return
            if ack_src_addr != self.dest_address:
                return

            with self._ack_lock:
                if ack_packet_num == self._expected_ack:
                    self._ack_event.set()
                    
        except Exception as e:
            print(f"[ARQ] Error handling ACK: {str(e)}")

