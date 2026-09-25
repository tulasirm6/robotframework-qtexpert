#!/usr/bin/env python3
"""
QtExpert Independent Object Spy & UI Inspector GUI.
A standalone visual desktop tool for Linux (and cross-platform) to inspect,
explore, and generate Robot Framework locators for any running Qt application.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, Optional

from robotframework_qtexpert.qt_compat import QtCore, QtWidgets, QtGui, QtTest, QT_BINDING
from robotframework_qtexpert.client import QtAgentClient

if not QtWidgets:
    raise ImportError("No Qt binding (PyQt5, PyQt6, PySide2, PySide6) found to launch Spy GUI.")

# Aliases
QWidget = QtWidgets.QWidget
QMainWindow = QtWidgets.QMainWindow
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QSplitter = QtWidgets.QSplitter
QTreeWidget = QtWidgets.QTreeWidget
QTreeWidgetItem = QtWidgets.QTreeWidgetItem
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QPushButton = QtWidgets.QPushButton
QGroupBox = QtWidgets.QGroupBox
QTextEdit = QtWidgets.QTextEdit
QFileDialog = QtWidgets.QFileDialog
QMessageBox = QtWidgets.QMessageBox
QHeaderView = QtWidgets.QHeaderView
QApplication = QtWidgets.QApplication


class SpyMainWindow(QMainWindow):
    def __init__(self, host="127.0.0.1", port=9988):
        super().__init__()
        self.setWindowTitle("QtExpert Object Spy - Desktop UI Inspector")
        self.setObjectName("qtexpertSpyWindow")
        self.resize(1100, 750)

        self.client: Optional[QtAgentClient] = None
        self.current_tree_data: Dict[str, Any] = {}
        self.selected_node_data: Optional[Dict[str, Any]] = None

        self._apply_dark_theme()
        self._init_ui(host, port)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f19;
                color: #f1f5f9;
            }
            QWidget {
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 14px;
                font-weight: bold;
                background-color: #131b2e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #38bdf8;
            }
            QLineEdit, QTextEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #38bdf8;
            }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 7px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QPushButton#btnSuccess {
                background-color: #059669;
            }
            QPushButton#btnSuccess:hover {
                background-color: #047857;
            }
            QPushButton#btnSecondary {
                background-color: #334155;
            }
            QPushButton#btnSecondary:hover {
                background-color: #475569;
            }
            QTreeWidget, QTableWidget {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                gridline-color: #1e293b;
                selection-background-color: #1e3a8a;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 6px;
                border: 1px solid #0f172a;
                font-weight: bold;
            }
            QSplitter::handle {
                background-color: #1e293b;
                width: 3px;
            }
        """)

    def _init_ui(self, host: str, port: int):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Connection Header Bar
        # -------------------------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        title_lbl = QLabel("🔍 <b>QtExpert Spy</b>")
        title_lbl.setStyleSheet("font-size: 16px; color: #38bdf8;")

        host_lbl = QLabel("Host:")
        self.host_input = QLineEdit(str(host))
        self.host_input.setFixedWidth(110)

        port_lbl = QLabel("Port:")
        self.port_input = QLineEdit(str(port))
        self.port_input.setFixedWidth(70)

        self.connect_btn = QPushButton("Connect & Spy")
        self.connect_btn.setObjectName("btnSuccess")
        self.connect_btn.clicked.connect(self.on_connect_clicked)

        self.refresh_btn = QPushButton("🔄 Refresh Tree")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)

        self.export_btn = QPushButton("💾 Export JSON")
        self.export_btn.setObjectName("btnSecondary")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.on_export_clicked)

        self.status_badge = QLabel("🔴 Disconnected")
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("btnSecondary")
        self.min_btn.setToolTip("Minimize Spy Window")
        self.min_btn.setFixedWidth(36)
        self.min_btn.clicked.connect(self.showMinimized)

        self.max_btn = QPushButton("🗖")
        self.max_btn.setObjectName("btnSecondary")
        self.max_btn.setToolTip("Maximize / Restore Spy Window")
        self.max_btn.setFixedWidth(36)
        self.max_btn.clicked.connect(self.toggle_maximized)

        top_bar.addWidget(title_lbl)
        top_bar.addSpacing(15)
        top_bar.addWidget(host_lbl)
        top_bar.addWidget(self.host_input)
        top_bar.addWidget(port_lbl)
        top_bar.addWidget(self.port_input)
        top_bar.addWidget(self.connect_btn)
        top_bar.addWidget(self.refresh_btn)
        top_bar.addWidget(self.export_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.status_badge)
        top_bar.addSpacing(8)
        top_bar.addWidget(self.min_btn)
        top_bar.addWidget(self.max_btn)

        main_layout.addLayout(top_bar)

        # -------------------------------------------------------------
        # 2. Main Content Splitter (Left: Tree, Right: Inspector & Actions)
        # -------------------------------------------------------------
        splitter = QSplitter(getattr(QtCore.Qt, 'Orientation', QtCore.Qt).Horizontal)

        # Left Container
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Filter input
        filter_bar = QHBoxLayout()
        search_lbl = QLabel("Filter:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter widgets by name, class, or text...")
        self.filter_input.textChanged.connect(self.on_filter_changed)
        filter_bar.addWidget(search_lbl)
        filter_bar.addWidget(self.filter_input)
        left_layout.addLayout(filter_bar)

        # Widget Hierarchy Tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Widget (Class & ObjectName)", "Visible Text / Value", "Geometry"])
        header = self.tree_widget.header()
        if hasattr(header, 'setSectionResizeMode'):
            resize_mode = getattr(QtWidgets.QHeaderView, 'ResizeMode', QtWidgets.QHeaderView)
            header.setSectionResizeMode(0, getattr(resize_mode, 'ResizeToContents', 0))
            header.setSectionResizeMode(1, getattr(resize_mode, 'Stretch', 1))
        self.tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)
        left_layout.addWidget(self.tree_widget)

        splitter.addWidget(left_widget)

        # Right Container
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Locator Box
        loc_box = QGroupBox("Target Robot Framework Locators")
        loc_layout = QVBoxLayout(loc_box)
        loc_layout.setSpacing(6)

        # Best / Primary Locator
        p_row = QHBoxLayout()
        self.primary_loc_input = QLineEdit()
        self.primary_loc_input.setReadOnly(True)
        self.primary_loc_input.setStyleSheet("font-weight: bold; color: #38bdf8;")
        copy_p_btn = QPushButton("Copy")
        copy_p_btn.setFixedWidth(60)
        copy_p_btn.clicked.connect(lambda: self._copy_to_clipboard(self.primary_loc_input.text()))
        p_row.addWidget(QLabel("Primary:"))
        p_row.addWidget(self.primary_loc_input)
        p_row.addWidget(copy_p_btn)
        loc_layout.addLayout(p_row)

        # Alternative Locator
        a_row = QHBoxLayout()
        self.alt_loc_input = QLineEdit()
        self.alt_loc_input.setReadOnly(True)
        copy_a_btn = QPushButton("Copy")
        copy_a_btn.setFixedWidth(60)
        copy_a_btn.clicked.connect(lambda: self._copy_to_clipboard(self.alt_loc_input.text()))
        a_row.addWidget(QLabel("Alt:"))
        a_row.addWidget(self.alt_loc_input)
        a_row.addWidget(copy_a_btn)
        loc_layout.addLayout(a_row)

        right_layout.addWidget(loc_box)

        # Widget Properties Table
        props_box = QGroupBox("Widget Metadata & Qt Properties")
        props_layout = QVBoxLayout(props_box)
        self.props_table = QTableWidget(0, 2)
        self.props_table.setHorizontalHeaderLabels(["Property", "Value"])
        p_header = self.props_table.header() if hasattr(self.props_table, 'header') else self.props_table.horizontalHeader()
        if hasattr(p_header, 'setSectionResizeMode'):
            resize_mode = getattr(QtWidgets.QHeaderView, 'ResizeMode', QtWidgets.QHeaderView)
            p_header.setSectionResizeMode(0, getattr(resize_mode, 'ResizeToContents', 0))
            p_header.setSectionResizeMode(1, getattr(resize_mode, 'Stretch', 1))
        props_layout.addWidget(self.props_table)
        right_layout.addWidget(props_box)

        # Live Action Testing Sandbox
        action_box = QGroupBox("Live Control Action Sandbox (Test in Real-Time)")
        act_layout = QVBoxLayout(action_box)
        act_layout.setSpacing(6)

        btn_row = QHBoxLayout()
        self.click_btn = QPushButton("👆 Click Control")
        self.click_btn.setEnabled(False)
        self.click_btn.clicked.connect(self.on_live_click)

        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Enter text to type...")
        self.type_btn = QPushButton("⌨️ Type Text")
        self.type_btn.setEnabled(False)
        self.type_btn.clicked.connect(self.on_live_type)

        btn_row.addWidget(self.click_btn)
        btn_row.addWidget(self.type_input)
        btn_row.addWidget(self.type_btn)
        act_layout.addLayout(btn_row)

        # Action Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(60)
        self.log_output.setPlaceholderText("Live RPC feedback will appear here...")
        act_layout.addWidget(self.log_output)

        right_layout.addWidget(action_box)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

    # -------------------------------------------------------------
    # Agent Communication & Tree Loading
    # -------------------------------------------------------------
    def on_connect_clicked(self):
        host = self.host_input.text().strip() or "127.0.0.1"
        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Port must be an integer.")
            return

        try:
            self.client = QtAgentClient(host=host, port=port, timeout=4.0)
            self.client.connect(retry_seconds=2.0)
            self.status_badge.setText(f"🟢 Connected ({host}:{port})")
            self.status_badge.setStyleSheet("color: #34d399; font-weight: bold; padding-left: 8px;")
            self.refresh_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self._log_msg(f"Connected to Qt Agent at {host}:{port}")
            self.load_tree()
        except Exception as e:
            self.status_badge.setText("🔴 Disconnected")
            self.status_badge.setStyleSheet("color: #f87171; font-weight: bold; padding-left: 8px;")
            self.refresh_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            QMessageBox.critical(self, "Connection Error", f"Could not connect to Qt Agent at {host}:{port}\n\nError: {e}")

    def on_refresh_clicked(self):
        self.load_tree()

    def load_tree(self):
        if not self.client or not self.client.is_connected():
            return
        try:
            res = self.client.send_command("dumpTree")
            tree_data = res.get("tree", [])
            self.current_tree_data = tree_data
            self._populate_tree(tree_data)
            self._log_msg(f"Tree refreshed: successfully loaded Qt object hierarchy.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to dump tree: {e}")

    def _populate_tree(self, tree_data):
        self.tree_widget.clear()

        # Handle list of top-level widgets or dict
        nodes = tree_data if isinstance(tree_data, list) else [tree_data]
        for node in nodes:
            self._add_tree_node(self.tree_widget, node)

        self.tree_widget.expandAll()

    def _add_tree_node(self, parent_item, node: Dict[str, Any]):
        class_name = node.get("className", "QWidget")
        obj_name = node.get("objectName", "")
        text = str(node.get("text", "")).strip()
        geom = node.get("geometry", {})
        geom_str = f"{geom.get('width', 0)}x{geom.get('height', 0)} @ ({geom.get('x', 0)}, {geom.get('y', 0)})" if geom else ""

        display_name = f"{class_name}"
        if obj_name:
            display_name += f": {obj_name}"

        item = QTreeWidgetItem()
        item.setText(0, display_name)
        item.setText(1, text)
        item.setText(2, geom_str)
        item.setData(0, getattr(QtCore.Qt, 'ItemDataRole', QtCore.Qt).UserRole, node)

        # Visual styling depending on component type
        if "Button" in class_name:
            item.setForeground(0, QtGui.QColor("#38bdf8"))
        elif "Edit" in class_name or "Input" in class_name:
            item.setForeground(0, QtGui.QColor("#a7f3d0"))
        elif "Tab" in class_name:
            item.setForeground(0, QtGui.QColor("#fbcfe8"))
        elif "Box" in class_name:
            item.setForeground(0, QtGui.QColor("#fde68a"))

        if isinstance(parent_item, QTreeWidget):
            parent_item.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        children = node.get("children", [])
        for child in children:
            self._add_tree_node(item, child)

    # -------------------------------------------------------------
    # Selection, Inspection & Locator Synthesis
    # -------------------------------------------------------------
    def on_tree_selection_changed(self):
        selected = self.tree_widget.selectedItems()
        if not selected:
            return

        item = selected[0]
        node = item.data(0, getattr(QtCore.Qt, 'ItemDataRole', QtCore.Qt).UserRole)
        if not node:
            return

        self.selected_node_data = node
        self.click_btn.setEnabled(True)
        self.type_btn.setEnabled(True)

        self._update_locators(node)
        self._update_properties_table(node)

    def _update_locators(self, node: Dict[str, Any]):
        obj_name = node.get("objectName", "")
        class_name = node.get("className", "")
        text = str(node.get("text", "")).strip()

        # Primary Locator
        if obj_name:
            primary = f"name={obj_name}"
        elif text and ("Button" in class_name or "Label" in class_name):
            primary = f'type={class_name} text="{text}"'
        else:
            primary = f"type={class_name}"

        # Alternative Locator
        if obj_name and class_name:
            alt = f"type={class_name} name={obj_name}"
        elif text:
            alt = f'type={class_name} text="{text}"'
        else:
            alt = primary

        self.primary_loc_input.setText(primary)
        self.alt_loc_input.setText(alt)

    def _update_properties_table(self, node: Dict[str, Any]):
        self.props_table.setRowCount(0)
        row = 0

        # Ordered key properties
        keys = ["objectName", "className", "visible", "enabled", "text"]
        for k in keys:
            if k in node:
                self._insert_table_row(row, k, str(node[k]))
                row += 1

        geom = node.get("geometry", {})
        if geom:
            self._insert_table_row(row, "geometry.x", str(geom.get("x", "")))
            row += 1
            self._insert_table_row(row, "geometry.y", str(geom.get("y", "")))
            row += 1
            self._insert_table_row(row, "geometry.width", str(geom.get("width", "")))
            row += 1
            self._insert_table_row(row, "geometry.height", str(geom.get("height", "")))
            row += 1

        # Additional arbitrary properties
        for k, v in node.items():
            if k not in keys and k not in ("geometry", "children"):
                self._insert_table_row(row, k, str(v))
                row += 1

    def _insert_table_row(self, row: int, key: str, value: str):
        self.props_table.insertRow(row)
        k_item = QTableWidgetItem(key)
        v_item = QTableWidgetItem(value)
        k_item.setForeground(QtGui.QColor("#94a3b8"))
        v_item.setForeground(QtGui.QColor("#f8fafc"))
        self.props_table.setItem(row, 0, k_item)
        self.props_table.setItem(row, 1, v_item)

    # -------------------------------------------------------------
    # Live Action Sandbox
    # -------------------------------------------------------------
    def on_live_click(self):
        if not self.selected_node_data:
            return
        target = self._build_target(self.selected_node_data)
        try:
            res = self.client.send_command("click", target=target)
            self._log_msg(f"Clicked {target}: {res.get('status', 'ok')}")
        except Exception as e:
            self._log_msg(f"Click failed: {e}")

    def on_live_type(self):
        if not self.selected_node_data:
            return
        text = self.type_input.text()
        target = self._build_target(self.selected_node_data)
        try:
            self.client.send_command("clearText", target=target)
            res = self.client.send_command("keyClicks", target=target, text=text)
            self._log_msg(f"Typed '{text}' into {target}: {res.get('status', 'ok')}")
        except Exception as e:
            self._log_msg(f"Type failed: {e}")

    def _build_target(self, node: Dict[str, Any]) -> Dict[str, Any]:
        target = {}
        if node.get("objectName"):
            target["objectName"] = node["objectName"]
        elif node.get("className"):
            target["className"] = node["className"]
            if node.get("text"):
                target["text"] = node["text"]
        return target

    def _copy_to_clipboard(self, text: str):
        if not text:
            return
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            self._log_msg(f"Copied to clipboard: {text}")

    def on_filter_changed(self, text: str):
        text_lower = text.strip().lower()
        root = self.tree_widget.invisibleRootItem()
        self._filter_item(root, text_lower)

    def _filter_item(self, item, search_text: str) -> bool:
        if not search_text:
            item.setHidden(False)
            for i in range(item.childCount()):
                self._filter_item(item.child(i), search_text)
            return True

        child_visible = False
        for i in range(item.childCount()):
            if self._filter_item(item.child(i), search_text):
                child_visible = True

        matches = (search_text in item.text(0).lower()) or (search_text in item.text(1).lower())
        visible = matches or child_visible
        item.setHidden(not visible)
        return visible

    def on_export_clicked(self):
        if not self.current_tree_data:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save UI Object Tree", "object_spy.json", "JSON Files (*.json)")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_tree_data, f, indent=2)
            self._log_msg(f"Saved Object Tree to {filename}")

    def _log_msg(self, msg: str):
        self.log_output.append(f"• {msg}")

    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("🗖")
        else:
            self.showMaximized()
            self.max_btn.setText("🗗")

    def mousePressEvent(self, event):
        btn = getattr(QtCore.Qt, 'MouseButton', QtCore.Qt).LeftButton
        if event.button() == btn and event.pos().y() < 65:
            pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self._drag_pos = pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        btn = getattr(QtCore.Qt, 'MouseButton', QtCore.Qt).LeftButton
        if getattr(self, '_drag_pos', None) and (event.buttons() & btn):
            pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self.move(pos - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def main():
    parser = argparse.ArgumentParser(description="QtExpert Standalone UI Object Spy")
    parser.add_argument("--host", default="127.0.0.1", help="Target agent host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9988, help="Target agent port (default: 9988)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("QtExpertSpy")

    win = SpyMainWindow(host=args.host, port=args.port)
    win.show()

    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())


if __name__ == "__main__":
    main()
