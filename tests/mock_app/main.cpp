#if defined(__has_include) && (__has_include(<QtWidgets/QLabel>) || __has_include(<QLabel>))
  #define HAS_QT 1
  #if __has_include(<QtWidgets/QLabel>)
    #include <QtWidgets/QApplication>
    #include <QtWidgets/QMainWindow>
    #include <QtWidgets/QTabWidget>
    #include <QtWidgets/QWidget>
    #include <QtWidgets/QVBoxLayout>
    #include <QtWidgets/QHBoxLayout>
    #include <QtWidgets/QLabel>
    #include <QtWidgets/QLineEdit>
    #include <QtWidgets/QPushButton>
    #include <QtWidgets/QCheckBox>
    #include <QtWidgets/QRadioButton>
    #include <QtWidgets/QComboBox>
    #include <QtWidgets/QSlider>
    #include <QtWidgets/QSpinBox>
    #include <QtWidgets/QProgressBar>
    #include <QtWidgets/QTextEdit>
  #else
    #include <QApplication>
    #include <QMainWindow>
    #include <QTabWidget>
    #include <QWidget>
    #include <QVBoxLayout>
    #include <QHBoxLayout>
    #include <QLabel>
    #include <QLineEdit>
    #include <QPushButton>
    #include <QCheckBox>
    #include <QRadioButton>
    #include <QComboBox>
    #include <QSlider>
    #include <QSpinBox>
    #include <QProgressBar>
    #include <QTextEdit>
  #endif
