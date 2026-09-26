#include "agent.h"

#if HAS_QT
#include <QApplication>
#include <QCoreApplication>
#include <QTest>
#include <QMetaObject>
#include <QMetaProperty>
#include <QLineEdit>
#include <QLabel>
#include <QTextEdit>
#include <QPlainTextEdit>
#include <QAbstractButton>
#include <QComboBox>
#include <QMouseEvent>
#include <QKeyEvent>
#include <QTabBar>
#include <QCursor>
#include <QTimer>
#include <QThread>
#include <QDebug>
#include <cstdlib>
#include <thread>
#include <chrono>

AgentServer::AgentServer(quint16 port, QObject *parent)
    : QObject(parent), m_server(new QTcpServer(this)), m_port(port),
      m_isRecording(false), m_activeInput(nullptr),
      m_isInspectMode(false), m_hoverTimer(nullptr), m_lastHoveredWidget(nullptr),
      m_rubberBand(nullptr) {
    
    connect(m_server, &QTcpServer::newConnection, this, &AgentServer::onNewConnection);
    
    if (m_server->listen(QHostAddress::AnyIPv4, m_port)) {
        fprintf(stderr, "[QtTestAgent] Server listening on port %d\n", m_port);
        fflush(stderr);
        qDebug() << "[QtTestAgent] Server listening on port" << m_port;
    } else {
        fprintf(stderr, "[QtTestAgent] Failed to listen on port %d: %s\n", m_port, qPrintable(m_server->errorString()));
        fflush(stderr);
        qWarning() << "[QtTestAgent] Failed to listen on port" << m_port << ":" << m_server->errorString();
    }
}

AgentServer::~AgentServer() {
    if (m_server) {
        m_server->close();
    }
}

void AgentServer::onNewConnection() {
    while (m_server->hasPendingConnections()) {
        QTcpSocket *client = m_server->nextPendingConnection();
        m_clients.append(client);
        connect(client, &QTcpSocket::readyRead, this, &AgentServer::onReadyRead);
        connect(client, &QTcpSocket::disconnected, this, &AgentServer::onClientDisconnected);
        qDebug() << "[QtTestAgent] Client connected from" << client->peerAddress().toString();
    }
}

void AgentServer::onClientDisconnected() {
    QTcpSocket *client = qobject_cast<QTcpSocket*>(sender());
    if (client) {
        m_clients.removeAll(client);
        client->deleteLater();
        qDebug() << "[QtTestAgent] Client disconnected";
    }
}

void AgentServer::onReadyRead() {
    QTcpSocket *client = qobject_cast<QTcpSocket*>(sender());
    if (!client) return;

    while (client->canReadLine()) {
        QByteArray line = client->readLine().trimmed();
        if (line.isEmpty()) continue;

        QJsonParseError parseError;
        QJsonDocument doc = QJsonDocument::fromJson(line, &parseError);
        if (parseError.error != QJsonParseError::NoError || !doc.isObject()) {
            QJsonObject errResp;
            errResp["status"] = "error";
            errResp["message"] = QString("JSON Parse Error: %1").arg(parseError.errorString());
            client->write(QJsonDocument(errResp).toJson(QJsonDocument::Compact) + "\n");
            client->flush();
            continue;
        }

        QJsonObject request = doc.object();
        QString reqId = request["id"].toString();

        // Ensure this command executes on the Qt GUI / Main Thread
        QJsonObject response = processCommand(request);
        if (!reqId.isEmpty()) {
            response["id"] = reqId;
        }

        client->write(QJsonDocument(response).toJson(QJsonDocument::Compact) + "\n");
        client->flush();
    }
}

