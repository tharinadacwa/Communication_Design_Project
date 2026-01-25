import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, address=1, max_packet_size=32):
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

        # ---------------------------------------------------
        # NEW: State for ACK forwarding
        # ---------------------------------------------------
        self.last_ack_forwarded = None
        self.expected_ack_pkt = 0

    def reset_sequence(self):
        print("[Deduplicator] Resetting sequence state.")
        self.seen_packets = set()
        self.last_ack_forwarded = None
        self.expected_ack_pkt = 0

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

        # ===========================================================
        # NEW: Detect ACK packet coming *from transmitter*
        # ===========================================================
        if byte_data[0] == 0xAA:
            ack_src = byte_data[1]
            ack_dest = byte_data[2]
            ack_num = byte_data[3]

            # Check if ACK is expected
            if ack_num == self.expected_ack_pkt:

                # avoid forwarding duplicates
                if self.last_ack_forwarded != ack_num:
                    print(f"[Deduplicator] Forwarding expected ACK #{ack_num:02X}.")
                    ack_pdu = pmt.cons(
                        pmt.make_dict(),
                        pmt.init_u8vector(len(byte_data), list(byte_data))
                    )
                    self.message_port_pub(pmt.intern("pdus_out"), ack_pdu)
                    self.last_ack_forwarded = ack_num

                    # next expected ACK
                    self.expected_ack_pkt += 1

                else:
                    print(f"[Deduplicator] Duplicate expected ACK #{ack_num:02X} ignored.")

            else:
                print(f"[Deduplicator] Unexpected ACK #{ack_num:02X} discarded.")

            return
        # ===========================================================


        if dest_addr != self.address:
            return

        expected_term_length = self.max_packet_size + 1

        # ---------------------------------------------------------
        # TERMINATION PACKET
        # ---------------------------------------------------------
        if len(byte_data) == expected_term_length:
            payload = byte_data[3:]
            if all(b == 0xFF for b in payload):

                print(f"[Deduplicator] Termination packet #{pkt_num:02X} received.")

                # ---- Send ACK ----
                ack_packet = bytes([0xAA, self.address, src_addr, pkt_num])
                ack_pdu = pmt.cons(pmt.make_dict(),
                                   pmt.init_u8vector(len(ack_packet), list(ack_packet)))

                #for _ in range(80):
                self.message_port_pub(pmt.intern("ack_packet_out"), ack_pdu)

                # ---- Forward termination to next block ----
                forward_bytes = bytes([pkt_num]) + byte_data[3:]  # pkt_num + all FFs
                payload_pdu = pmt.init_u8vector(len(forward_bytes), list(forward_bytes))
                out = pmt.cons(pmt.make_dict(), payload_pdu)
                self.message_port_pub(pmt.intern("pdus_out"), out)

                # ---- Reset dedup ----
                self.reset_sequence()

                return

        # ---------------------------------------------------------
        # NORMAL PACKET
        # ---------------------------------------------------------
        if pkt_num in self.seen_packets:
            print(f"[Deduplicator] Duplicate packet #{pkt_num:02X} discarded.")
            return

        self.seen_packets.add(pkt_num)

        forward_bytes = bytes([pkt_num]) + byte_data[3:]
        payload = pmt.init_u8vector(len(forward_bytes), list(forward_bytes))
        out_pdu = pmt.cons(pmt.make_dict(), payload)
        self.message_port_pub(pmt.intern("pdus_out"), out_pdu)

        # ACK
        ack_packet = bytes([0xAA, self.address, src_addr, pkt_num])
        ack_pdu = pmt.cons(pmt.make_dict(),
                           pmt.init_u8vector(len(ack_packet), list(ack_packet)))

        
        self.message_port_pub(pmt.intern("ack_packet_out"), ack_pdu)

        print(f"[Deduplicator] Accepted packet #{pkt_num:02X}.")