#else
  #define HAS_QT 0
  #include <string>
  #include <vector>

  #ifndef Q_OBJECT
    #define Q_OBJECT
  #endif
  #ifndef slots
    #define slots
  #endif
  #ifndef signals
    #define signals
  #endif

  namespace Qt {
      enum Orientation { Horizontal = 1, Vertical = 2 };
      enum TextInteractionFlag { TextBrowserInteraction = 1 };
  }

  struct QString;
  struct QStringList : public std::vector<QString> {
      using std::vector<QString>::vector;
      QString first() const;
  };

  struct QString {
      std::string s;
      QString() = default;
      QString(const char *str) : s(str ? str : "") {}
      QString(const std::string &str) : s(str) {}
      bool operator==(const char *other) const { return s == other; }
      bool operator==(const QString &other) const { return s == other.s; }
      QString trimmed() const { return *this; }
      bool isEmpty() const { return s.empty(); }
      QStringList split(const char *) const {
          QStringList list;
          list.push_back(*this);
          return list;
      }
      QString toUpper() const { return *this; }
      template<typename T>
      QString arg(const T &) const { return *this; }
      template<typename T1, typename T2>
      QString arg(const T1 &, const T2 &) const { return *this; }
  };

  inline QString QStringList::first() const {
      return empty() ? QString() : front();
  }

  class QObject {
  public:
      QObject(QObject * = nullptr) {}
      virtual ~QObject() = default;
      void setObjectName(const QString &) {}
  };

  template<typename T1, typename T2, typename T3, typename T4>
  inline void connect(T1, T2, T3, T4) {}
  template<typename T1, typename T2, typename T3>
  inline void connect(T1, T2, T3) {}

  class QWidget : public QObject {
  public:
      QWidget(QWidget * = nullptr) {}
      void setStyleSheet(const QString &) {}
      void resize(int, int) {}
      void setWindowTitle(const QString &) {}
      void show() {}
      void setFocus() {}
  };

  class QMainWindow : public QWidget {
  public:
      QMainWindow(QWidget * = nullptr) {}
      void setCentralWidget(QWidget *) {}
  };

  class QTabWidget : public QWidget {
  public:
      QTabWidget(QWidget * = nullptr) {}
      void addTab(QWidget *, const QString &) {}
  };

  class QLayout : public QObject {
  public:
      QLayout(QWidget * = nullptr) {}
      void setContentsMargins(int, int, int, int) {}
      void setSpacing(int) {}
      void addWidget(QWidget *) {}
      void addLayout(QLayout *) {}
      void addStretch(int = 0) {}
      void addSpacing(int) {}
  };

  class QVBoxLayout : public QLayout {
  public:
      QVBoxLayout(QWidget * = nullptr) {}
  };

  class QHBoxLayout : public QLayout {
  public:
      QHBoxLayout(QWidget * = nullptr) {}
  };

  class QLabel : public QWidget {
  public:
      QLabel(const QString & = "", QWidget * = nullptr) {}
      void setText(const QString &) {}
      void setTextInteractionFlags(int) {}
      void linkActivated(const QString & = "") {}
  };

  class QLineEdit : public QWidget {
  public:
      enum EchoMode { Normal, NoEcho, Password, PasswordEchoOnEdit };
      QLineEdit(QWidget * = nullptr) {}
      void setPlaceholderText(const QString &) {}
      void setEchoMode(EchoMode) {}
      void setText(const QString &) {}
      QString text() const { return QString(); }
  };

  class QPushButton : public QWidget {
  public:
      QPushButton(const QString & = "", QWidget * = nullptr) {}
      void clicked(bool = false) {}
  };

  class QCheckBox : public QWidget {
  public:
      QCheckBox(const QString & = "", QWidget * = nullptr) {}
      void setChecked(bool) {}
      bool isChecked() const { return false; }
      void toggled(bool = false) {}
  };

  class QRadioButton : public QWidget {
  public:
      QRadioButton(const QString & = "", QWidget * = nullptr) {}
      void setChecked(bool) {}
      bool isChecked() const { return false; }
      void toggled(bool = false) {}
  };

  class QComboBox : public QWidget {
  public:
      QComboBox(QWidget * = nullptr) {}
      void addItem(const QString &) {}
      QString currentText() const { return QString(); }
  };

  class QSlider : public QWidget {
  public:
      QSlider(int = 1, QWidget * = nullptr) {}
      void setRange(int, int) {}
      void setValue(int) {}
      int value() const { return 0; }
      void valueChanged(int = 0) {}
  };

  class QSpinBox : public QWidget {
  public:
      QSpinBox(QWidget * = nullptr) {}
      void setRange(int, int) {}
      void setValue(int) {}
      int value() const { return 0; }
      void valueChanged(int = 0) {}
  };

  class QProgressBar : public QWidget {
  public:
      QProgressBar(QWidget * = nullptr) {}
      void setRange(int, int) {}
      void setValue(int) {}
      int value() const { return 0; }
  };

  class QTextEdit : public QWidget {
  public:
      QTextEdit(QWidget * = nullptr) {}
      void setPlaceholderText(const QString &) {}
      void setFixedHeight(int) {}
      void setText(const QString &) {}
      void setPlainText(const QString &) {}
      QString toPlainText() const { return QString(); }
  };

  class QApplication {
  public:
      QApplication(int &, char **) {}
      static void setApplicationName(const QString &) {}
      int exec() { return 0; }
  };
#endif