QJsonObject AgentServer::processCommand(const QJsonObject &request) {
    QString action = request["action"].toString();
    QJsonObject target = request["target"].toObject();

    if (action == "ping") {
        return handlePing();
    } else if (action == "click") {
        QString button = request["button"].toString("left");
        int x = request["x"].toInt(-1);
        int y = request["y"].toInt(-1);
        bool dbl = request["double"].toBool(false);
        return handleClick(target, button, x, y, dbl);
    } else if (action == "keyClicks") {
        QString text = request["text"].toString();
        int delay = request["delay"].toInt(-1);
        return handleKeyClicks(target, text, delay);
    } else if (action == "keyPress") {
        QString key = request["key"].toString();
        QString mods = request["modifiers"].toString();
        return handleKeyPress(target, key, mods);
    } else if (action == "clearText") {
        return handleClearText(target);
    } else if (action == "getProperty") {
        QString prop = request.contains("propertyName") ? request["propertyName"].toString() : request["property"].toString();
        return handleGetProperty(target, prop);
    } else if (action == "setProperty") {
        QString prop = request.contains("propertyName") ? request["propertyName"].toString() : request["property"].toString();
        QJsonValue val = request["value"];
        return handleSetProperty(target, prop, val);
    } else if (action == "exists") {
        return handleExists(target);
    } else if (action == "dumpTree") {
        return handleDumpTree(target);
    } else if (action == "selectTab") {
        QString tab = request["tab"].toString();
        return handleSelectTab(target, tab);
    } else if (action == "selectComboItem") {
        QString item = request["item"].toString();
        return handleSelectComboItem(target, item);
    } else if (action == "startRecording") {
        return handleStartRecording();
    } else if (action == "stopRecording") {
        return handleStopRecording();
    } else if (action == "startInspect") {
        return handleStartInspect();
    } else if (action == "stopInspect") {
        return handleStopInspect();
    } else if (action == "getCoverage") {
        return handleGetCoverage();
    }

    QJsonObject err;
    err["status"] = "error";
    err["message"] = QString("Unknown action: %1").arg(action);
    return err;
}

QJsonObject AgentServer::handlePing() {
    QJsonObject res;
    res["status"] = "ok";
    res["app"] = QCoreApplication::applicationName();
    res["pid"] = static_cast<int>(QCoreApplication::applicationPid());
    res["qtVersion"] = QString::fromLatin1(qVersion());
    return res;
}

bool AgentServer::matchesCriteria(QWidget *w, const QJsonObject &criteria) {
    if (!w) return false;

    if (criteria.contains("objectName")) {
        QString expected = criteria["objectName"].toString();
        if (w->objectName() != expected) return false;
    }

    if (criteria.contains("className")) {
        QString expected = criteria["className"].toString();
        if (QString(w->metaObject()->className()) != expected && !w->inherits(expected.toUtf8().constData())) {
            return false;
        }
    }

    if (criteria.contains("text")) {
        QString expected = criteria["text"].toString();
        QString actual = w->property("text").toString();
        if (actual.isEmpty() && w->inherits("QAbstractButton")) {
            actual = qobject_cast<QAbstractButton*>(w)->text();
        }
        if (actual != expected) return false;
    }

    if (criteria.contains("windowTitle")) {
        QString expected = criteria["windowTitle"].toString();
        QWidget *top = w->window();
        if (!top || top->windowTitle() != expected) return false;
    }

    if (criteria.contains("visible")) {
        bool expected = criteria["visible"].toBool();
        if (w->isVisible() != expected) return false;
    }

    if (criteria.contains("enabled")) {
        bool expected = criteria["enabled"].toBool();
        if (w->isEnabled() != expected) return false;
    }

    return true;
}

QWidget* AgentServer::findWidget(const QJsonObject &criteria) {
    if (criteria.isEmpty()) return nullptr;

    const QWidgetList topWidgets = QApplication::topLevelWidgets();
    for (QWidget *top : topWidgets) {
        if (matchesCriteria(top, criteria)) {
            return top;
        }

        const QList<QWidget*> children = top->findChildren<QWidget*>();
        for (QWidget *child : children) {
            if (matchesCriteria(child, criteria)) {
                return child;
            }
        }
    }
    return nullptr;
}

QJsonObject AgentServer::handleClick(const QJsonObject &target, const QString &button, int x, int y, bool isDoubleClick) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }

    ensureWidgetVisible(w);
    m_exercisedWidgets.insert(w);

    Qt::MouseButton btn = Qt::LeftButton;
    if (button.toLower() == "right") btn = Qt::RightButton;
    else if (button.toLower() == "middle") btn = Qt::MiddleButton;

    QPoint pos;
    if (x >= 0 && y >= 0) {
        pos = QPoint(x, y);
    } else if (w->inherits("QCheckBox") || w->inherits("QRadioButton")) {
        pos = QPoint(10, qMax(w->height() / 2, 5));
    } else {
        pos = QPoint(w->width() / 2, w->height() / 2);
    }

    // Bring widget to focus if possible
    w->setFocus();

    if (isDoubleClick) {
        QTest::mouseDClick(w, btn, Qt::NoModifier, pos);
    } else {
        QTest::mouseClick(w, btn, Qt::NoModifier, pos);
    }

