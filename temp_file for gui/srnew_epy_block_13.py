import os
import pmt
from gnuradio import gr

class ack_sync_prepender(gr.basic_block):
    """
    Inserts a sync burst BEFORE every ACK PDU.
    1st ACK: 10,000 bytes burst
    Subsequent ACKs: 1,000 bytes burst
    """

    def __init__(self, sync_len_first=10000):
        gr.basic_block.__init__(
            self,
            name="ack_sync_prepender",
            in_sig=[],
            out_sig=[]
        )

        # --- BURST SIZE CONFIGURATION ---
        self.sync_len_first = int(sync_len_first)  # Default: 10000
        self.sync_len_next = 2000                  # Fixed: 1000
        
        # --- STATE ---
        # Keeps track if we have sent the first ACK yet
        self._is_first_ack = True

        self.message_port_register_in(pmt.intern("ack_in"))
        self.message_port_register_out(pmt.intern("ack_out"))

        self.set_msg_handler(pmt.intern("ack_in"), self.handle_ack)


    # --------------------------------------------------------
    # This function CREATES + PUBLISHES the sync burst
    # --------------------------------------------------------
    def send_sync_burst(self, length):
        
        # Create random bytes of exactly 'length' size
        sync_data = os.urandom(length)

        vec = pmt.init_u8vector(length, list(sync_data))
        burst_pdu = pmt.cons(pmt.PMT_NIL, vec)

        # <---- the burst is SENT here ---->
        self.message_port_pub(pmt.intern("ack_out"), burst_pdu)

        # Debug print (Optional)
        # if length > 2000:
        #     print(f"[ACK SYNC] Sent FIRST burst ({length} bytes)")
        # else:
        #     print(f"[ACK SYNC] Sent burst ({length} bytes)")


    # --------------------------------------------------------
    # ACK handler
    # --------------------------------------------------------
    def handle_ack(self, msg):
        """
        msg is the original ACK PDU.

        This block outputs:
            [SYNC BURST (Variable Size)]
            [ACK PDU]
        """
        
        # --- DECIDE BURST SIZE ---
        if self._is_first_ack:
            current_len = self.sync_len_first
            self._is_first_ack = False # Mark that we have handled the first one
        else:
            current_len = self.sync_len_next

        # 1) send the sync burst with the calculated length
        self.send_sync_burst(current_len)

        # 2) forward ACK
        for _ in range(10):
            self.message_port_pub(pmt.intern("ack_out"), msg)

