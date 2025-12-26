import os
import shutil
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QFileDialog, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt
import database

class DataManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.backup_dir = os.path.join(database._app_dir(), "backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        self.setup_ui()
        self.load_backups()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Section 1: Backup
        backup_group = QFrame()
        backup_group.setStyleSheet(".QFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; }")
        backup_layout = QVBoxLayout(backup_group)
        
        title_backup = QLabel("数据备份")
        title_backup.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
        backup_layout.addWidget(title_backup)
        
        desc_backup = QLabel("建议定期备份数据，以防止意外丢失。默认备份文件保存在程序目录下的 backups 文件夹中。")
        desc_backup.setStyleSheet("color: #6B7280; margin-bottom: 10px;")
        desc_backup.setWordWrap(True)
        backup_layout.addWidget(desc_backup)
        
        btn_layout = QHBoxLayout()
        self.btn_backup_now = QPushButton("立即备份")
        self.btn_backup_now.setMinimumHeight(40)
        self.btn_backup_now.setStyleSheet("""
            QPushButton { background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold; padding: 0 20px; }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        self.btn_backup_now.clicked.connect(self.do_backup_default)
        
        self.btn_backup_export = QPushButton("导出备份...")
        self.btn_backup_export.setMinimumHeight(40)
        self.btn_backup_export.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #374151; border: 1px solid #D1D5DB; border-radius: 6px; padding: 0 20px; }
            QPushButton:hover { background-color: #F3F4F6; }
        """)
        self.btn_backup_export.clicked.connect(self.do_backup_export)
        
        btn_layout.addWidget(self.btn_backup_now)
        btn_layout.addWidget(self.btn_backup_export)
        btn_layout.addStretch()
        backup_layout.addLayout(btn_layout)
        
        layout.addWidget(backup_group)
        
        # Section 2: Restore / History
        restore_group = QFrame()
        restore_group.setStyleSheet(".QFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; }")
        restore_layout = QVBoxLayout(restore_group)
        
        title_restore = QLabel("备份历史与恢复")
        title_restore.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
        restore_layout.addWidget(title_restore)
        
        warn_layout = QHBoxLayout()
        warn_icon = QLabel("⚠️")
        warn_msg = QLabel("注意：恢复数据将覆盖当前所有记录，请谨慎操作。")
        warn_msg.setStyleSheet("color: #DC2626; font-weight: bold;")
        warn_layout.addWidget(warn_icon)
        warn_layout.addWidget(warn_msg)
        warn_layout.addStretch()
        restore_layout.addLayout(warn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["备份文件名", "备份时间", "文件大小", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E5E7EB; border-radius: 4px; }
            QHeaderView::section { background-color: #F9FAFB; padding: 8px; border: none; border-bottom: 1px solid #E5E7EB; font-weight: bold; color: #374151; }
        """)
        restore_layout.addWidget(self.table)
        
        # Bottom tools
        bottom_layout = QHBoxLayout()
        self.btn_restore_file = QPushButton("从外部文件恢复...")
        self.btn_restore_file.setStyleSheet("""
            QPushButton { color: #2563EB; border: none; font-weight: bold; text-align: left; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_restore_file.setCursor(Qt.PointingHandCursor)
        self.btn_restore_file.clicked.connect(self.do_restore_external)
        
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_refresh.clicked.connect(self.load_backups)
        
        bottom_layout.addWidget(self.btn_restore_file)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_refresh)
        restore_layout.addLayout(bottom_layout)
        
        layout.addWidget(restore_group)
        layout.addStretch()

    def load_backups(self):
        self.table.setRowCount(0)
        if not os.path.exists(self.backup_dir):
            return
            
        files = []
        for f in os.listdir(self.backup_dir):
            if f.endswith(".db"):
                path = os.path.join(self.backup_dir, f)
                stat = os.stat(path)
                files.append({
                    "name": f,
                    "path": path,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size
                })
        
        # Sort by time desc
        files.sort(key=lambda x: x["mtime"], reverse=True)
        
        self.table.setRowCount(len(files))
        for r, info in enumerate(files):
            # Name
            self.table.setItem(r, 0, QTableWidgetItem(info["name"]))
            
            # Time
            dt = datetime.datetime.fromtimestamp(info["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
            self.table.setItem(r, 1, QTableWidgetItem(dt))
            
            # Size
            size_kb = info["size"] / 1024
            self.table.setItem(r, 2, QTableWidgetItem(f"{size_kb:.1f} KB"))
            
            # Actions
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(4, 2, 4, 2)
            h.setSpacing(8)
            
            btn_restore = QPushButton("还原")
            btn_restore.setStyleSheet("background-color: #10B981; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_restore.setCursor(Qt.PointingHandCursor)
            btn_restore.clicked.connect(lambda checked, p=info["path"]: self.confirm_restore(p))
            
            btn_del = QPushButton("删除")
            btn_del.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(lambda checked, p=info["path"]: self.delete_backup(p))
            
            h.addWidget(btn_restore)
            h.addWidget(btn_del)
            self.table.setCellWidget(r, 3, w)

    def do_backup_default(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"purchase_{timestamp}.db"
            target_path = os.path.join(self.backup_dir, filename)
            
            shutil.copyfile(database.DB_PATH, target_path)
            QMessageBox.information(self, "成功", f"备份已创建：\n{filename}")
            self.load_backups()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")

    def do_backup_export(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"purchase_backup_{timestamp}.db"
            target_path, _ = QFileDialog.getSaveFileName(self, "导出备份", default_name, "SQLite Database (*.db)")
            if target_path:
                shutil.copyfile(database.DB_PATH, target_path)
                QMessageBox.information(self, "成功", "备份导出成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def delete_backup(self, path):
        if QMessageBox.question(self, "确认", "确定要删除此备份文件吗？") == QMessageBox.Yes:
            try:
                os.remove(path)
                self.load_backups()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def confirm_restore(self, source_path):
        reply = QMessageBox.warning(
            self, 
            "危险操作", 
            "还原数据将覆盖当前所有数据且不可撤销！\n\n系统将在还原前自动创建一个临时备份。\n\n确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.perform_restore(source_path)

    def do_restore_external(self):
        source_path, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "SQLite Database (*.db)")
        if source_path:
            self.confirm_restore(source_path)

    def perform_restore(self, source_path):
        try:
            # 1. Safety Backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = os.path.join(self.backup_dir, f"auto_backup_before_restore_{timestamp}.db")
            shutil.copyfile(database.DB_PATH, safety_backup)
            
            # 2. Restore (Copy source to DB_PATH)
            # We assume no other process is locking the DB.
            # In a real heavy app we might need to close connections first, but here connections are short-lived per function.
            shutil.copyfile(source_path, database.DB_PATH)
            
            QMessageBox.information(self, "成功", "数据还原成功！\n\n为了确保数据正常加载，请重启软件。")
            self.load_backups() # refresh list to show safety backup
            
        except Exception as e:
            QMessageBox.critical(self, "严重错误", f"还原失败: {str(e)}\n\n您的当前数据未被修改。")