#if HAS_QT
    if (QLabel *lbl = qobject_cast<QLabel*>(w)) {
        QString txt = lbl->text();
        int hrefIdx = txt.indexOf("href=\"");
        if (hrefIdx != -1) {
            int start = hrefIdx + 6;
            int end = txt.indexOf("\"", start);
            if (end != -1) {
                QString link = txt.mid(start, end - start);
                QMetaObject::invokeMethod(lbl, "linkActivated", Q_ARG(QString, link));
            }
        }
    }
#endif

    QJsonObject res;
    res["status"] = "ok";
    return res;
}

QJsonObject AgentServer::handleKeyClicks(const QJsonObject &target, const QString &text, int delayMs) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }

    ensureWidgetVisible(w);
    m_exercisedWidgets.insert(w);
    w->setFocus();
    QTest::keyClicks(w, text, Qt::NoModifier, delayMs > 0 ? delayMs : -1);

    QJsonObject res;
    res["status"] = "ok";
    return res;
}

static Qt::Key parseKey(const QString &name) {
    QString n = name.toUpper();
    if (n == "RETURN" || n == "ENTER") return Qt::Key_Return;
    if (n == "TAB") return Qt::Key_Tab;
    if (n == "BACKSPACE") return Qt::Key_Backspace;
    if (n == "ESCAPE" || n == "ESC") return Qt::Key_Escape;
    if (n == "DELETE" || n == "DEL") return Qt::Key_Delete;
    if (n == "SPACE") return Qt::Key_Space;
    if (n == "UP") return Qt::Key_Up;
    if (n == "DOWN") return Qt::Key_Down;
    if (n == "LEFT") return Qt::Key_Left;
    if (n == "RIGHT") return Qt::Key_Right;
    if (n == "HOME") return Qt::Key_Home;
    if (n == "END") return Qt::Key_End;
    if (n == "PAGEUP") return Qt::Key_PageUp;
    if (n == "PAGEDOWN") return Qt::Key_PageDown;
    return Qt::Key_unknown;
}

QJsonObject AgentServer::handleKeyPress(const QJsonObject &target, const QString &keyName, const QString &modifiers) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }

    ensureWidgetVisible(w);
    m_exercisedWidgets.insert(w);
    w->setFocus();
    Qt::KeyboardModifiers mods = Qt::NoModifier;
    if (modifiers.contains("Ctrl", Qt::CaseInsensitive)) mods |= Qt::ControlModifier;
    if (modifiers.contains("Shift", Qt::CaseInsensitive)) mods |= Qt::ShiftModifier;
    if (modifiers.contains("Alt", Qt::CaseInsensitive)) mods |= Qt::AltModifier;

    Qt::Key k = parseKey(keyName);
    if (k == Qt::Key_unknown && keyName.length() == 1) {
        k = static_cast<Qt::Key>(keyName.at(0).toUpper().unicode());
    }

    QTest::keyClick(w, k, mods);

    QJsonObject res;
    res["status"] = "ok";
    return res;
}

QJsonObject AgentServer::handleClearText(const QJsonObject &target) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }

    ensureWidgetVisible(w);
    m_exercisedWidgets.insert(w);

    if (QLineEdit *le = qobject_cast<QLineEdit*>(w)) {
        le->clear();
    } else if (QTextEdit *te = qobject_cast<QTextEdit*>(w)) {
        te->clear();
    } else if (QPlainTextEdit *pte = qobject_cast<QPlainTextEdit*>(w)) {
        pte->clear();
    } else {
        w->setProperty("text", "");
    }

    QJsonObject res;
    res["status"] = "ok";
    return res;
}