class MockMainWindow : public QMainWindow {
    Q_OBJECT
public:
    MockMainWindow(QWidget *parent = nullptr) : QMainWindow(parent), m_clickCount(0), m_emergency(false) {
        setWindowTitle("Railway Yard Operations & Dispatch Manager");
        setObjectName("mainWindow");
        resize(760, 640);

        setStyleSheet(
            "QMainWindow { background-color: #111827; }"
            "QTabWidget::pane { border: 2px solid #1f2937; background-color: #1f2937; border-radius: 6px; }"
            "QTabBar::tab { background-color: #111827; color: #9ca3af; padding: 10px 18px; font-weight: bold; margin-right: 2px; }"
            "QTabBar::tab:selected { background-color: #1f2937; color: #38bdf8; border-bottom: 2px solid #38bdf8; }"
            "QLabel { color: #f3f4f6; font-size: 13px; font-weight: 500; }"
            "QLineEdit, QComboBox, QSpinBox { background-color: #374151; color: #ffffff; border: 1px solid #4b5563; padding: 7px 10px; border-radius: 5px; font-size: 13px; }"
            "QPushButton { background-color: #2563eb; color: #ffffff; font-weight: bold; border-radius: 5px; padding: 8px 16px; font-size: 13px; }"
            "QCheckBox, QRadioButton { color: #e5e7eb; font-size: 13px; }"
            "QProgressBar { background-color: #374151; border: 1px solid #4b5563; border-radius: 5px; text-align: center; color: #ffffff; font-weight: bold; height: 22px; }"
            "QProgressBar::chunk { background-color: #059669; border-radius: 4px; }"
            "QTextEdit { background-color: #374151; color: #ffffff; border: 1px solid #4b5563; border-radius: 5px; font-size: 13px; padding: 6px; }"
        );

        QTabWidget *tabs = new QTabWidget(this);
        tabs->setObjectName("mainTabWidget");

        // ==========================================
        // Tab 1: Dispatcher Auth & Compliance Links
        // ==========================================
        QWidget *loginTab = new QWidget();
        loginTab->setObjectName("loginTab");
        QVBoxLayout *loginLayout = new QVBoxLayout(loginTab);
        loginLayout->setContentsMargins(24, 18, 24, 18);
        loginLayout->setSpacing(10);

        QLabel *banner = new QLabel("🚂 RAILWAY YARD CONTROL TOWER - DISPATCHER AUTH", loginTab);
        banner->setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8; margin-bottom: 6px;");

        QLabel *userLabel = new QLabel("Yard Operator ID:", loginTab);
        m_usernameInput = new QLineEdit(loginTab);
        m_usernameInput->setObjectName("usernameInput");
        m_usernameInput->setPlaceholderText("Enter operator ID (e.g. admin)");

        QLabel *passLabel = new QLabel("Dispatch Authorization Key:", loginTab);
        m_passwordInput = new QLineEdit(loginTab);
        m_passwordInput->setObjectName("passwordInput");
        m_passwordInput->setPlaceholderText("Enter security key");
        m_passwordInput->setEchoMode(QLineEdit::Password);

        m_rememberMeCheck = new QCheckBox("Remember Me (Retain Shift Session)", loginTab);
        m_rememberMeCheck->setObjectName("rememberMeCheck");

        m_docLink = new QLabel("<a href=\"safety_rules\" style=\"color: #38bdf8; text-decoration: underline; font-weight: bold;\">📋 Review Yard Operating & Safety Rules (Reg 492)</a>", loginTab);
        m_docLink->setObjectName("docLinkLabel");
        m_docLink->setTextInteractionFlags(Qt::TextBrowserInteraction);

        m_docStatus = new QLabel("Safety Protocol: Pending Review", loginTab);
        m_docStatus->setObjectName("docStatusLabel");
        m_docStatus->setStyleSheet("color: #94a3b8; font-style: italic; font-size: 12px;");

        m_loginBtn = new QPushButton("Authorize & Enter Yard Console", loginTab);
        m_loginBtn->setObjectName("loginButton");
        m_loginBtn->setStyleSheet("background-color: #059669; font-size: 14px;");

        m_statusLabel = new QLabel("Please enter credentials", loginTab);
        m_statusLabel->setObjectName("statusLabel");
        m_statusLabel->setStyleSheet("color: #fbbf24; font-weight: bold; padding-top: 4px;");

        loginLayout->addWidget(banner);
        loginLayout->addWidget(userLabel);
        loginLayout->addWidget(m_usernameInput);
        loginLayout->addWidget(passLabel);
        loginLayout->addWidget(m_passwordInput);
        loginLayout->addWidget(m_rememberMeCheck);
        loginLayout->addWidget(m_docLink);
        loginLayout->addWidget(m_docStatus);
        loginLayout->addWidget(m_loginBtn);
        loginLayout->addWidget(m_statusLabel);
        loginLayout->addStretch();

        connect(m_loginBtn, &QPushButton::clicked, this, &MockMainWindow::onLoginClicked);
        connect(m_docLink, &QLabel::linkActivated, this, &MockMainWindow::onLinkActivated);

        // ==========================================
        // Tab 2: Route & Switch Alignment + Radios/Checks
        // ==========================================
        QWidget *dispatchTab = new QWidget();
        dispatchTab->setObjectName("dispatchTab");
        QVBoxLayout *dispatchLayout = new QVBoxLayout(dispatchTab);
        dispatchLayout->setContentsMargins(24, 18, 24, 18);
        dispatchLayout->setSpacing(10);

        QLabel *dispTitle = new QLabel("SWITCH ALIGNMENT & ROUTE INTERLOCKING", dispatchTab);
        dispTitle->setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;");

        QLabel *trainLabel = new QLabel("Incoming / Staged Train ID:", dispatchTab);
        m_trainInput = new QLineEdit(dispatchTab);
        m_trainInput->setObjectName("trainIdInput");
        m_trainInput->setText("FRT-4892");

        QLabel *trackLabel = new QLabel("Assigned Destination Track:", dispatchTab);
        m_comboBox = new QComboBox(dispatchTab);
        m_comboBox->setObjectName("optionsCombo");
        m_comboBox->addItem("Track 1 - Mainline Express");
        m_comboBox->addItem("Track 2 - Freight Classification Siding");
        m_comboBox->addItem("Track 3 - Intermodal Container Yard");
        m_comboBox->addItem("Track 4 - Heavy Maintenance Depot");

        // Radio group for priority
        QLabel *prioTitle = new QLabel("Train Clearance Priority Tier:", dispatchTab);
        QHBoxLayout *prioLayout = new QHBoxLayout();
        m_radioFreight = new QRadioButton("Standard Freight", dispatchTab);
        m_radioFreight->setObjectName("radioFreight");
        m_radioExpress = new QRadioButton("Express Passenger", dispatchTab);
        m_radioExpress->setObjectName("radioExpress");
        m_radioExpress->setChecked(true);
        m_radioHazmat = new QRadioButton("Hazmat Cargo", dispatchTab);
        m_radioHazmat->setObjectName("radioHazmat");
        prioLayout->addWidget(m_radioFreight);
        prioLayout->addWidget(m_radioExpress);
        prioLayout->addWidget(m_radioHazmat);
        prioLayout->addStretch();

        m_priorityStatus = new QLabel("Priority Tier: Express Passenger", dispatchTab);
        m_priorityStatus->setObjectName("priorityStatusLabel");
        m_priorityStatus->setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;");

        connect(m_radioFreight, &QRadioButton::toggled, this, [this](bool c) {
            if (c) m_priorityStatus->setText("Priority Tier: Standard Freight");
        });
        connect(m_radioExpress, &QRadioButton::toggled, this, [this](bool c) {
            if (c) m_priorityStatus->setText("Priority Tier: Express Passenger");
        });
        connect(m_radioHazmat, &QRadioButton::toggled, this, [this](bool c) {
            if (c) m_priorityStatus->setText("Priority Tier: Hazmat Cargo");
        });

        // Safety Interlocking Checkboxes
        QLabel *chkTitle = new QLabel("Interlocking Safety Verification:", dispatchTab);
        QHBoxLayout *chkLayout = new QHBoxLayout();
        m_chkCatenary = new QCheckBox("Overhead 25kV Catenary Energized", dispatchTab);
        m_chkCatenary->setObjectName("chkCatenary");
        m_chkRetarders = new QCheckBox("Track Retarders Active", dispatchTab);
        m_chkRetarders->setObjectName("chkRetarders");
        m_chkRetarders->setChecked(true);
        chkLayout->addWidget(m_chkCatenary);
        chkLayout->addWidget(m_chkRetarders);
        chkLayout->addStretch();

        m_signalStatus = new QLabel("SIGNAL STATUS: CAUTION / HOLD", dispatchTab);
        m_signalStatus->setObjectName("signalStatusLabel");
        m_signalStatus->setStyleSheet("background-color: #78350f; color: #fde68a; padding: 7px; border-radius: 4px; font-weight: bold;");

        m_alignBtn = new QPushButton("Align Switch Points & Lock Route", dispatchTab);
        m_alignBtn->setObjectName("alignSwitchBtn");
        m_alignBtn->setStyleSheet("background-color: #0284c7;");

        m_routeStatus = new QLabel("Route status: Awaiting alignment command", dispatchTab);
        m_routeStatus->setObjectName("routeStatusLabel");
        m_routeStatus->setStyleSheet("color: #94a3b8; font-style: italic;");

        dispatchLayout->addWidget(dispTitle);
        dispatchLayout->addWidget(trainLabel);
        dispatchLayout->addWidget(m_trainInput);
        dispatchLayout->addWidget(trackLabel);
        dispatchLayout->addWidget(m_comboBox);
        dispatchLayout->addWidget(prioTitle);
        dispatchLayout->addLayout(prioLayout);
        dispatchLayout->addWidget(m_priorityStatus);
        dispatchLayout->addWidget(chkTitle);
        dispatchLayout->addLayout(chkLayout);
        dispatchLayout->addWidget(m_alignBtn);
        dispatchLayout->addWidget(m_signalStatus);
        dispatchLayout->addWidget(m_routeStatus);
        dispatchLayout->addStretch();

        connect(m_alignBtn, &QPushButton::clicked, this, &MockMainWindow::onAlignRouteClicked);

        // ==========================================
        // Tab 3: Shunting, Sliders, SpinBox, Progress, TextEdit
        // ==========================================
        QWidget *controlsTab = new QWidget();
        controlsTab->setObjectName("controlsTab");
        QVBoxLayout *controlsLayout = new QVBoxLayout(controlsTab);
        controlsLayout->setContentsMargins(24, 18, 24, 18);
        controlsLayout->setSpacing(10);

        QLabel *counterTitle = new QLabel("TRAIN DEPARTURE & SHUNTING OPERATIONS", controlsTab);
        counterTitle->setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;");

        QHBoxLayout *cntLayout = new QHBoxLayout();
        m_counterLabel = new QLabel("Clicks: 0", controlsTab);
        m_counterLabel->setObjectName("counterLabel");
        m_counterLabel->setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981; padding: 4px;");
        m_incBtn = new QPushButton("Increment Counter", controlsTab);
        m_incBtn->setObjectName("incrementButton");
        m_incBtn->setStyleSheet("background-color: #059669;");
        cntLayout->addWidget(m_counterLabel);
        cntLayout->addWidget(m_incBtn);
        cntLayout->addStretch();

        // Slider: Hump Speed Control
        m_sliderLabel = new QLabel("Hump Shunting Speed: 25 km/h", controlsTab);
        m_sliderLabel->setObjectName("sliderValLabel");
        m_sliderLabel->setStyleSheet("color: #38bdf8; font-weight: bold;");

        m_speedSlider = new QSlider(Qt::Horizontal, controlsTab);
        m_speedSlider->setObjectName("humpSpeedSlider");
        m_speedSlider->setRange(0, 60);
        m_speedSlider->setValue(25);

        connect(m_speedSlider, &QSlider::valueChanged, this, [this](int v) {
            m_sliderLabel->setText(QString("Hump Shunting Speed: %1 km/h").arg(v));
        });

        // SpinBox: Consist Wagon Count
        QHBoxLayout *spinLayout = new QHBoxLayout();
        QLabel *spinTitle = new QLabel("Consist Wagon Count:", controlsTab);
        m_wagonSpin = new QSpinBox(controlsTab);
        m_wagonSpin->setObjectName("wagonCountSpin");
        m_wagonSpin->setRange(1, 120);
        m_wagonSpin->setValue(18);
        m_wagonLabel = new QLabel("Total Wagons in Cut: 18 cars", controlsTab);
        m_wagonLabel->setObjectName("wagonValLabel");
        m_wagonLabel->setStyleSheet("color: #a7f3d0; font-weight: bold;");
        spinLayout->addWidget(spinTitle);
        spinLayout->addWidget(m_wagonSpin);
        spinLayout->addWidget(m_wagonLabel);
        spinLayout->addStretch();

#if HAS_QT
        connect(m_wagonSpin, static_cast<void(QSpinBox::*)(int)>(&QSpinBox::valueChanged), this, [this](int v) {
            m_wagonLabel->setText(QString("Total Wagons in Cut: %1 cars").arg(v));
        });
#endif

        // Progress Bar: Capacity
        QLabel *capTitle = new QLabel("Yard Track Siding Capacity Utilization:", controlsTab);
        m_capacityBar = new QProgressBar(controlsTab);
        m_capacityBar->setObjectName("yardCapacityBar");
        m_capacityBar->setRange(0, 100);
        m_capacityBar->setValue(68);

        // Train Manifest Text & Button
        QHBoxLayout *manifestLayout = new QHBoxLayout();
        m_myInput = new QLineEdit(controlsTab);
        m_myInput->setObjectName("myInput");
        m_myInput->setPlaceholderText("Enter train manifest details");
        m_myBtn = new QPushButton("Click Me", controlsTab);
        m_myBtn->setObjectName("myButton");
        manifestLayout->addWidget(m_myInput);
        manifestLayout->addWidget(m_myBtn);

        m_myLabel = new QLabel("", controlsTab);
        m_myLabel->setObjectName("myLabel");
        m_myLabel->setStyleSheet("color: #a7f3d0; font-weight: bold;");

        connect(m_myBtn, &QPushButton::clicked, this, [this]() {
            m_myLabel->setText(QString("Hello, %1!").arg(m_myInput->text()));
        });

        // Multi-line TextEdit: Shift Dispatcher Notes
        QLabel *notesTitle = new QLabel("Shift Handover Dispatcher Notes:", controlsTab);
        m_shiftNotes = new QTextEdit(controlsTab);
        m_shiftNotes->setObjectName("shiftNotesEdit");
        m_shiftNotes->setPlaceholderText("Enter shift handover dispatcher notes...");
        m_shiftNotes->setFixedHeight(50);

        QPushButton *emergBtn = new QPushButton("🚨 EMERGENCY YARD ALL-TRACK HALT", controlsTab);
        emergBtn->setObjectName("emergencyHaltBtn");
        emergBtn->setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 9px;");

        m_yardBanner = new QLabel("YARD STATUS: NORMAL OPERATIONS", controlsTab);
        m_yardBanner->setObjectName("yardBannerLabel");
        m_yardBanner->setStyleSheet("color: #34d399; font-weight: bold;");

        controlsLayout->addWidget(counterTitle);
        controlsLayout->addLayout(cntLayout);
        controlsLayout->addWidget(m_sliderLabel);
        controlsLayout->addWidget(m_speedSlider);
        controlsLayout->addLayout(spinLayout);
        controlsLayout->addWidget(capTitle);
        controlsLayout->addWidget(m_capacityBar);
        controlsLayout->addLayout(manifestLayout);
        controlsLayout->addWidget(m_myLabel);
        controlsLayout->addWidget(notesTitle);
        controlsLayout->addWidget(m_shiftNotes);
        controlsLayout->addWidget(emergBtn);
        controlsLayout->addWidget(m_yardBanner);
        controlsLayout->addStretch();

        connect(m_incBtn, &QPushButton::clicked, this, [this]() {
            m_clickCount++;
            m_counterLabel->setText(QString("Clicks: %1").arg(m_clickCount));
        });

        connect(emergBtn, &QPushButton::clicked, this, &MockMainWindow::onEmergencyToggle);

        tabs->addTab(loginTab, "Dispatcher Auth");
        tabs->addTab(dispatchTab, "Route Alignment");
        tabs->addTab(controlsTab, "Yard Operations");

        setCentralWidget(tabs);
    }

private slots:
    void onLinkActivated(const QString &) {
        m_docStatus->setText("Safety Protocol: Reviewed & Interlock Accepted");
        m_docStatus->setStyleSheet("color: #34d399; font-weight: bold; font-size: 12px;");
    }

