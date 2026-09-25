import sys
import os
import importlib

_qt_widgets = None
_qt_core = None
for _mod in ['PyQt5.QtWidgets', 'PySide2.QtWidgets', 'PyQt6.QtWidgets', 'PySide6.QtWidgets']:
    try:
        _qt_widgets = importlib.import_module(_mod)
        break
    except (ImportError, ModuleNotFoundError):
        pass

for _mod in ['PyQt5.QtCore', 'PySide2.QtCore', 'PyQt6.QtCore', 'PySide6.QtCore']:
    try:
        _qt_core = importlib.import_module(_mod)
        break
    except (ImportError, ModuleNotFoundError):
        pass

Qt = getattr(_qt_core, 'Qt', None)

if _qt_widgets is None:
    # Fallback dummy class definitions so static analyzers don't fail if Qt is absent in IDE
    class _Dummy:
        def __init__(self, *args, **kwargs): pass
        def __getattr__(self, name): return _Dummy
    QApplication = QMainWindow = QWidget = QTabWidget = QVBoxLayout = QHBoxLayout = QLabel = QLineEdit = QPushButton = QCheckBox = QComboBox = QRadioButton = QSlider = QSpinBox = QProgressBar = QTextEdit = _Dummy
else:
    QApplication = _qt_widgets.QApplication
    QMainWindow = _qt_widgets.QMainWindow
    QWidget = _qt_widgets.QWidget
    QTabWidget = _qt_widgets.QTabWidget
    QVBoxLayout = _qt_widgets.QVBoxLayout
    QHBoxLayout = _qt_widgets.QHBoxLayout
    QLabel = _qt_widgets.QLabel
    QLineEdit = _qt_widgets.QLineEdit
    QPushButton = _qt_widgets.QPushButton
    QCheckBox = _qt_widgets.QCheckBox
    QComboBox = _qt_widgets.QComboBox
    QRadioButton = _qt_widgets.QRadioButton
    QSlider = _qt_widgets.QSlider
    QSpinBox = _qt_widgets.QSpinBox
    QProgressBar = _qt_widgets.QProgressBar
    QTextEdit = _qt_widgets.QTextEdit

try:
    from robotframework_qtexpert.agent import start_agent
except ImportError:
    start_agent = None