QJsonObject AgentServer::handleGetProperty(const QJsonObject &target, const QString &propertyName) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }

    if (propertyName == "text" || propertyName == "plainText") {
        if (QTextEdit *te = qobject_cast<QTextEdit*>(w)) {
            QJsonObject res;
            res["status"] = "ok";
            res["value"] = te->toPlainText();
            return res;
        } else if (QPlainTextEdit *pte = qobject_cast<QPlainTextEdit*>(w)) {
            QJsonObject res;
            res["status"] = "ok";
            res["value"] = pte->toPlainText();
            return res;
        }
    }

    QVariant val = w->property(propertyName.toUtf8().constData());
    if (!val.isValid()) {
        return {{"status", "error"}, {"message", QString("Property '%1' is not valid").arg(propertyName)}};
    }

    QJsonObject res;
    res["status"] = "ok";
    res["value"] = QJsonValue::fromVariant(val);
    return res;
}

QJsonObject AgentServer::handleSetProperty(const QJsonObject &target, const QString &propertyName, const QJsonValue &value) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }

    ensureWidgetVisible(w);
    m_exercisedWidgets.insert(w);

    if (propertyName == "text" || propertyName == "plainText") {
        if (QTextEdit *te = qobject_cast<QTextEdit*>(w)) {
            te->setPlainText(value.toString());
            QJsonObject res;
            res["status"] = "ok";
            return res;
        } else if (QPlainTextEdit *pte = qobject_cast<QPlainTextEdit*>(w)) {
            pte->setPlainText(value.toString());
            QJsonObject res;
            res["status"] = "ok";
            return res;
        }
    }

    bool success = w->setProperty(propertyName.toUtf8().constData(), value.toVariant());
    if (!success) {
        return {{"status", "error"}, {"message", QString("Failed to set property '%1'").arg(propertyName)}};
    }

    QJsonObject res;
    res["status"] = "ok";
    return res;
}

QJsonObject AgentServer::handleExists(const QJsonObject &target) {
    QWidget *w = findWidget(target);
    QJsonObject res;
    res["status"] = "ok";
    res["exists"] = (w != nullptr);
    if (w) {
        res["visible"] = w->isVisible();
        res["enabled"] = w->isEnabled();
    }
    return res;
}

QJsonObject AgentServer::serializeWidget(QWidget *w, bool recursive) {
    QJsonObject node;
    node["className"] = QString(w->metaObject()->className());
    node["objectName"] = w->objectName();
    node["visible"] = w->isVisible();
    node["enabled"] = w->isEnabled();

    // Common properties
    QString text = w->property("text").toString();
    if (!text.isEmpty()) node["text"] = text;

    QJsonObject geom;
    geom["x"] = w->x();
    geom["y"] = w->y();
    geom["width"] = w->width();
    geom["height"] = w->height();
    node["geometry"] = geom;

    if (recursive) {
        QJsonArray childrenArr;
        for (QObject *childObj : w->children()) {
            if (QWidget *childW = qobject_cast<QWidget*>(childObj)) {
                childrenArr.append(serializeWidget(childW, true));
            }
        }
        node["children"] = childrenArr;
    }

    return node;
}

QJsonObject AgentServer::handleDumpTree(const QJsonObject &target) {
    QJsonArray rootArr;
    if (!target.isEmpty()) {
        QWidget *w = findWidget(target);
        if (w) {
            rootArr.append(serializeWidget(w, true));
        }
    } else {
        const QWidgetList topWidgets = QApplication::topLevelWidgets();
        for (QWidget *top : topWidgets) {
            rootArr.append(serializeWidget(top, true));
        }
    }

    QJsonObject res;
    res["status"] = "ok";
    res["tree"] = rootArr;
    return res;
}

void AgentServer::ensureWidgetVisible(QWidget *w) {
    if (!w) return;
    QWidget *curr = w;
    while (curr) {
        QWidget *parent = curr->parentWidget();
        if (parent) {
            QWidget *anc = parent;
            while (anc) {
                if (anc->inherits("QTabWidget")) {
                    QTabWidget *tabWidget = qobject_cast<QTabWidget*>(anc);
                    if (tabWidget) {
                        int idx = tabWidget->indexOf(curr);
                        if (idx >= 0 && tabWidget->currentIndex() != idx) {
                            tabWidget->setCurrentIndex(idx);
                            QApplication::processEvents();
                        }
                    }
                    break;
                }
                anc = anc->parentWidget();
            }
        }
        curr = parent;
    }
}

