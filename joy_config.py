import sys
import json
import pygame
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                             QAbstractItemView, QMessageBox, QFrame, QHeaderView)
from PyQt6.QtCore import QTimer, Qt

class ListenDialog(QDialog):
    def __init__(self, action_name, joysticks, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self.detected_combo = []
        self.deadzone = 0.6

        self.initial_axes = {}
        for joy in joysticks.values():
            axes = []
            for i in range(joy.get_numaxes()):
                axes.append(joy.get_axis(i))
            self.initial_axes[joy.get_instance_id()] = axes

        self.setWindowTitle("Assign Input")
        self.setFixedSize(350, 180)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.title_label = QLabel(f"Assigning: <b style='color:#89b4fa;'>{self.action_name}</b>")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.title_label)

        self.info_label = QLabel("Press a button, move a stick,\nor use the D-pad...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        pygame.event.clear()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_events)
        self.timer.start(30)

        self.recording_timer = QTimer(self)
        self.recording_timer.setSingleShot(True)
        self.recording_timer.timeout.connect(self.finish_recording)

    def poll_events(self):
        for event in pygame.event.get():
            event_detected = None
            if event.type == pygame.JOYBUTTONDOWN:
                event_detected = {"type": "button", "index": event.button}
            elif event.type == pygame.JOYAXISMOTION:
                inst_id = getattr(event, 'instance_id', getattr(event, 'joy', 0))
                initial_val = 0
                if inst_id in self.initial_axes and event.axis < len(self.initial_axes[inst_id]):
                    initial_val = self.initial_axes[inst_id][event.axis]
                if abs(event.value - initial_val) > 0.5 and abs(event.value) > self.deadzone:
                    direction = 1 if event.value > 0 else -1
                    event_detected = {"type": "axis", "index": event.axis, "dir": direction}
            elif event.type == pygame.JOYHATMOTION:
                if event.value != (0, 0):
                    event_detected = {"type": "hat", "index": event.hat, "dir": list(event.value)}

            if event_detected and event_detected not in self.detected_combo:
                self.detected_combo.append(event_detected)
                self.info_label.setText("Recording combo...\n(Press additional keys or wait)")
                if not self.recording_timer.isActive():
                    self.recording_timer.start(800) 

    def finish_recording(self):
        if self.detected_combo:
            self.accept()

    def accept(self):
        self.timer.stop()
        self.recording_timer.stop()
        super().accept()

    def reject(self):
        self.timer.stop()
        self.recording_timer.stop()
        super().reject()

class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

class JoystickConfigurator(QDialog):
    def __init__(self):
        super().__init__()
        pygame.init()
        pygame.joystick.init()
        self.joysticks = {}

        self.actions = ["LEFT", "RIGHT", "ROTATE", "HARD_DROP", "SOFT_DROP"]
        self.joy_map = {action: [] for action in self.actions}

        self.init_ui()
        self.load_existing_config()
        self.refresh_devices()

    def init_ui(self):
        self.setWindowTitle("Controller Configuration") 
        self.resize(700, 600)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        actions_card = CardFrame()
        actions_layout = QVBoxLayout(actions_card)
        
        user_label = QLabel("Configured Actions")
        user_label.setObjectName("HeaderLabel")
        actions_layout.addWidget(user_label)

        self.action_table = QTableWidget(len(self.actions), 2)
        self.action_table.setHorizontalHeaderLabels(["Action", "Assigned Inputs"])
        self.action_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.action_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.action_table.verticalHeader().setVisible(False)
        self.action_table.horizontalHeader().setStretchLastSection(True)
        self.action_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.action_table.setShowGrid(False)
        self.action_table.setAlternatingRowColors(True)
        
        for i, action in enumerate(self.actions):
            act_item = QTableWidgetItem(action)
            act_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            val_item = QTableWidgetItem("")
            val_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.action_table.setItem(i, 0, act_item)
            self.action_table.setItem(i, 1, val_item)
            
        actions_layout.addWidget(self.action_table)

        action_btn_layout = QHBoxLayout()
        action_btn_layout.addStretch()
        
        self.assign_btn = QPushButton("Assign Selected")
        self.assign_btn.setMinimumWidth(150)
        self.assign_btn.clicked.connect(self.assign_input)
        action_btn_layout.addWidget(self.assign_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumWidth(100)
        self.clear_btn.setObjectName("SecondaryButton")
        self.clear_btn.clicked.connect(self.clear_input)
        action_btn_layout.addWidget(self.clear_btn)
        
        actions_layout.addLayout(action_btn_layout)
        main_layout.addWidget(actions_card)

        devices_card = CardFrame()
        devices_layout = QVBoxLayout(devices_card)

        sys_label = QLabel("Detected Controllers")
        sys_label.setObjectName("HeaderLabel")
        devices_layout.addWidget(sys_label)

        self.device_table = QTableWidget(0, 2)
        self.device_table.setHorizontalHeaderLabels(["ID", "Device Name"])
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.horizontalHeader().setStretchLastSection(True)
        self.device_table.setShowGrid(False)
        self.device_table.setAlternatingRowColors(True)
        self.device_table.setFixedHeight(120)
        devices_layout.addWidget(self.device_table)

        dev_btn_layout = QHBoxLayout()
        dev_btn_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.setMinimumWidth(150)
        self.refresh_btn.setObjectName("SecondaryButton")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        dev_btn_layout.addWidget(self.refresh_btn)
        
        devices_layout.addLayout(dev_btn_layout)
        main_layout.addWidget(devices_card)

        main_btn_layout = QHBoxLayout()
        main_btn_layout.addStretch()
        
        self.ok_btn = QPushButton("Save & Close")
        self.ok_btn.setMinimumWidth(150)
        self.ok_btn.clicked.connect(self.save_and_close)
        main_btn_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setObjectName("SecondaryButton")
        self.cancel_btn.clicked.connect(self.reject)
        main_btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(main_btn_layout)
        self.setLayout(main_layout)

    def format_single_input(self, cfg):
        if cfg["type"] == "button":
            return f"Btn {cfg['index']}"
        elif cfg["type"] == "axis":
            return f"Ax {cfg['index']} ({'+' if cfg['dir'] > 0 else '-'})"
        elif cfg["type"] == "hat":
            return f"Hat {cfg['index']} {cfg['dir']}"
        return "Unknown"

    def format_combo(self, combo):
        return " + ".join([self.format_single_input(cfg) for cfg in combo])

    def format_input_str(self, config_list):
        return " | ".join([self.format_combo(combo) for combo in config_list])

    def load_existing_config(self):
        try:
            import os
            if os.path.exists("joy_map.json"):
                with open("joy_map.json", "r") as f:
                    loaded_map = json.load(f)
                    
                for action, cfg in loaded_map.items():
                    if action in self.actions:
                        normalized_combos = []
                        if isinstance(cfg, dict):
                            normalized_combos = [[cfg]]
                        elif isinstance(cfg, list):
                            for item in cfg:
                                if isinstance(item, dict):
                                    normalized_combos.append([item])
                                elif isinstance(item, list):
                                    normalized_combos.append(item)
                        self.joy_map[action] = normalized_combos
                        
                self.update_table_displays()
        except Exception:
            pass

    def update_table_displays(self):
        for i in range(self.action_table.rowCount()):
            action = self.action_table.item(i, 0).text()
            if action in self.joy_map and self.joy_map[action]:
                display_str = self.format_input_str(self.joy_map[action])
                self.action_table.item(i, 1).setText(display_str)
            else:
                self.action_table.item(i, 1).setText("")

    def refresh_devices(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        
        count = pygame.joystick.get_count()
        self.device_table.setRowCount(count)
        self.joysticks.clear()
        
        for i in range(count):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self.joysticks[i] = joy
            
            id_item = QTableWidgetItem(str(i))
            id_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            name_item = QTableWidgetItem(joy.get_name())
            name_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            
            self.device_table.setItem(i, 0, id_item)
            self.device_table.setItem(i, 1, name_item)

    def assign_input(self):
        current_row = self.action_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select an action from the list first.")
            return
            
        if pygame.joystick.get_count() == 0:
            QMessageBox.critical(self, "No Controller", "No controllers detected. Please plug one in and refresh.")
            return

        action_name = self.action_table.item(current_row, 0).text()
        
        dialog = ListenDialog(action_name, self.joysticks, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.detected_combo:
            if action_name not in self.joy_map:
                self.joy_map[action_name] = []
                
            if dialog.detected_combo not in self.joy_map[action_name]:
                self.joy_map[action_name].append(dialog.detected_combo)
                
            self.update_table_displays()

    def clear_input(self):
        current_row = self.action_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select an action to clear.")
            return
            
        action_name = self.action_table.item(current_row, 0).text()
        combos = self.joy_map.get(action_name, [])

        if not combos:
            return

        if len(combos) == 1:
            self.joy_map[action_name] = []
            self.update_table_displays()
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Clear Input")
        dialog.setFixedSize(300, 150 + len(combos) * 45)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel(f"Remove input for <b style='color:#89b4fa;'>{action_name}</b>:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        for i, combo in enumerate(combos):
            btn_text = self.format_combo(combo)
            btn = QPushButton(f"Delete {btn_text}")
            btn.clicked.connect(lambda checked, idx=i, d=dialog: self.remove_specific_input(action_name, idx, d))
            layout.addWidget(btn)

        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(lambda checked, d=dialog: self.clear_all_inputs(action_name, d))
        layout.addWidget(clear_all_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def remove_specific_input(self, action_name, idx, dialog):
        if 0 <= idx < len(self.joy_map[action_name]):
            self.joy_map[action_name].pop(idx)
            self.update_table_displays()
        dialog.accept()

    def clear_all_inputs(self, action_name, dialog):
        self.joy_map[action_name] = []
        self.update_table_displays()
        dialog.accept()

    def save_and_close(self):
        try:
            with open("joy_map.json", "w") as f:
                json.dump(self.joy_map, f, indent=4)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

STYLESHEET = """
QWidget {
    background-color: #11111b;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}
QFrame#Card {
    background-color: #1e1e2e;
    border-radius: 8px;
    border: 1px solid #313244;
}
QLabel#HeaderLabel {
    font-size: 16px;
    font-weight: bold;
    color: #89b4fa;
    margin-bottom: 5px;
    background: transparent;
}
QTableWidget {
    background-color: #181825;
    alternate-background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 5px;
    outline: none;
}
QTableWidget::item {
    padding: 8px;
}
QTableWidget::item:selected {
    background-color: #313244;
    color: #89b4fa;
    font-weight: bold;
}
QHeaderView::section {
    background-color: #11111b;
    color: #a6adc8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #313244;
    font-weight: bold;
}
QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
    border-radius: 4px;
    padding: 10px 20px;
    border: none;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:pressed {
    background-color: #74c7ec;
}
QPushButton#SecondaryButton {
    background-color: #313244;
    color: #cdd6f4;
    font-weight: normal;
}
QPushButton#SecondaryButton:hover {
    background-color: #45475a;
}
QMessageBox {
    background-color: #1e1e2e;
}
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = JoystickConfigurator()
    window.show()
    sys.exit(app.exec())