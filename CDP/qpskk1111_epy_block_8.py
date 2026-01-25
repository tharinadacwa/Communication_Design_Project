import pmt
from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import datetime

class MessageBubble(QtWidgets.QWidget):
    """A custom widget to render a message bubble"""
    def __init__(self, text, time_str, status="Waiting", parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 5, 0, 5)

        self.container = QtWidgets.QFrame()
        self.container_layout = QtWidgets.QVBoxLayout()
        self.container.setLayout(self.container_layout)
        
        self.container.setStyleSheet("""
            QFrame {
                background-color: #EEFFDD; 
                border-radius: 10px;
                border: 1px solid #CCDDCC;
            }
        """)

        self.lbl_text = QtWidgets.QLabel(text)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("border: none; font-size: 14px; color: black;")
        self.container_layout.addWidget(self.lbl_text)

        self.meta_layout = QtWidgets.QHBoxLayout()
        self.lbl_time = QtWidgets.QLabel(time_str)
        self.lbl_time.setStyleSheet("border: none; font-size: 10px; color: #555;")
        
        self.lbl_status = QtWidgets.QLabel(status)
        self.lbl_status.setStyleSheet("border: none; font-size: 10px; font-weight: bold; color: gray;")
        
        self.meta_layout.addStretch()
        self.meta_layout.addWidget(self.lbl_time)
        self.meta_layout.addWidget(self.lbl_status)
        self.container_layout.addLayout(self.meta_layout)

        self.layout.addStretch()
        self.layout.addWidget(self.container)
        self.setLayout(self.layout)

    def set_status(self, status, color):
        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet(f"border: none; font-size: 10px; font-weight: bold; color: {color};")
        if status == "Failed":
             self.container.setStyleSheet("QFrame { background-color: #FFDDDD; border-radius: 10px; border: 1px solid #DDAAAA; }")
        elif "Sent" in status:
             self.container.setStyleSheet("QFrame { background-color: #EEFFDD; border-radius: 10px; border: 1px solid #CCDDCC; }")

class ChatWindow(QtWidgets.QWidget):
    """The Telegram-style Window"""
    send_signal = QtCore.pyqtSignal(str)
    # NEW: Internal signal for thread-safe updates
    status_signal = QtCore.pyqtSignal(str, str) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Radio Chat")
        self.resize(400, 600)
        self.setStyleSheet("background-color: #E6EBEF;")

        layout = QtWidgets.QVBoxLayout()

        self.chat_area = QtWidgets.QListWidget()
        self.chat_area.setStyleSheet("border: none; background-color: transparent;")
        self.chat_area.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.chat_area.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        layout.addWidget(self.chat_area)

        input_container = QtWidgets.QWidget()
        input_container.setStyleSheet("background-color: white; border-top: 1px solid #DDD;")
        input_layout = QtWidgets.QHBoxLayout()
        input_container.setLayout(input_layout)

        self.text_input = QtWidgets.QLineEdit()
        self.text_input.setPlaceholderText("Write a message...")
        self.text_input.returnPressed.connect(self.on_send)
        input_layout.addWidget(self.text_input)

        self.send_btn = QtWidgets.QPushButton("➤") 
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet("background-color: #3390EC; color: white; border-radius: 20px; font-weight: bold;")
        self.send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_container)
        self.setLayout(layout)

        self.current_bubble = None
        
        # Connect the signal to the update function
        self.status_signal.connect(self.update_last_status)

    def on_send(self):
        text = self.text_input.text().strip()
        if text:
            self.text_input.clear()
            time_str = datetime.datetime.now().strftime("%H:%M")
            self.current_bubble = MessageBubble(text, time_str, "Sending...")
            
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(self.current_bubble.sizeHint())
            self.chat_area.addItem(item)
            self.chat_area.setItemWidget(item, self.current_bubble)
            self.chat_area.scrollToBottom()

            self.send_signal.emit(text)

    def update_last_status(self, text, color):
        if self.current_bubble:
            self.current_bubble.set_status(text, color)

class ChatInterface(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="Chat Interface (Telegram Style)",
            in_sig=None,
            out_sig=None
        )

        self.message_port_register_out(pmt.intern("msg_out"))
        self.message_port_register_in(pmt.intern("status_in"))
        self.set_msg_handler(pmt.intern("status_in"), self.handle_status)

        self.qapp = QtWidgets.QApplication.instance()
        if not self.qapp:
            self.qapp = QtWidgets.QApplication(sys.argv)

        self.gui = ChatWindow()
        self.gui.send_signal.connect(self.send_message)
        self.gui.show()

    def send_message(self, text):
        msg = pmt.intern(text)
        self.message_port_pub(pmt.intern("msg_out"), msg)

    def handle_status(self, msg):
        """Receives status updates from Block 2"""
        try:
            status_str = pmt.symbol_to_string(msg)
            
            # DEBUG PRINT: Check if this appears in your GRC console!
            print(f"[GUI] Status received: '{status_str}'")

            if status_str == "success":
                # Use signal to update GUI safely
                self.gui.status_signal.emit("✓ Sent", "#3390EC")
            elif status_str == "fail":
                self.gui.status_signal.emit("Failed", "red")
            elif status_str == "pending":
                pass

        except Exception as e:
            print(f"[GUI] Error handling status: {e}")

    def stop(self):
        self.gui.close()
        return super().stop()