QJsonObject AgentServer::handleSelectTab(const QJsonObject &target, const QString &tab) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }
    if (!w->inherits("QTabWidget")) {
        return {{"status", "error"}, {"message", "Widget is not a QTabWidget"}};
    }
    QTabWidget *tabWidget = qobject_cast<QTabWidget*>(w);
    if (!tabWidget) {
        return {{"status", "error"}, {"message", "Failed to cast to QTabWidget"}};
    }

    bool ok = false;
    int idx = tab.toInt(&ok);
    if (ok) {
        if (idx >= 0 && idx < tabWidget->count()) {
            tabWidget->setCurrentIndex(idx);
            QApplication::processEvents();
            return {{"status", "ok"}, {"currentIndex", idx}};
        }
        return {{"status", "error"}, {"message", QString("Tab index %1 out of range").arg(idx)}};
    }

    QString tabLower = tab.trimmed().toLower();
    for (int i = 0; i < tabWidget->count(); ++i) {
        QString text = tabWidget->tabText(i).trimmed().toLower();
        if (text == tabLower || text.contains(tabLower)) {
            tabWidget->setCurrentIndex(i);
            QApplication::processEvents();
            return {{"status", "ok"}, {"currentIndex", i}};
        }
    }

    return {{"status", "error"}, {"message", QString("Tab '%1' not found").arg(tab)}};
}

QJsonObject AgentServer::handleSelectComboItem(const QJsonObject &target, const QString &item) {
    QWidget *w = findWidget(target);
    if (!w) {
        return {{"status", "error"}, {"message", "Widget not found"}};
    }
    if (!w->inherits("QComboBox")) {
        return {{"status", "error"}, {"message", "Widget is not a QComboBox"}};
    }
    QComboBox *cb = qobject_cast<QComboBox*>(w);
    if (!cb) {
        return {{"status", "error"}, {"message", "Failed to cast to QComboBox"}};
    }

    ensureWidgetVisible(w);
    m_exercisedWidgets.insert(w);

    bool ok = false;
    int idx = item.toInt(&ok);
    if (ok) {
        if (idx >= 0 && idx < cb->count()) {
            cb->setCurrentIndex(idx);
            QApplication::processEvents();
            return {{"status", "ok"}, {"currentIndex", idx}};
        }
        return {{"status", "error"}, {"message", QString("Combo index %1 out of range").arg(idx)}};
    }

    QString itemLower = item.trimmed().toLower();
    for (int i = 0; i < cb->count(); ++i) {
        QString text = cb->itemText(i).trimmed().toLower();
        if (text == itemLower || text.contains(itemLower)) {
            cb->setCurrentIndex(i);
            QApplication::processEvents();
            return {{"status", "ok"}, {"currentIndex", i}};
        }
    }

    return {{"status", "error"}, {"message", QString("Combo option '%1' not found").arg(item)}};
}

// ==========================================================
// Test Flow Recorder Implementation
// ==========================================================
QString AgentServer::determineLocator(QWidget *w) {
    if (!w) return "unknown";

    if (!w->objectName().isEmpty()) {
        return QString("name=%1").arg(w->objectName());
    }

    if (w->inherits("QAbstractButton")) {
        QString text = w->property("text").toString();
        if (!text.isEmpty()) {
            return QString("type=%1 text='%2'").arg(w->metaObject()->className()).arg(text);
        }
    }

    if (w->inherits("QTabBar")) {
        QTabBar *tb = qobject_cast<QTabBar*>(w);
        if (tb && tb->currentIndex() >= 0) {
            QString tabText = tb->tabText(tb->currentIndex());
            return QString("type=QTabBar text='%1'").arg(tabText);
        }
    }

    return QString("type=%1").arg(w->metaObject()->className());
}

void AgentServer::sendRecordedStep(const QString &keyword, const QString &locator, const QString &arg) {
    QJsonObject step;
    step["type"] = "recordStep";
    step["keyword"] = keyword;
    step["locator"] = locator;
    if (!arg.isEmpty()) {
        step["argument"] = arg;
    }

    QByteArray data = QJsonDocument(step).toJson(QJsonDocument::Compact) + "\n";
    for (QTcpSocket *client : m_clients) {
        client->write(data);
        client->flush();
    }
}