    void onLoginClicked() {
        QString user = m_usernameInput->text();
        QString pass = m_passwordInput->text();

        if (user == "admin" && pass == "secret123") {
            m_statusLabel->setText("Login Successful!");
            m_statusLabel->setStyleSheet("color: #34d399; font-weight: bold;");
        } else {
            m_statusLabel->setText("Invalid Credentials!");
            m_statusLabel->setStyleSheet("color: #f87171; font-weight: bold;");
        }
    }

    void onAlignRouteClicked() {
        QString train = m_trainInput->text().trimmed();
        if (train.isEmpty()) train = "TRAIN";
        QString track = m_comboBox->currentText().split("-").first().trimmed();
        m_signalStatus->setText(QString("SIGNAL STATUS: CLEAR / GREEN - %1").arg(track.toUpper()));
        m_signalStatus->setStyleSheet("background-color: #065f46; color: #6ee7b7; padding: 7px; border-radius: 4px; font-weight: bold;");
        m_routeStatus->setText(QString("Route locked: %1 aligned to %2").arg(train, track));
        m_routeStatus->setStyleSheet("color: #38bdf8; font-weight: bold;");
    }

    void onEmergencyToggle() {
        m_emergency = !m_emergency;
        if (m_emergency) {
            m_yardBanner->setText("YARD STATUS: EMERGENCY STOP ACTIVE - ALL SIGNALS RED");
            m_yardBanner->setStyleSheet("color: #ef4444; font-weight: bold; background-color: #450a0a; padding: 6px;");
            m_signalStatus->setText("SIGNAL STATUS: EMERGENCY RED - HALT");
            m_signalStatus->setStyleSheet("background-color: #991b1b; color: #fecaca; padding: 7px; border-radius: 4px; font-weight: bold;");
        } else {
            m_yardBanner->setText("YARD STATUS: NORMAL OPERATIONS");
            m_yardBanner->setStyleSheet("color: #34d399; font-weight: bold;");
            m_signalStatus->setText("SIGNAL STATUS: CAUTION / HOLD");
            m_signalStatus->setStyleSheet("background-color: #78350f; color: #fde68a; padding: 7px; border-radius: 4px; font-weight: bold;");
        }
    }

private:
    // Tab 1
    QLineEdit *m_usernameInput;
    QLineEdit *m_passwordInput;
    QCheckBox *m_rememberMeCheck;
    QLabel *m_docLink;
    QLabel *m_docStatus;
    QPushButton *m_loginBtn;
    QLabel *m_statusLabel;