class Qt5DemoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Railway Yard Operations & Dispatch Manager")
        self.setObjectName("mainWindow")
        self.resize(760, 640)
        self.click_count = 0
        self.emergency_active = False

        # Apply Modern SCADA Railway Yard Dark Theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111827;
            }
            QTabWidget::pane {
                border: 2px solid #1f2937;
                background-color: #1f2937;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #111827;
                color: #9ca3af;
                padding: 10px 18px;
                font-weight: bold;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1f2937;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QLabel {
                color: #f3f4f6;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #374151;
                color: #ffffff;
                border: 1px solid #4b5563;
                padding: 7px 10px;
                border-radius: 5px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #38bdf8;
            }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QCheckBox, QRadioButton {
                color: #e5e7eb;
                font-size: 13px;
                spacing: 8px;
            }
            QProgressBar {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 5px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #059669;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #374151;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 5px;
                font-size: 13px;
                padding: 6px;
            }
        """)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("mainTabWidget")

        # ==========================================
        # Tab 1: Operator Authentication & Docs
        # ==========================================
        login_tab = QWidget()
        login_tab.setObjectName("loginTab")
        login_layout = QVBoxLayout(login_tab)
        login_layout.setContentsMargins(24, 18, 24, 18)
        login_layout.setSpacing(10)

        banner = QLabel("🚂 RAILWAY YARD CONTROL TOWER - DISPATCHER AUTH", login_tab)
        banner.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8; margin-bottom: 6px;")

        user_label = QLabel("Yard Operator ID:", login_tab)
        self.username_input = QLineEdit(login_tab)
        self.username_input.setObjectName("usernameInput")
        self.username_input.setPlaceholderText("Enter operator ID (e.g. admin)")

        pass_label = QLabel("Dispatch Authorization Key:", login_tab)
        self.password_input = QLineEdit(login_tab)
        self.password_input.setObjectName("passwordInput")
        self.password_input.setPlaceholderText("Enter security key")
        echo_mode = getattr(QLineEdit, 'EchoMode', QLineEdit).Password
        self.password_input.setEchoMode(echo_mode)

        self.remember_check = QCheckBox("Remember Me (Retain Shift Session)", login_tab)
        self.remember_check.setObjectName("rememberMeCheck")

        # Clickable Documentation Link
        self.doc_link = QLabel('<a href="safety_rules" style="color: #38bdf8; text-decoration: underline; font-weight: bold;">📋 Review Yard Operating & Safety Rules (Reg 492)</a>', login_tab)
        self.doc_link.setObjectName("docLinkLabel")
        if hasattr(self.doc_link, 'setTextInteractionFlags'):
            self.doc_link.setTextInteractionFlags(getattr(getattr(Qt, 'TextInteractionFlag', Qt), 'TextBrowserInteraction', 1))
        self.doc_link.linkActivated.connect(self.on_link_activated)

        self.doc_status = QLabel("Safety Protocol: Pending Review", login_tab)
        self.doc_status.setObjectName("docStatusLabel")
        self.doc_status.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 12px;")

        self.login_btn = QPushButton("Authorize & Enter Yard Console", login_tab)
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setStyleSheet("background-color: #059669; font-size: 14px;")
        self.login_btn.clicked.connect(self.on_login_click)

        self.status_label = QLabel("Please enter credentials", login_tab)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("color: #fbbf24; font-weight: bold; padding-top: 4px;")

        login_layout.addWidget(banner)
        login_layout.addWidget(user_label)
        login_layout.addWidget(self.username_input)
        login_layout.addWidget(pass_label)
        login_layout.addWidget(self.password_input)
        login_layout.addWidget(self.remember_check)
        login_layout.addWidget(self.doc_link)
        login_layout.addWidget(self.doc_status)
        login_layout.addWidget(self.login_btn)
        login_layout.addWidget(self.status_label)
        login_layout.addStretch()

        # ==========================================
        # Tab 2: Track & Route Dispatcher
        # ==========================================
        dispatch_tab = QWidget()
        dispatch_tab.setObjectName("dispatchTab")
        dispatch_layout = QVBoxLayout(dispatch_tab)
        dispatch_layout.setContentsMargins(24, 18, 24, 18)
        dispatch_layout.setSpacing(10)

        disp_title = QLabel("SWITCH ALIGNMENT & ROUTE INTERLOCKING", dispatch_tab)
        disp_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")

        train_label = QLabel("Incoming / Staged Train ID:", dispatch_tab)
        self.train_input = QLineEdit(dispatch_tab)
        self.train_input.setObjectName("trainIdInput")
        self.train_input.setText("FRT-4892")

        track_label = QLabel("Assigned Destination Track:", dispatch_tab)
        self.combo = QComboBox(dispatch_tab)
        self.combo.setObjectName("optionsCombo")
        self.combo.addItems([
            "Track 1 - Mainline Express",
            "Track 2 - Freight Classification Siding",
            "Track 3 - Intermodal Container Yard",
            "Track 4 - Heavy Maintenance Depot"
        ])

        # Radio Group for Train Clearance Priority
        prio_title = QLabel("Train Clearance Priority Tier:", dispatch_tab)
        prio_layout = QHBoxLayout()
        self.radio_freight = QRadioButton("Standard Freight", dispatch_tab)
        self.radio_freight.setObjectName("radioFreight")
        self.radio_express = QRadioButton("Express Passenger", dispatch_tab)
        self.radio_express.setObjectName("radioExpress")
        self.radio_express.setChecked(True)
        self.radio_hazmat = QRadioButton("Hazmat Cargo", dispatch_tab)
        self.radio_hazmat.setObjectName("radioHazmat")
        prio_layout.addWidget(self.radio_freight)
        prio_layout.addWidget(self.radio_express)
        prio_layout.addWidget(self.radio_hazmat)
        prio_layout.addStretch()

        self.priority_status = QLabel("Priority Tier: Express Passenger", dispatch_tab)
        self.priority_status.setObjectName("priorityStatusLabel")
        self.priority_status.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")

        self.radio_freight.toggled.connect(lambda c: c and self.priority_status.setText("Priority Tier: Standard Freight"))
        self.radio_express.toggled.connect(lambda c: c and self.priority_status.setText("Priority Tier: Express Passenger"))
        self.radio_hazmat.toggled.connect(lambda c: c and self.priority_status.setText("Priority Tier: Hazmat Cargo"))

        # Safety Interlocking Checkboxes
        chk_title = QLabel("Interlocking Safety Verification:", dispatch_tab)
        chk_layout = QHBoxLayout()
        self.chk_catenary = QCheckBox("Overhead 25kV Catenary Energized", dispatch_tab)
        self.chk_catenary.setObjectName("chkCatenary")
        self.chk_retarders = QCheckBox("Track Retarders Active", dispatch_tab)
        self.chk_retarders.setObjectName("chkRetarders")
        self.chk_retarders.setChecked(True)
        chk_layout.addWidget(self.chk_catenary)
        chk_layout.addWidget(self.chk_retarders)
        chk_layout.addStretch()

        self.signal_status = QLabel("SIGNAL STATUS: CAUTION / HOLD", dispatch_tab)
        self.signal_status.setObjectName("signalStatusLabel")
        self.signal_status.setStyleSheet("background-color: #78350f; color: #fde68a; padding: 7px; border-radius: 4px; font-weight: bold;")

        self.align_btn = QPushButton("Align Switch Points & Lock Route", dispatch_tab)
        self.align_btn.setObjectName("alignSwitchBtn")
        self.align_btn.setStyleSheet("background-color: #0284c7;")
        self.align_btn.clicked.connect(self.on_align_route)

        self.route_status = QLabel("Route status: Awaiting alignment command", dispatch_tab)
        self.route_status.setObjectName("routeStatusLabel")
        self.route_status.setStyleSheet("color: #94a3b8; font-style: italic;")

        dispatch_layout.addWidget(disp_title)
        dispatch_layout.addWidget(train_label)
        dispatch_layout.addWidget(self.train_input)
        dispatch_layout.addWidget(track_label)
        dispatch_layout.addWidget(self.combo)
        dispatch_layout.addWidget(prio_title)
        dispatch_layout.addLayout(prio_layout)
        dispatch_layout.addWidget(self.priority_status)
        dispatch_layout.addWidget(chk_title)
        dispatch_layout.addLayout(chk_layout)
        dispatch_layout.addWidget(self.align_btn)
        dispatch_layout.addWidget(self.signal_status)
        dispatch_layout.addWidget(self.route_status)
        dispatch_layout.addStretch()

        # ==========================================
        # Tab 3: Shunting & Yard Operations
        # ==========================================
        controls_tab = QWidget()
        controls_tab.setObjectName("controlsTab")
        ctrl_layout = QVBoxLayout(controls_tab)
        ctrl_layout.setContentsMargins(24, 18, 24, 18)
        ctrl_layout.setSpacing(10)

        counter_title = QLabel("TRAIN DEPARTURE & SHUNTING OPERATIONS", controls_tab)
        counter_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")

        # Counter section
        cnt_layout = QHBoxLayout()
        self.counter_label = QLabel("Clicks: 0", controls_tab)
        self.counter_label.setObjectName("counterLabel")
        self.counter_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981; padding: 4px;")
        self.inc_btn = QPushButton("Increment Counter", controls_tab)
        self.inc_btn.setObjectName("incrementButton")
        self.inc_btn.setStyleSheet("background-color: #059669;")
        self.inc_btn.clicked.connect(self.on_increment_click)
        cnt_layout.addWidget(self.counter_label)
        cnt_layout.addWidget(self.inc_btn)
        cnt_layout.addStretch()

        # Slider: Hump Speed Control
        horiz = getattr(getattr(Qt, 'Orientation', Qt), 'Horizontal', 1)
        self.speed_slider = QSlider(horiz, controls_tab)
        self.speed_slider.setObjectName("humpSpeedSlider")
        self.speed_slider.setRange(0, 60)
        self.speed_slider.setValue(25)
        self.slider_label = QLabel("Hump Shunting Speed: 25 km/h", controls_tab)
        self.slider_label.setObjectName("sliderValLabel")
        self.slider_label.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.speed_slider.valueChanged.connect(lambda v: self.slider_label.setText(f"Hump Shunting Speed: {v} km/h"))

        # SpinBox: Consist Wagon Count
        spin_layout = QHBoxLayout()
        spin_title = QLabel("Consist Wagon Count:", controls_tab)
        self.wagon_spin = QSpinBox(controls_tab)
        self.wagon_spin.setObjectName("wagonCountSpin")
        self.wagon_spin.setRange(1, 120)
        self.wagon_spin.setValue(18)
        self.wagon_label = QLabel("Total Wagons in Cut: 18 cars", controls_tab)
        self.wagon_label.setObjectName("wagonValLabel")
        self.wagon_label.setStyleSheet("color: #a7f3d0; font-weight: bold;")
        self.wagon_spin.valueChanged.connect(lambda v: self.wagon_label.setText(f"Total Wagons in Cut: {v} cars"))
        spin_layout.addWidget(spin_title)
        spin_layout.addWidget(self.wagon_spin)
        spin_layout.addWidget(self.wagon_label)
        spin_layout.addStretch()

        # Progress Bar: Track Capacity Utilization
        cap_title = QLabel("Yard Track Siding Capacity Utilization:", controls_tab)
        self.capacity_bar = QProgressBar(controls_tab)
        self.capacity_bar.setObjectName("yardCapacityBar")
        self.capacity_bar.setRange(0, 100)
        self.capacity_bar.setValue(68)

        # Train Manifest Text
        manifest_layout = QHBoxLayout()
        self.my_input = QLineEdit(controls_tab)
        self.my_input.setObjectName("myInput")
        self.my_input.setPlaceholderText("Enter train manifest details")
        self.my_btn = QPushButton("Click Me", controls_tab)
        self.my_btn.setObjectName("myButton")
        self.my_btn.clicked.connect(lambda: self.my_label.setText(f"Hello, {self.my_input.text()}!"))
        manifest_layout.addWidget(self.my_input)
        manifest_layout.addWidget(self.my_btn)

        self.my_label = QLabel("", controls_tab)
        self.my_label.setObjectName("myLabel")
        self.my_label.setStyleSheet("color: #a7f3d0; font-weight: bold;")

        # Multi-line TextEdit: Shift Dispatcher Notes
        notes_title = QLabel("Shift Handover Dispatcher Notes:", controls_tab)
        self.shift_notes = QTextEdit(controls_tab)
        self.shift_notes.setObjectName("shiftNotesEdit")
        self.shift_notes.setPlaceholderText("Enter shift handover dispatcher notes...")
        self.shift_notes.setFixedHeight(50)

        # Emergency Halt Section
        self.emergency_btn = QPushButton("🚨 EMERGENCY YARD ALL-TRACK HALT", controls_tab)
        self.emergency_btn.setObjectName("emergencyHaltBtn")
        self.emergency_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 9px;")
        self.emergency_btn.clicked.connect(self.on_emergency_toggle)

        self.yard_banner = QLabel("YARD STATUS: NORMAL OPERATIONS", controls_tab)
        self.yard_banner.setObjectName("yardBannerLabel")
        self.yard_banner.setStyleSheet("color: #34d399; font-weight: bold;")

        ctrl_layout.addWidget(counter_title)
        ctrl_layout.addLayout(cnt_layout)
        ctrl_layout.addWidget(self.slider_label)
        ctrl_layout.addWidget(self.speed_slider)
        ctrl_layout.addLayout(spin_layout)
        ctrl_layout.addWidget(cap_title)
        ctrl_layout.addWidget(self.capacity_bar)
        ctrl_layout.addLayout(manifest_layout)
        ctrl_layout.addWidget(self.my_label)
        ctrl_layout.addWidget(notes_title)
        ctrl_layout.addWidget(self.shift_notes)
        ctrl_layout.addWidget(self.emergency_btn)
        ctrl_layout.addWidget(self.yard_banner)
        ctrl_layout.addStretch()

        self.tabs.addTab(login_tab, "Dispatcher Auth")
        self.tabs.addTab(dispatch_tab, "Route Alignment")
        self.tabs.addTab(controls_tab, "Yard Operations")
        self.setCentralWidget(self.tabs)

    def on_link_activated(self, link):
        self.doc_status.setText("Safety Protocol: Reviewed & Interlock Accepted")
        self.doc_status.setStyleSheet("color: #34d399; font-weight: bold; font-size: 12px;")

    def on_login_click(self):
        u = self.username_input.text().strip()
        p = self.password_input.text().strip()
        if u == "admin" and p == "secret123":
            self.status_label.setText("Login Successful!")
            self.status_label.setStyleSheet("color: #34d399; font-weight: bold;")
            self.tabs.setCurrentIndex(1)
        else:
            self.status_label.setText("Invalid Credentials!")
            self.status_label.setStyleSheet("color: #f87171; font-weight: bold;")

    def on_align_route(self):
        train = self.train_input.text().strip() or "TRAIN"
        track = self.combo.currentText().split("-")[0].strip()
        self.signal_status.setText(f"SIGNAL STATUS: CLEAR / GREEN - {track.upper()}")
        self.signal_status.setStyleSheet("background-color: #065f46; color: #6ee7b7; padding: 7px; border-radius: 4px; font-weight: bold;")
        self.route_status.setText(f"Route locked: {train} aligned to {track}")
        self.route_status.setStyleSheet("color: #38bdf8; font-weight: bold;")

    def on_emergency_toggle(self):
        self.emergency_active = not self.emergency_active
        if self.emergency_active:
            self.yard_banner.setText("YARD STATUS: EMERGENCY STOP ACTIVE - ALL SIGNALS RED")
            self.yard_banner.setStyleSheet("color: #ef4444; font-weight: bold; background-color: #450a0a; padding: 6px;")
            self.signal_status.setText("SIGNAL STATUS: EMERGENCY RED - HALT")
            self.signal_status.setStyleSheet("background-color: #991b1b; color: #fecaca; padding: 7px; border-radius: 4px; font-weight: bold;")
        else:
            self.yard_banner.setText("YARD STATUS: NORMAL OPERATIONS")
            self.yard_banner.setStyleSheet("color: #34d399; font-weight: bold;")
            self.signal_status.setText("SIGNAL STATUS: CAUTION / HOLD")
            self.signal_status.setStyleSheet("background-color: #78350f; color: #fde68a; padding: 7px; border-radius: 4px; font-weight: bold;")

    def on_increment_click(self):
        self.click_count += 1
        self.counter_label.setText(f"Clicks: {self.click_count}")

def main():
    app = QApplication(sys.argv)
    window = Qt5DemoApp()
    window.show()

    port_file = os.environ.get('QT_AGENT_PORT_FILE')
    agent_port = None
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        if idx + 1 < len(sys.argv):
            agent_port = int(sys.argv[idx + 1])
    elif 'QT_AGENT_PORT' in os.environ:
        agent_port = int(os.environ['QT_AGENT_PORT'])
    elif '--agent' in sys.argv:
        agent_port = 9988

    if (port_file or agent_port is not None) and start_agent:
        p = agent_port if agent_port is not None else 0
        agent = start_agent(app, port=p)
        if port_file:
            with open(port_file, 'w') as f:
                f.write(str(agent.port))
        print(f"[QtAgent] Yard Manager running with agent on port {agent.port}")

    exec_fn = getattr(app, 'exec', getattr(app, 'exec_', None))
    sys.exit(exec_fn())

if __name__ == '__main__':
    main()