QJsonObject AgentServer::handleStartRecording() {
    m_isRecording = true;
    m_activeInput = nullptr;
    m_initialInputText.clear();

    if (QCoreApplication::instance()) {
        QCoreApplication::instance()->installEventFilter(this);
    }

    qDebug() << "[QtTestAgent] Started recording test flow";
    return {{"status", "ok"}};
}

QJsonObject AgentServer::handleStopRecording() {
    // Flush any active input
    if (m_activeInput) {
        QString currentText = m_activeInput->property("text").toString();
        if (currentText != m_initialInputText) {
            sendRecordedStep("Type Text Into Object", determineLocator(m_activeInput), currentText);
        }
        m_activeInput = nullptr;
    }

    m_isRecording = false;
    if (QCoreApplication::instance()) {
        QCoreApplication::instance()->removeEventFilter(this);
    }

    qDebug() << "[QtTestAgent] Stopped recording test flow";
    return {{"status", "ok"}};
}

// ==========================================================
// Live Inspect on Hover & Pick Object Implementation
// ==========================================================
QJsonObject AgentServer::handleStartInspect() {
    m_isInspectMode = true;
    m_lastHoveredWidget = nullptr;

    if (!m_hoverTimer) {
        m_hoverTimer = new QTimer(this);
        connect(m_hoverTimer, &QTimer::timeout, this, &AgentServer::onHoverTick);
    }
    m_hoverTimer->start(80);

    if (QCoreApplication::instance()) {
        QCoreApplication::instance()->installEventFilter(this);
    }

    qDebug() << "[QtTestAgent] Started live inspect on hover";
    return {{"status", "ok"}};
}

QJsonObject AgentServer::handleStopInspect() {
    m_isInspectMode = false;
    if (m_hoverTimer) {
        m_hoverTimer->stop();
    }
    m_lastHoveredWidget = nullptr;
#if HAS_QT
    if (m_rubberBand) {
        m_rubberBand->hide();
    }
#endif

    if (!m_isRecording && QCoreApplication::instance()) {
        QCoreApplication::instance()->removeEventFilter(this);
    }

    qDebug() << "[QtTestAgent] Stopped inspect mode";
    return {{"status", "ok"}};
}

void AgentServer::onHoverTick() {
    if (!m_isInspectMode) return;

    QPoint globalPos = QCursor::pos();
    QWidget *w = QApplication::widgetAt(globalPos);

#if HAS_QT
    if (w == m_rubberBand) return;
#endif

    if (w && w != m_lastHoveredWidget) {
        m_lastHoveredWidget = w;

#if HAS_QT
        QWidget *topWin = w->window();
        if (topWin) {
            if (!m_rubberBand) {
                m_rubberBand = new QRubberBand(QRubberBand::Rectangle, topWin);
                m_rubberBand->setAttribute(Qt::WA_TransparentForMouseEvents, true);
                m_rubberBand->setStyleSheet("border: 2px solid #38bdf8; background-color: rgba(56, 189, 248, 45);");
            } else if (m_rubberBand->parentWidget() != topWin) {
                m_rubberBand->setParent(topWin);
                m_rubberBand->setAttribute(Qt::WA_TransparentForMouseEvents, true);
                m_rubberBand->setStyleSheet("border: 2px solid #38bdf8; background-color: rgba(56, 189, 248, 45);");
            }

            QPoint posInWin = w->mapTo(topWin, QPoint(0, 0));
            m_rubberBand->setGeometry(QRect(posInWin, w->size()));
            m_rubberBand->show();
            m_rubberBand->raise();
        }
#endif

        QJsonObject info;
        info["type"] = "hoverWidget";
        info["widget"] = serializeWidget(w, false);
        info["locator"] = determineLocator(w);

        QByteArray data = QJsonDocument(info).toJson(QJsonDocument::Compact) + "\n";
        for (QTcpSocket *client : m_clients) {
            client->write(data);
            client->flush();
        }
    } else if (!w) {
        m_lastHoveredWidget = nullptr;
#if HAS_QT
        if (m_rubberBand) {
            m_rubberBand->hide();
        }
#endif
    }
}

