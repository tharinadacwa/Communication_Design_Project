import pmt
from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import datetime

# ==========================================
# 1. CUSTOM UI COMPONENTS
# ==========================================

class WallpaperScrollArea(QtWidgets.QScrollArea):
    def __init__(self, bg_image="", parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.bg_pixmap = QtGui.QPixmap(bg_image) if bg_image else None

    def paintEvent(self, event):
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            painter = QtGui.QPainter(self.viewport())
            scaled_pixmap = self.bg_pixmap.scaled(
                self.viewport().size(),
                QtCore.Qt.KeepAspectRatioByExpanding,
                QtCore.Qt.SmoothTransformation
            )
            x = (self.viewport().width() - scaled_pixmap.width()) // 2
            y = (self.viewport().height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        super().paintEvent(event)

# ==========================================
# 2. THE MAIN WINDOW (GUI LOGIC)
# ==========================================
class MessengerWindow(QtWidgets.QWidget):
    # Signals to GR
    send_to_gr_signal = QtCore.pyqtSignal(str)
    addr_selected_signal = QtCore.pyqtSignal(str)

    def __init__(self, bg_image=""):
        super().__init__()
        self.setWindowTitle("BellLabz - Control Center")
        self.resize(950, 700)
        self.bg_image_path = bg_image
        
        # --- STATE FLAGS ---
        self.is_waiting_for_ack = False 
        
        # --- DATA STRUCTURES ---
        self.added_addresses = set()
        self.selected_btn = None 
        self.current_dest_address = None
        
        # Structure: { addr_int: {'page': widget, 'layout': box, 'scroll': area, 'btn': btn_obj, 'dot': dot_label} }
        self.user_data = {} 

        # --- STYLES ---
        self.style_btn_normal = """
            QPushButton {
                background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50;
                padding: 12px; border-radius: 6px; text-align: left;
            }
            QPushButton:hover { background-color: #4b6584; }
            QPushButton:disabled { background-color: #2c3e50; color: #7f8c8d; border: 1px solid #2c3e50; }
        """
        self.style_btn_selected = """
            QPushButton {
                background-color: #27ae60; color: white; border: 2px solid white;
                padding: 12px; border-radius: 6px; text-align: left; font-weight: bold;
            }
            QPushButton:disabled { background-color: #2ecc71; opacity: 0.7; }
        """

        # --- MAIN LAYOUT ---
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self._init_sidebar()
        self._init_right_panel()

    def _init_sidebar(self):
        self.sidebar = QtWidgets.QWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #2c3e50; border-right: 1px solid #1a252f;")
        layout = QtWidgets.QVBoxLayout(self.sidebar)
        layout.setSpacing(10)

        header = QtWidgets.QLabel("CHATS")
        header.setStyleSheet("color: #95a5a6; font-weight: bold; margin-top: 10px; font-size: 14px;")
        layout.addWidget(header)

        # Input
        input_con = QtWidgets.QHBoxLayout()
        self.addr_input = QtWidgets.QLineEdit()
        self.addr_input.setPlaceholderText("ID (0-255)")
        self.addr_input.setStyleSheet("""
            QLineEdit { background: #ecf0f1; border: none; border-radius: 4px; padding: 8px; color: black; }
            QLineEdit:disabled { background: #95a5a6; color: #555; }
        """)
        self.addr_input.setValidator(QtGui.QIntValidator(0, 255))
        self.addr_input.returnPressed.connect(self.manual_add_address)

        self.add_btn = QtWidgets.QPushButton("+")
        self.add_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.add_btn.setFixedWidth(40)
        self.add_btn.clicked.connect(self.manual_add_address)
        self.add_btn.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none; border-radius: 4px; font-weight: bold; }
            QPushButton:disabled { background: #7f8c8d; }
        """)
        
        input_con.addWidget(self.addr_input)
        input_con.addWidget(self.add_btn)
        layout.addLayout(input_con)

        layout.addWidget(self._create_separator())

        # Contact List Scroll
        self.contact_scroll = QtWidgets.QScrollArea()
        self.contact_scroll.setWidgetResizable(True)
        self.contact_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.contact_container = QtWidgets.QWidget()
        self.contact_layout = QtWidgets.QVBoxLayout(self.contact_container)
        self.contact_layout.setAlignment(QtCore.Qt.AlignTop)
        self.contact_layout.setSpacing(5)
        self.contact_scroll.setWidget(self.contact_container)

        layout.addWidget(self.contact_scroll)
        self.main_layout.addWidget(self.sidebar)

    def _init_right_panel(self):
        right_panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(right_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stack for Chat Pages
        self.chat_stack = QtWidgets.QStackedWidget()
        welcome_page = QtWidgets.QLabel("Select a contact to start messaging")
        welcome_page.setAlignment(QtCore.Qt.AlignCenter)
        welcome_page.setStyleSheet("background-color: #e5ddd5; color: #888; font-size: 18px;")
        self.chat_stack.addWidget(welcome_page)
        layout.addWidget(self.chat_stack, stretch=1)

        # Input Area
        self.input_box_wrapper = QtWidgets.QWidget()
        self.input_box_wrapper.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #dcdcdc;")
        input_box_layout = QtWidgets.QHBoxLayout(self.input_box_wrapper)
        input_box_layout.setContentsMargins(10, 10, 10, 10)
        
        self.msg_input = QtWidgets.QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.setStyleSheet("""
            QLineEdit { border-radius: 20px; padding: 10px 15px; background: white; border: 1px solid #ccc; font-size: 14px; }
            QLineEdit:disabled { background-color: #e0e0e0; color: #888; }
        """)
        
        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton { background-color: #008069; color: white; border-radius: 20px; padding: 10px 20px; font-weight: bold; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        
        self.msg_input.returnPressed.connect(self.on_send_click)
        self.send_btn.clicked.connect(self.on_send_click)

        input_box_layout.addWidget(self.msg_input)
        input_box_layout.addWidget(self.send_btn)

        layout.addWidget(self.input_box_wrapper)
        self.main_layout.addWidget(right_panel)
        
        self.input_box_wrapper.hide()

    def _create_separator(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #3e5871;")
        return line

    def manual_add_address(self):
        text = self.addr_input.text().strip()
        if not text: return
        try:
            val = int(text)
            self.ensure_user_exists(val)
            # Simulate click to select logic
            btn = self.user_data[val]['btn']
            self.handle_address_click(btn, val)
            self.addr_input.clear()
        except ValueError:
            pass

    def ensure_user_exists(self, address_val):
        """Creates user context if it doesn't exist."""
        if address_val in self.user_data:
            return self.user_data[address_val]

        self.added_addresses.add(address_val)

        # 1. Create Sidebar Button Widget
        btn = QtWidgets.QPushButton(f"Node {address_val}")
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setStyleSheet(self.style_btn_normal)
        btn.setFixedHeight(50)
        
        btn.clicked.connect(lambda checked, b=btn, a=address_val: self.handle_address_click(b, a))
        self.contact_layout.addWidget(btn)

        # 2. Create Chat Page
        new_chat_page = self._create_chat_page_widget()
        self.chat_stack.addWidget(new_chat_page)
        
        chat_layout = new_chat_page.widget().layout()
        
        # Store Data
        self.user_data[address_val] = {
            "page": new_chat_page,
            "layout": chat_layout,
            "scroll_area": new_chat_page,
            "btn": btn,
            "has_unread": False
        }
        
        return self.user_data[address_val]

    def _create_chat_page_widget(self):
        scroll = WallpaperScrollArea(bg_image=self.bg_image_path)
        scroll.setStyleSheet("border: none; background-color: #e5ddd5;") 
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setAlignment(QtCore.Qt.AlignTop)
        scroll.setWidget(container)
        container.setStyleSheet("background: transparent;")
        return scroll

    def handle_address_click(self, btn_obj, address_val):
        if self.is_waiting_for_ack:
            return

        if self.input_box_wrapper.isHidden():
            self.input_box_wrapper.show()

        if self.selected_btn and self.selected_btn != btn_obj:
            self.selected_btn.setStyleSheet(self.style_btn_normal)
        
        btn_obj.setStyleSheet(self.style_btn_selected)
        self.selected_btn = btn_obj
        
        if self.user_data[address_val]["has_unread"]:
            self.user_data[address_val]["has_unread"] = False
            btn_obj.setText(f"Node {address_val}") # Remove dot

        self.current_dest_address = address_val
        
        target_page = self.user_data[address_val]["page"]
        self.chat_stack.setCurrentWidget(target_page)

        # Emit Address Change to GR Block
        self.addr_selected_signal.emit(str(address_val))

    def on_send_click(self):
        if self.is_waiting_for_ack:
            return

        text = self.msg_input.text().strip()
        if not text: return
        
        if self.current_dest_address is None:
            return

        self._set_ui_busy_state(True)

        user_entry = self.user_data[self.current_dest_address]
        
        # Add SENT Bubble
        self._add_message_bubble(text, user_entry["layout"], user_entry["scroll_area"], is_sender=True)
        
        self.send_to_gr_signal.emit(text)
        self.msg_input.clear()

    @QtCore.pyqtSlot(int, str)
    def handle_received_msg(self, src_addr, text):
        """Called when a PDU arrives from GNU Radio"""
        user_entry = self.ensure_user_exists(src_addr)
        self._add_message_bubble(text, user_entry["layout"], user_entry["scroll_area"], is_sender=False)
        
        if self.current_dest_address != src_addr:
            user_entry["has_unread"] = True
            btn = user_entry["btn"]
            if "●" not in btn.text():
                btn.setText(f"Node {src_addr} ●")

    def _add_message_bubble(self, text, layout, scroll_area, is_sender):
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(0,0,0,0)

        h_scroll = QtWidgets.QScrollArea()
        h_scroll.setWidgetResizable(True)
        h_scroll.setFixedHeight(60)
        h_scroll.setStyleSheet("background: transparent; border: none;")
        h_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        h_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        lbl = QtWidgets.QLabel(text)
        
        if is_sender:
            lbl.setStyleSheet("background-color: #dcf8c6; padding: 8px; border-radius: 10px; font-size: 16px; color: black;")
            align = QtCore.Qt.AlignRight
        else:
            lbl.setStyleSheet("background-color: #ffffff; padding: 8px; border-radius: 10px; font-size: 16px; color: black;")
            align = QtCore.Qt.AlignLeft

        h_scroll.setWidget(lbl)
        h_scroll.setMinimumWidth(100)
        h_scroll.setMaximumWidth(450)
        lbl.adjustSize()
        h_scroll.setFixedHeight(lbl.height() + 25)

        ts_text = datetime.now().strftime("%H:%M")
        ts = QtWidgets.QLabel(ts_text)
        ts.setStyleSheet("color: grey; font-size: 10px;")
        ts.setAlignment(QtCore.Qt.AlignRight if is_sender else QtCore.Qt.AlignLeft)
        
        vbox.addWidget(h_scroll)
        vbox.addWidget(ts)

        row = QtWidgets.QHBoxLayout()
        if is_sender:
            row.addStretch()
            row.addWidget(container)
            self._last_message_timestamp = ts 
        else:
            row.addWidget(container)
            row.addStretch()
        
        layout.addLayout(row)
        QtCore.QTimer.singleShot(50, lambda: scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().maximum()))

    def _set_ui_busy_state(self, is_busy):
        self.is_waiting_for_ack = is_busy
        self.msg_input.setEnabled(not is_busy)
        self.send_btn.setEnabled(not is_busy)
        self.addr_input.setEnabled(not is_busy)
        self.add_btn.setEnabled(not is_busy)

        for addr, data in self.user_data.items():
            data['btn'].setEnabled(not is_busy)
        
        if is_busy:
            self.send_btn.setText("Wait...")
        else:
            self.send_btn.setText("Send")
            self.msg_input.setFocus()

    @QtCore.pyqtSlot(str)
    def handle_feedback(self, feedback):
        if hasattr(self, '_last_message_timestamp') and self._last_message_timestamp:
            if feedback == "END_ACK_RECEIVED":
                current_text = self._last_message_timestamp.text()
                if "✓" not in current_text:
                    self._last_message_timestamp.setText(current_text + " ✓✓")
                    self._last_message_timestamp.setStyleSheet("color: #34B7F1; font-weight: bold; font-size: 10px;")
            elif feedback == "RETRY_LIMIT_EXCEEDED":
                self._last_message_timestamp.setText("Failed ❌")
                self._last_message_timestamp.setStyleSheet("color: red; font-size: 10px;")
        
        self._set_ui_busy_state(False)

# ==========================================
# 3. GNU RADIO BLOCK
# ==========================================
class GuiSignaler(QtCore.QObject):
    feedback_signal = QtCore.pyqtSignal(str)
    receive_signal = QtCore.pyqtSignal(int, str) # addr, text

class messenger_gui(gr.basic_block):
    """
    Inputs: 
       'in' (PDUs from receiver)
       'feedback' (ACK/NACK)
    Outputs: 
       'out' (payload), 
       'dest_addr' (selected address)
    """
    def __init__(self, bg_image=""):
        gr.basic_block.__init__(
            self,
            name="Messenger GUI",
            in_sig=None,
            out_sig=None,
        )

        self.message_port_register_out(pmt.intern("out"))
        self.message_port_register_out(pmt.intern("dest_addr"))
        
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_in(pmt.intern("feedback"))

        self.set_msg_handler(pmt.intern("feedback"), self._process_feedback_msg)
        self.set_msg_handler(pmt.intern("in"), self._process_incoming_pdu)

        self.qapp = QtWidgets.QApplication.instance()
        if not self.qapp:
            self.qapp = QtWidgets.QApplication(sys.argv)

        self.signaler = GuiSignaler()
        self.gui_window = MessengerWindow(bg_image=bg_image)
        
        self.signaler.feedback_signal.connect(self.gui_window.handle_feedback)
        self.signaler.receive_signal.connect(self.gui_window.handle_received_msg)
        
        self.gui_window.send_to_gr_signal.connect(self._send_payload)
        self.gui_window.addr_selected_signal.connect(self._send_dest_addr)

        self.gui_window.show()

    def _process_feedback_msg(self, msg):
        try:
            if pmt.is_symbol(msg):
                s = pmt.symbol_to_string(msg)
                self.signaler.feedback_signal.emit(s)
        except Exception:
            pass

    def _process_incoming_pdu(self, msg):
        """
        Expects PDU: Pair(Meta, u8vector).
        Byte 0 = Sender Address.
        Bytes 1+ = Text.
        """
        try:
            if not pmt.is_pair(msg): return
            vec = pmt.cdr(msg)
            if not pmt.is_u8vector(vec): return
            
            data = bytearray(pmt.u8vector_elements(vec))
            if len(data) < 1: return
            
            sender_addr = data[0] # Byte 0
            payload = data[1:]    # Remaining bytes
            
            text = payload.decode("utf-8", errors="ignore")
            
            self.signaler.receive_signal.emit(sender_addr, text)
            
        except Exception as e:
            print(f"Error processing input PDU: {e}")

    def _send_payload(self, text_msg):
        self.message_port_pub(pmt.intern("out"), pmt.string_to_symbol(text_msg))

    def _send_dest_addr(self, addr_str):
        self.message_port_pub(pmt.intern("dest_addr"), pmt.string_to_symbol(addr_str))