import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, address=1, max_packet_size=32):  # Receiver address + packet size
        gr.basic_block.__init__(
            self,
            name="pdu_deduplicator",
            in_sig=[],
            out_sig=[]
        )

        self.address = int(address) & 0xFF
        self.max_packet_size = int(max_packet_size)

        self.message_port_register_in(pmt.intern("pdus_in"))
        self.message_port_register_out(pmt.intern("pdus_out"))
        self.message_port_register_out(pmt.intern("ack_packet_out"))

        self.set_msg_handler(pmt.intern("pdus_in"), self.handle_pdu)

        self.seen_packets = set()

    def reset_sequence(self):
        """Resets deduplication state after receiving termination packet."""
        print("[Deduplicator] Resetting sequence state.")
        self.seen_packets = set()

    def handle_pdu(self, msg):

        data = pmt.cdr(msg)

        if not pmt.is_u8vector(data):
            print("[Deduplicator] Invalid data type.")
            return

        byte_data = bytearray(pmt.u8vector_elements(data))

        if len(byte_data) < 3:
            print("[Deduplicator] Packet too short.")
            return

        src_addr = byte_data[0]
        dest_addr = byte_data[1]
        pkt_num = byte_data[2]

        # Only accept packets addressed to me
        if dest_addr != self.address:
            return

        # ---------------------------------------------------------
        #  CHECK FOR TERMINATION PACKET
        # ---------------------------------------------------------
        expected_term_length = self.max_packet_size + 1

        if len(byte_data) == expected_term_length:
            # termination payload = all 0xFF bytes
            payload = byte_data[3:]
            if all(b == 0xFF for b in payload):

                print(f"[Deduplicator] Termination packet #{pkt_num:02X} received. Sending ACK & resetting.")

                # Send ACK (same mechanism as normal)
                ack_packet = bytes([0xAA, self.address, src_addr, pkt_num])
                ack_pdu = pmt.cons(pmt.make_dict(),
                                   pmt.init_u8vector(len(ack_packet), list(ack_packet)))

                for _ in range(80):
                    self.message_port_pub(pmt.intern("ack_packet_out"), ack_pdu)

                # Reset deduplication for next message
                self.reset_sequence()

                # DO NOT forward termination packet
                return

        # ---------------------------------------------------------
        #  NORMAL PACKET HANDLING
        # ---------------------------------------------------------

        # Duplicate check
        if pkt_num in self.seen_packets:
            print(f"[Deduplicator] Duplicate packet #{pkt_num:02X} discarded.")
            return

        self.seen_packets.add(pkt_num)

        # Forward stripped payload (remove src,dest,pktnum)
        stripped_payload = byte_data[3:]
        payload = pmt.init_u8vector(len(stripped_payload), list(stripped_payload))
        pdu = pmt.cons(pmt.make_dict(), payload)
        self.message_port_pub(pmt.intern("pdus_out"), pdu)

        # Send ACK
        ack_packet = bytes([0xAA, self.address, src_addr, pkt_num])
        ack_pdu = pmt.cons(pmt.make_dict(),
                           pmt.init_u8vector(len(ack_packet), list(ack_packet)))

        print("[Deduplicator] Sending ACK...")
        for _ in range(80):
            self.message_port_pub(pmt.intern("ack_packet_out"), ack_pdu)

        print(f"[Deduplicator] Accepted packet #{pkt_num:02X} from {src_addr:02X}. Sent ACK.")
