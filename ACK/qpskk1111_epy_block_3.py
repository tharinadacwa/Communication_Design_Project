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
        self.message_port_register_out(pmt.intern("feedback"))

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
            nack = pmt.to_pmt(("nack", 0x00))  # or unknown packet
            self.message_port_pub(pmt.intern("feedback"), nack)
            return

        packet_num = byte_data[0]

        if packet_num in self.seen_packets:
            # Duplicate packet
            print(f"[Deduplicator] Duplicate packet #{packet_num:02X} discarded.")
            nack = pmt.to_pmt(("nack", packet_num))
            self.message_port_pub(pmt.intern("feedback"), nack)
            return

        # New packet
        self.seen_packets.add(packet_num)

        # Send ACK
        ack = pmt.cons(pmt.intern("ack"), pmt.from_long(packet_num))
        #ack = pmt.to_pmt(("ack", packet_num))
        print(pmt.is_pair(ack))  
        self.message_port_pub(pmt.intern("feedback"), ack)

        # Strip first byte and forward payload
        stripped_data = byte_data[1:]
        payload = pmt.init_u8vector(len(stripped_data), stripped_data)
        pdu = pmt.cons(pmt.make_dict(), payload)

        self.message_port_pub(pmt.intern("pdus_out"), pdu)
        print(f"[Deduplicator] Passed packet #{packet_num:02X} and sent ACK.")