    // Tab 2
    QLineEdit *m_trainInput;
    QComboBox *m_comboBox;
    QRadioButton *m_radioFreight;
    QRadioButton *m_radioExpress;
    QRadioButton *m_radioHazmat;
    QLabel *m_priorityStatus;
    QCheckBox *m_chkCatenary;
    QCheckBox *m_chkRetarders;
    QPushButton *m_alignBtn;
    QLabel *m_signalStatus;
    QLabel *m_routeStatus;

    // Tab 3
    QLabel *m_counterLabel;
    QPushButton *m_incBtn;
    QLabel *m_sliderLabel;
    QSlider *m_speedSlider;
    QSpinBox *m_wagonSpin;
    QLabel *m_wagonLabel;
    QProgressBar *m_capacityBar;
    QLineEdit *m_myInput;
    QPushButton *m_myBtn;
    QLabel *m_myLabel;
    QTextEdit *m_shiftNotes;
    QLabel *m_yardBanner;

    int m_clickCount;
    bool m_emergency;
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    app.setApplicationName("RailwayYardManager");

    MockMainWindow win;
    win.show();

    return app.exec();
}

#if HAS_QT
  #if defined(__has_include)
    #if __has_include("main.moc")
      #include "main.moc"
    #endif
  #else
    #include "main.moc"
  #endif
#endif
