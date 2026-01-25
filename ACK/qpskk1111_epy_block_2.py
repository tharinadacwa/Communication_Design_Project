import pmt
import threading
import time
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, file_path="", interval=2.0, max_packet_size=32):
        gr.basic_block.__init__(
            self,
            name="File to PDU (chunked, ack-based retransmit)",
            in_sig=[],
            out_sig=[]
        )

        self.file_path = file_path
        self.interval = float(interval)
        self.max_packet_size = int(max_packet_size)

        # Output: PDUs to transmitter
        self.message_port_register_out(pmt.intern("pdus"))

        # Input: ACKs as bit-level PDUs
        self.message_port_register_in(pmt.intern("ack_bits"))
        self.set_msg_handler(pmt.intern("ack_bits"), self.handle_ack_bits)

        # Threading + ACK control
        self._stop_event = threading.Event()
        self._ack_event = threading.Event()
        self._ack_lock = threading.Lock()
        self._expected_ack = None

        self._thread = threading.Thread(target=self._send_loop)
        self._thread.daemon = True

    def start(self):
        self._stop_event.clear()
        self._thread.start()
        return super().start()

    def stop(self):
        self._stop_event.set()
        self._ack_event.set()  # Unblock any waiting
        self._thread.join()
        return super().stop()

    def _send_loop(self):
        try:
            with open(self.file_path, 'rb') as f:
                data = f.read()
        except Exception as e:
            print(f"[FileToPDU] Error reading file: {str(e)}")
            return

        # Break data into chunks (1 byte reserved for packet number)
        chunks = [
            data[i:i + self.max_packet_size - 1]
            for i in range(0, len(data), self.max_packet_size - 1)
        ]

        packet_number = 1

        for chunk in chunks:
            if self._stop_event.is_set():
                break

            # Add packet number as first byte
            full_packet = bytes([packet_number]) + chunk
            payload = pmt.init_u8vector(len(full_packet), list(full_packet))
            pdu = pmt.cons(pmt.make_dict(), payload)

            # Set expected ACK number
            with self._ack_lock:
                self._expected_ack = packet_number
                self._ack_event.clear()

            retry_count = 0
            max_retries = 100

            while not self._stop_event.is_set() and retry_count < max_retries:
                self.message_port_pub(pmt.intern("pdus"), pdu)
                print(f"[FileToPDU] Sent packet #{packet_number:02X}, attempt {retry_count + 1}")

                ack_received = self._ack_event.wait(timeout=self.interval)

                if ack_received:
                    break  # Got ACK, move on
                else:
                    print(f"[FileToPDU] Timeout waiting for ACK for packet #{packet_number:02X}, retrying...")
                    retry_count += 1

            #if retry_count == max_retries:
                #print(f"[FileToPDU] No ACK after {max_retries} attempts. Skipping packet #{packet_number:02X}.")

            if retry_count == max_retries:
                print(f"[FileToPDU] No ACK after {max_retries} attempts for packet #{packet_number:02X}.")
                print("[FileToPDU] Error occurred. Try again.")
                self._stop_event.set()
                return  # Exit the loop early

            # Increment and wrap packet number
            packet_number = (packet_number + 1) & 0xFF
            if packet_number == 0x00:
                packet_number = 0x01

    def handle_ack_bits(self, msg):
        """Receives physical-layer ACKs as PDUs (e.g., [0xAA, packet_num])"""
        try:
            meta = pmt.car(msg)
            data = pmt.cdr(msg)

            if not pmt.is_u8vector(data):
                print("[FileToPDU] Invalid ACK PDU format.")
                return

            byte_data = bytearray(pmt.u8vector_elements(data))

            if len(byte_data) < 2:
                print("[FileToPDU] ACK PDU too short.")
                return

            if byte_data[0] != 0xAA:
                print("[FileToPDU] Not a valid ACK header.")
                return

            pkt_num = byte_data[1]

            with self._ack_lock:
                if pkt_num == self._expected_ack:
                    print(f"[FileToPDU] Received PHYSICAL ACK for packet #{pkt_num:02X}")
                    self._ack_event.set()

        except Exception as e:
            print(f"[FileToPDU] Error handling physical ACK: {str(e)}")