bool AgentServer::eventFilter(QObject *watched, QEvent *event) {
    // 1. Pick Object on Mouse Click while in Inspect Mode
    if (m_isInspectMode && event->type() == QEvent::MouseButtonRelease) {
        QMouseEvent *me = static_cast<QMouseEvent*>(event);
        if (me->button() == Qt::LeftButton) {
            QWidget *w = qobject_cast<QWidget*>(watched);
#if HAS_QT
            if (w == m_rubberBand) {
                w = m_lastHoveredWidget;
            }
#endif
            if (w) {
                QJsonObject info;
                info["type"] = "pickWidget";
                info["widget"] = serializeWidget(w, false);
                info["locator"] = determineLocator(w);

                QByteArray data = QJsonDocument(info).toJson(QJsonDocument::Compact) + "\n";
                for (QTcpSocket *client : m_clients) {
                    client->write(data);
                    client->flush();
                }

                // Keep inspect mode active so continuous hovering and inspecting works seamlessly
                return true; // Consume click event during pick
            }
        }
    }

    if (!m_isRecording) {
        return QObject::eventFilter(watched, event);
    }

    QWidget *w = qobject_cast<QWidget*>(watched);
    if (!w) {
        return QObject::eventFilter(watched, event);
    }

    // 1. Mouse Clicks on Buttons, Checkboxes, TabBars, etc.
    if (event->type() == QEvent::MouseButtonRelease) {
        QMouseEvent *me = static_cast<QMouseEvent*>(event);
        if (me->button() == Qt::LeftButton) {
            if (w->inherits("QAbstractButton") || w->inherits("QTabBar") || w->inherits("QComboBox")) {
                // If user was typing in an input before clicking, flush typed text first
                if (m_activeInput && m_activeInput != w) {
                    QString currentText = m_activeInput->property("text").toString();
                    if (currentText != m_initialInputText) {
                        sendRecordedStep("Type Text Into Object", determineLocator(m_activeInput), currentText);
                    }
                    m_activeInput = nullptr;
                }

                QString loc = determineLocator(w);
                sendRecordedStep("Click Object", loc);
            }
        }
    }
    // 2. Track text field focus in
    else if (event->type() == QEvent::FocusIn) {
        if (w->inherits("QLineEdit") || w->inherits("QTextEdit") || w->inherits("QPlainTextEdit")) {
            m_activeInput = w;
            m_initialInputText = w->property("text").toString();
        }
    }
    // 3. Track text field focus out (save text)
    else if (event->type() == QEvent::FocusOut) {
        if (w == m_activeInput) {
            QString currentText = w->property("text").toString();
            if (currentText != m_initialInputText) {
                sendRecordedStep("Type Text Into Object", determineLocator(w), currentText);
            }
            m_activeInput = nullptr;
        }
    }
    // 4. Return / Enter key in text field
    else if (event->type() == QEvent::KeyPress) {
        QKeyEvent *ke = static_cast<QKeyEvent*>(event);
        if ((ke->key() == Qt::Key_Return || ke->key() == Qt::Key_Enter) && m_activeInput) {
            QString currentText = m_activeInput->property("text").toString();
            if (currentText != m_initialInputText) {
                sendRecordedStep("Type Text Into Object", determineLocator(m_activeInput), currentText);
                m_initialInputText = currentText;
            }
        }
    }

    return QObject::eventFilter(watched, event);
}

// ==========================================================
// UI Screen & Component Coverage Implementation
// ==========================================================
bool AgentServer::isInteractiveControl(QWidget *w) {
    if (!w || !w->isVisible()) return false;
    return w->inherits("QAbstractButton") ||
           w->inherits("QLineEdit") ||
           w->inherits("QTextEdit") ||
           w->inherits("QPlainTextEdit") ||
           w->inherits("QComboBox") ||
           w->inherits("QAbstractSpinBox") ||
           w->inherits("QAbstractSlider") ||
           w->inherits("QTabBar");
}

QString AgentServer::getParentScreenName(QWidget *w) {
    QWidget *cur = w;
    while (cur) {
        QWidget *parent = cur->parentWidget();
        if (parent && parent->inherits("QTabWidget")) {
            QTabWidget *tabWidget = qobject_cast<QTabWidget*>(parent);
            int idx = tabWidget->indexOf(cur);
            QString tabTitle = (idx >= 0) ? tabWidget->tabText(idx) : "";
            QString screen = !cur->objectName().isEmpty() ? cur->objectName() : tabTitle;
            return screen.isEmpty() ? "TabScreen" : screen;
        }
        if (cur->isWindow() || cur->inherits("QDialog") || cur->inherits("QMainWindow")) {
            QString winTitle = cur->windowTitle();
            QString name = !cur->objectName().isEmpty() ? cur->objectName() : winTitle;
            return name.isEmpty() ? cur->metaObject()->className() : name;
        }
        cur = parent;
    }
    return "MainScreen";
}

