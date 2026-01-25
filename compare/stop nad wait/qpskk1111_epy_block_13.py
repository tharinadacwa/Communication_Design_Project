import os
import pmt
from gnuradio import gr

class ack_sync_prepender(gr.basic_block):
    """
    Inserts a sync burst BEFORE every ACK PDU.
    The sync burst function sends the burst itself.
    """

    def __init__(self, sync_len_bytes=200):
        gr.basic_block.__init__(
            self,
            name="ack_sync_prepender",
            in_sig=[],
            out_sig=[]
        )

        self.sync_len = int(sync_len_bytes)  # FIXED: Reduced from 2000 to 200 bytes

        self.message_port_register_in(pmt.intern("ack_in"))
        self.message_port_register_out(pmt.intern("ack_out"))

        self.set_msg_handler(pmt.intern("ack_in"), self.handle_ack)


    # --------------------------------------------------------
    # This function CREATES + PUBLISHES the sync burst itself
    # --------------------------------------------------------
    def send_sync_burst(self):
        sync_data = os.urandom(self.sync_len)

        vec = pmt.init_u8vector(self.sync_len, list(sync_data))
        burst_pdu = pmt.cons(pmt.PMT_NIL, vec)

        # <---- the burst is SENT here ---->
        self.message_port_pub(pmt.intern("ack_out"), burst_pdu)

        print(f"[ACK SYNC] Sent burst ({self.sync_len} bytes)")


    # --------------------------------------------------------
    # ACK handler
    # --------------------------------------------------------
    def handle_ack(self, msg):
        """
        msg is the original ACK PDU.

        This block outputs:

            [SYNC BURST]
            [ACK PDU]
        """
        # 1) send the sync burst
        self.send_sync_burst()

        # 2) forward ACK
        self.message_port_pub(pmt.intern("ack_out"), msg)

        print(f"[ACK SYNC] Forwarded ACK")

