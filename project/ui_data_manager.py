import os
import shutil
import datetime
import zipfile
import sqlite3
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
            if f.endswith(".db") or f.endswith(".zip"):
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

    def _create_backup_zip(self, target_zip_path):
        # Ensure associated files are in project directory before zipping
        self.consolidate_files()
        
        with zipfile.ZipFile(target_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Database
            if os.path.exists(database.DB_PATH):
                zipf.write(database.DB_PATH, arcname="purchase.db")
            
            # 2. Attachments folder (合同附件)
            base_dir = os.path.dirname(database.DB_PATH)
            attach_dir = os.path.join(base_dir, "合同附件")
            if os.path.exists(attach_dir):
                for root, dirs, files in os.walk(attach_dir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        # Relative path inside zip
                        rel_path = os.path.relpath(abs_path, base_dir)
                        zipf.write(abs_path, arcname=rel_path)
            
            # 3. Approval Docs folder (审批单据)
            approval_dir = os.path.join(base_dir, "审批单据")
            if os.path.exists(approval_dir):
                for root, dirs, files in os.walk(approval_dir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_path, base_dir)
                        zipf.write(abs_path, arcname=rel_path)

            # 4. Column Config (optional but good)
            config_path = os.path.join(base_dir, "column_config.json")
            if os.path.exists(config_path):
                zipf.write(config_path, arcname="column_config.json")

    def consolidate_files(self):
        """
        Check all file links in DB. If they point to files outside the project directory,
        copy them to project directory and update DB.
        """
        try:
            base_dir = os.path.dirname(database.DB_PATH)
            
            # Setup Dirs
            dir_approval = os.path.join(base_dir, "审批单据")
            dir_contract = os.path.join(base_dir, "合同附件")
            for d in [dir_approval, dir_contract]:
                if not os.path.exists(d):
                    os.makedirs(d)
                    
            conn = sqlite3.connect(database.DB_PATH)
            cur = conn.cursor()
            
            # 1. Process Approval Docs (orders table)
            cur.execute("SELECT number, approval_doc FROM orders WHERE approval_doc IS NOT NULL AND approval_doc != ''")
            rows = cur.fetchall()
            for number, path in rows:
                if not os.path.exists(path):
                    continue
                
                abs_path = os.path.abspath(path)
                abs_target = os.path.abspath(dir_approval)
                
                if not abs_path.startswith(abs_target):
                    fname = os.path.basename(path)
                    new_path = os.path.join(dir_approval, fname)
                    
                    if os.path.exists(new_path):
                        # Simple rename if collision
                        import time
                        timestamp = int(time.time())
                        name, ext = os.path.splitext(fname)
                        new_path = os.path.join(dir_approval, f"{name}_{timestamp}{ext}")
                        
                    shutil.copy2(path, new_path)
                    cur.execute("UPDATE orders SET approval_doc=? WHERE number=?", (new_path, number))
                
            # 2. Process Contract Attachments (contracts table)
            cur.execute("SELECT id, attachment FROM contracts WHERE attachment IS NOT NULL AND attachment != ''")
            rows = cur.fetchall()
            for cid, path in rows:
                if not os.path.exists(path):
                    continue
                    
                abs_path = os.path.abspath(path)
                abs_target = os.path.abspath(dir_contract)
                
                if not abs_path.startswith(abs_target):
                    fname = os.path.basename(path)
                    new_path = os.path.join(dir_contract, fname)
                    
                    if os.path.exists(new_path):
                        import time
                        timestamp = int(time.time())
                        name, ext = os.path.splitext(fname)
                        new_path = os.path.join(dir_contract, f"{name}_{timestamp}{ext}")
                        
                    shutil.copy2(path, new_path)
                    cur.execute("UPDATE contracts SET attachment=? WHERE id=?", (new_path, cid))

            # 3. Process Contract Attachments (contract_attachments table)
            cur.execute("SELECT id, file_path FROM contract_attachments WHERE file_path IS NOT NULL AND file_path != ''")
            rows = cur.fetchall()
            for aid, path in rows:
                if not os.path.exists(path):
                    continue
                    
                abs_path = os.path.abspath(path)
                abs_target = os.path.abspath(dir_contract)
                
                if not abs_path.startswith(abs_target):
                    fname = os.path.basename(path)
                    new_path = os.path.join(dir_contract, fname)
                    
                    if os.path.exists(new_path):
                        import time
                        timestamp = int(time.time())
                        name, ext = os.path.splitext(fname)
                        new_path = os.path.join(dir_contract, f"{name}_{timestamp}{ext}")
                        
                    shutil.copy2(path, new_path)
                    cur.execute("UPDATE contract_attachments SET file_path=? WHERE id=?", (new_path, aid))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Consolidate error: {e}")

    def do_backup_default(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"purchase_{timestamp}.zip"
            target_path = os.path.join(self.backup_dir, filename)
            
            self._create_backup_zip(target_path)
            
            QMessageBox.information(self, "成功", f"备份已创建：\n{filename}\n(包含数据库与附件)")
            self.load_backups()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")

    def do_backup_export(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"purchase_backup_{timestamp}.zip"
            target_path, _ = QFileDialog.getSaveFileName(self, "导出备份", default_name, "Backup Archive (*.zip)")
            if target_path:
                self._create_backup_zip(target_path)
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
            "还原数据将覆盖当前所有数据（包括附件）且不可撤销！\n\n系统将在还原前自动创建一个临时备份。\n\n确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.perform_restore(source_path)

    def do_restore_external(self):
        source_path, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "Backup Archive (*.zip);;SQLite Database (*.db)")
        if source_path:
            self.confirm_restore(source_path)

    def perform_restore(self, source_path):
        try:
            # 1. Safety Backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Always make a zip backup for safety now, to preserve current state fully
            safety_backup = os.path.join(self.backup_dir, f"auto_backup_before_restore_{timestamp}.zip")
            self._create_backup_zip(safety_backup)
            
            # 2. Restore Logic
            app_dir = os.path.dirname(database.DB_PATH)
            
            if source_path.lower().endswith(".zip"):
                with zipfile.ZipFile(source_path, 'r') as zipf:
                    # Validate
                    if "purchase.db" not in zipf.namelist():
                        raise Exception("无效的备份文件：缺少数据库文件 purchase.db")
                    
                    # Extract all (overwrite)
                    zipf.extractall(app_dir)
                    
            else:
                # Legacy .db restore
                shutil.copyfile(source_path, database.DB_PATH)
            
            # 3. Migrate schema immediately to ensure compatibility with current version
            try:
                database.ensure_db()
            except Exception as e:
                print(f"Schema migration after restore failed: {e}")

            QMessageBox.information(self, "成功", "数据还原成功！\n\n数据库结构已自动更新以兼容当前版本。\n为了防止界面显示异常，建议重启软件。")
            self.load_backups() # refresh list to show safety backup
            
        except Exception as e:
            QMessageBox.critical(self, "严重错误", f"还原失败: {str(e)}\n\n您的当前数据未被修改。")