QJsonObject AgentServer::handleGetCoverage() {
    QMap<QString, QList<QWidget*>> screenMap;
    int overallTotal = 0;
    int overallExercised = 0;

    const QWidgetList topWidgets = QApplication::topLevelWidgets();
    for (QWidget *top : topWidgets) {
        if (!top->isVisible()) continue;

        QList<QWidget*> allWidgets;
        if (isInteractiveControl(top)) allWidgets.append(top);
        allWidgets.append(top->findChildren<QWidget*>());

        for (QWidget *w : allWidgets) {
            if (isInteractiveControl(w)) {
                QString screen = getParentScreenName(w);
                if (!screenMap[screen].contains(w)) {
                    screenMap[screen].append(w);
                }
            }
        }
    }

    QJsonArray screensArr;
    for (auto it = screenMap.begin(); it != screenMap.end(); ++it) {
        QString screenName = it.key();
        const QList<QWidget*> &controls = it.value();

        int screenTotal = controls.size();
        int screenExercised = 0;
        QJsonArray exercisedList;
        QJsonArray unexercisedList;

        for (QWidget *w : controls) {
            bool exercised = m_exercisedWidgets.contains(w);
            QJsonObject item;
            item["className"] = QString(w->metaObject()->className());
            item["objectName"] = w->objectName();
            item["locator"] = determineLocator(w);
            QString txt = w->property("text").toString();
            if (!txt.isEmpty()) item["text"] = txt;

            if (exercised) {
                screenExercised++;
                exercisedList.append(item);
            } else {
                unexercisedList.append(item);
            }
        }

        overallTotal += screenTotal;
        overallExercised += screenExercised;

        double screenRate = screenTotal > 0 ? (static_cast<double>(screenExercised) / screenTotal) * 100.0 : 0.0;

        QJsonObject screenObj;
        screenObj["screenName"] = screenName;
        screenObj["total"] = screenTotal;
        screenObj["exercised"] = screenExercised;
        screenObj["coverageRate"] = screenRate;
        screenObj["exercisedControls"] = exercisedList;
        screenObj["unexercisedControls"] = unexercisedList;

        screensArr.append(screenObj);
    }

    double overallRate = overallTotal > 0 ? (static_cast<double>(overallExercised) / overallTotal) * 100.0 : 0.0;

    QJsonObject overall;
    overall["totalControls"] = overallTotal;
    overall["exercisedControls"] = overallExercised;
    overall["coverageRate"] = overallRate;

    QJsonObject res;
    res["status"] = "ok";
    res["overall"] = overall;
    res["screens"] = screensArr;
    return res;
}

// ==========================================================
// Initialization Hook for LD_PRELOAD
// ==========================================================
static void startAgent() {
    quint16 port = 9988;
    const char *portEnv = std::getenv("QT_AGENT_PORT");
    if (portEnv) {
        int p = std::atoi(portEnv);
        if (p > 0 && p < 65536) port = static_cast<quint16>(p);
    }

    fprintf(stderr, "[QtTestAgent] Initializing agent server on port %d...\n", port);
    fflush(stderr);

    // AgentServer will be parented to QCoreApplication::instance()
    new AgentServer(port, QCoreApplication::instance());
}

__attribute__((constructor))
static void initializeLibrary() {
    fprintf(stderr, "[QtTestAgent] Library injected via LD_PRELOAD. Waiting for QCoreApplication...\n");
    fflush(stderr);

    // Spawn a watcher thread to wait until Qt creates the QApplication instance
    std::thread([]() {
        while (!QCoreApplication::instance()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }

        fprintf(stderr, "[QtTestAgent] QCoreApplication detected. Posting startAgent to main thread...\n");
        fflush(stderr);

        // Schedule startAgent() on the Qt Main Thread via QMetaObject::invokeMethod
        QMetaObject::invokeMethod(QCoreApplication::instance(), []() {
            startAgent();
        }, Qt::QueuedConnection);
    }).detach();
}
#endif // HAS_QT

