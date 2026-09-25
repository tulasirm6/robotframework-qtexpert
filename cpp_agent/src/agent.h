#ifndef QT_AGENT_H
#define QT_AGENT_H

#if defined(QT_CORE_LIB) || (defined(__has_include) && (__has_include(<QObject>) || __has_include(<QtCore/QObject>)))
  #define HAS_QT 1
  #if defined(__has_include) && __has_include(<QtCore/QObject>)
    #include <QtCore/QObject>
    #include <QtNetwork/QTcpServer>
    #include <QtNetwork/QTcpSocket>
    #include <QtCore/QJsonObject>
    #include <QtCore/QJsonArray>
    #include <QtCore/QJsonDocument>
    #include <QtWidgets/QWidget>
    #include <QtCore/QSet>
  #else
    #include <QObject>
    #include <QTcpServer>
    #include <QTcpSocket>
    #include <QJsonObject>
    #include <QJsonArray>
    #include <QJsonDocument>
    #include <QWidget>
    #include <QSet>
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

  using quint16 = unsigned short;
  class QEvent {};
  class QObject {
  public:
      QObject(QObject * = nullptr) {}
      virtual ~QObject() = default;
      virtual bool eventFilter(QObject * = nullptr, QEvent * = nullptr) { return false; }
  };
  class QTcpServer : public QObject {
  public:
      QTcpServer(QObject * = nullptr) {}
  };
  class QTcpSocket : public QObject {
  public:
      QTcpSocket(QObject * = nullptr) {}
  };
  class QWidget : public QObject {
  public:
      QWidget(QWidget * = nullptr) {}
  };
  class QTimer : public QObject {};
  class QString {
  public:
      QString(const char * = "") {}
  };
  class QJsonValue {};
  class QJsonObject {};
  class QJsonArray {};
  template<typename T>
  class QList : public std::vector<T> {};
  template<typename T>
  class QSet : public std::vector<T> {};
#endif

class AgentServer : public QObject {
    Q_OBJECT
public:
    explicit AgentServer(quint16 port = 9988, QObject *parent = nullptr);
    virtual ~AgentServer();

public slots:
    void onNewConnection();
    void onReadyRead();
    void onClientDisconnected();

private:
    // Core command dispatcher (runs on Main GUI Thread)
    QJsonObject processCommand(const QJsonObject &request);

    // Command implementations
    QJsonObject handlePing();
    QJsonObject handleClick(const QJsonObject &target, const QString &button, int x, int y, bool isDoubleClick);
    QJsonObject handleKeyClicks(const QJsonObject &target, const QString &text, int delayMs);
    QJsonObject handleKeyPress(const QJsonObject &target, const QString &keyName, const QString &modifiers);
    QJsonObject handleClearText(const QJsonObject &target);
    QJsonObject handleGetProperty(const QJsonObject &target, const QString &propertyName);
    QJsonObject handleSetProperty(const QJsonObject &target, const QString &propertyName, const QJsonValue &value);
    QJsonObject handleExists(const QJsonObject &target);
    QJsonObject handleDumpTree(const QJsonObject &target);
    QJsonObject handleSelectTab(const QJsonObject &target, const QString &tab);
    QJsonObject handleSelectComboItem(const QJsonObject &target, const QString &item);
    void ensureWidgetVisible(QWidget *w);

    // Object resolution
    QWidget* findWidget(const QJsonObject &criteria);
    bool matchesCriteria(QWidget *w, const QJsonObject &criteria);
    QJsonObject serializeWidget(QWidget *w, bool recursive = true);

    // Recording & Event Filter
    bool eventFilter(QObject *watched, QEvent *event) override;
    QJsonObject handleStartRecording();
    QJsonObject handleStopRecording();
    void sendRecordedStep(const QString &keyword, const QString &locator, const QString &arg = "");
    QString determineLocator(QWidget *w);

    // Live Inspect on Hover & Pick Object
    QJsonObject handleStartInspect();
    QJsonObject handleStopInspect();
    void onHoverTick();

    // UI Screen & Component Coverage
    QJsonObject handleGetCoverage();
    bool isInteractiveControl(QWidget *w);
    QString getParentScreenName(QWidget *w);

    QTcpServer *m_server;
    QList<QTcpSocket*> m_clients;
    quint16 m_port;
    bool m_isRecording;
    QWidget *m_activeInput;
    QString m_initialInputText;

    // Inspect members
    bool m_isInspectMode;
    QTimer *m_hoverTimer;
    QWidget *m_lastHoveredWidget;

    // Coverage tracking
    QSet<QWidget*> m_exercisedWidgets;
};

#endif // QT_AGENT_H
