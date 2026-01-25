import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="pdu_deduplicator",
            in_sig=[],
            out_sig=[]
        )

        self.message_port_register_in(pmt.intern("pdus_in"))
        self.message_port_register_out(pmt.intern("pdus_out"))
        self.message_port_register_out(pmt.intern("ack_packet_out"))  # NEW

        self.set_msg_handler(pmt.intern("pdus_in"), self.handle_pdu)

        self.seen_packets = set()

    def handle_pdu(self, msg):
        meta = pmt.car(msg)
        data = pmt.cdr(msg)

        if not pmt.is_u8vector(data):
            print("[Deduplicator] Invalid data type.")
            return

        byte_data = bytearray(pmt.u8vector_elements(data))

        if len(byte_data) == 0:
            print("[Deduplicator] Empty PDU received.")
            return

        packet_num = byte_data[0]

        if packet_num in self.seen_packets:
            # Duplicate packet
            print(f"[Deduplicator] Duplicate packet #{packet_num:02X} discarded.")
            return

        # New packet
        self.seen_packets.add(packet_num)

        # Strip first byte and forward remaining data
        stripped_data = byte_data[1:]
        payload = pmt.init_u8vector(len(stripped_data), stripped_data)
        pdu = pmt.cons(pmt.make_dict(), payload)
        self.message_port_pub(pmt.intern("pdus_out"), pdu)

        # ----- Create physical-layer ACK packet -----
        ack_header = 0xAA  # Fixed header for ACKs
        ack_packet = bytes([ack_header, packet_num])  # [0xAA][packet_num]
        print("hiiiiiiiiiiiiii")
        ack_pdu = pmt.cons(
            pmt.make_dict(),
            pmt.init_u8vector(len(ack_packet), list(ack_packet))
        )


                # Send ACK multiple times to improve PHY-layer reception
        repeat_count = 20
        for i in range(repeat_count):
            self.message_port_pub(pmt.intern("ack_packet_out"), ack_pdu)

        print(f"[Deduplicator] Sent physical ACK packet {repeat_count} times: [{ack_header:02X} {packet_num:02X}]")
