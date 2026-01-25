import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):

    def __init__(self, num_bytes=4):
        gr.basic_block.__init__(
            self,
            name="PDU Prepend Random Bytes",
            in_sig=None,
            out_sig=None
        )

        self.num_bytes = int(num_bytes)

        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))

        self.set_msg_handler(pmt.intern("in"), self.handle_msg)


    def handle_msg(self, msg):
        meta = pmt.car(msg)
        vec = pmt.cdr(msg)

        payload = bytes(pmt.u8vector_elements(vec))

        # random bytes
        prepend = np.random.randint(0, 256, self.num_bytes, dtype=np.uint8).tolist()

        # convert payload to list of ints
        payload_list = list(payload)

        # final output list
        out_list = prepend + payload_list

        # convert back to PDU
        out_vec = pmt.init_u8vector(len(out_list), out_list)

        self.message_port_pub(
            pmt.intern("out"),
            pmt.cons(meta, out_vec)
        )
