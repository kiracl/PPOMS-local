import json
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, 
    QLineEdit, QComboBox, QSplitter, QFrame, QScrollArea, QMessageBox,
    QTabWidget, QFormLayout, QGroupBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QTextCursor, QFont
import database
import knowledge_base
from datetime import datetime

# --- Worker Thread for LLM Streaming ---
class LLMClient(QThread):
    response_chunk = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, provider, base_url, api_key, model, system_prompt, messages):
        super().__init__()
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.messages = messages

    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct full messages list including system prompt
            full_messages = []
            if self.system_prompt:
                full_messages.append({"role": "system", "content": self.system_prompt})
            full_messages.extend(self.messages)

            # Prepare payload
            payload = {
                "model": self.model,
                "messages": full_messages,
                "stream": True
            }
            
            # Adjust for Ollama (no Bearer token usually needed, but harmless if sent)
            # Adjust endpoint
            endpoint = f"{self.base_url}/chat/completions"
            if self.base_url.endswith("/"):
                endpoint = f"{self.base_url}chat/completions"
            
            response = requests.post(endpoint, headers=headers, json=payload, stream=True, timeout=60)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            if "choices" in data_json and len(data_json["choices"]) > 0:
                                delta = data_json["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    self.response_chunk.emit(content)
                        except json.JSONDecodeError:
                            pass
            
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

# --- Knowledge Base Widget ---
class AiKnowledgeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_docs()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left Panel: Document Management
        left_panel = QGroupBox("📚 知识库文档")
        left_layout = QVBoxLayout(left_panel)
        
        self.table_docs = QTableWidget(0, 4)
        self.table_docs.setHorizontalHeaderLabels(["ID", "文件名", "类型", "上传时间"])
        self.table_docs.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Stretch Filename
        self.table_docs.setSelectionBehavior(QAbstractItemView.SelectRows) # Select Rows
        self.table_docs.setEditTriggers(QAbstractItemView.NoEditTriggers) # No Edit
        left_layout.addWidget(self.table_docs)
        
        btn_box = QHBoxLayout()
        self.btn_add_doc = QPushButton("➕ 添加文档")
        self.btn_add_doc.clicked.connect(self.add_doc)
        self.btn_del_doc = QPushButton("🗑️ 删除文档")
        self.btn_del_doc.clicked.connect(self.del_doc)
        btn_box.addWidget(self.btn_add_doc)
        btn_box.addWidget(self.btn_del_doc)
        left_layout.addLayout(btn_box)
        
        layout.addWidget(left_panel, 1)
        
        # Right Panel: Knowledge Chat
        right_panel = QGroupBox("💡 知识问答")
        right_layout = QVBoxLayout(right_panel)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        right_layout.addWidget(self.chat_history)
        
        input_layout = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(80)
        self.input_text.setPlaceholderText("请输入问题，例如：采购审批流程是怎样的？")
        
        self.btn_ask = QPushButton("提问")
        self.btn_ask.setFixedSize(60, 80)
        self.btn_ask.clicked.connect(self.ask_question)
        
        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.btn_ask)
        right_layout.addLayout(input_layout)
        
        layout.addWidget(right_panel, 1)

    def load_docs(self):
        self.table_docs.setRowCount(0)
        docs = knowledge_base.get_docs()
        for i, row in enumerate(docs):
            # id, filename, doc_type, upload_time, chunk_count
            self.table_docs.insertRow(i)
            self.table_docs.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table_docs.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table_docs.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table_docs.setItem(i, 3, QTableWidgetItem(row[3]))

    def add_doc(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文档", "", "Documents (*.pdf *.docx *.txt *.md)")
        if file_path:
            success, msg = knowledge_base.add_document(file_path)
            if success:
                QMessageBox.information(self, "成功", msg)
                self.load_docs()
            else:
                QMessageBox.warning(self, "失败", msg)

    def del_doc(self):
        row = self.table_docs.currentRow()
        if row < 0:
            return
        doc_id = int(self.table_docs.item(row, 0).text())
        fname = self.table_docs.item(row, 1).text()
        if QMessageBox.question(self, "确认", f"确定删除文档 '{fname}' 吗？") == QMessageBox.Yes:
            knowledge_base.delete_document(doc_id)
            self.load_docs()

    def append_message(self, role, content):
        name = "我" if role == "user" else "AI"
        color = "blue" if role == "user" else "green"
        self.chat_history.append(f"<b style='color:{color}'>{name}:</b> {content}<br>")

    def ask_question(self):
        query = self.input_text.toPlainText().strip()
        if not query:
            return
            
        self.input_text.clear()
        self.append_message("user", query)
        self.btn_ask.setEnabled(False)
        
        # 1. Search Local Knowledge Base
        results = knowledge_base.search_knowledge(query, limit=3)
        
        if not results:
            context = "知识库中未找到相关内容。"
        else:
            context = "参考以下本地文档内容：\n"
            for i, res in enumerate(results):
                context += f"--- 文档: {res['filename']} ---\n{res['content']}\n"

        # 2. Call LLM
        config = database.get_ai_config()
        if not config or not config.get('api_key'):
             # Allow local ollama without key
            if config and "Ollama" in config.get('provider', ''):
                 pass
            else:
                self.append_message("AI", "请先配置 AI API Key。")
                self.btn_ask.setEnabled(True)
                return

        system_prompt = f"""
        你是一个企业知识助手。请根据提供的上下文回答用户问题。
        如果上下文中没有答案，请直接说“知识库中没有相关信息”，不要编造。
        
        上下文：
        {context}
        """
        
        self.worker = LLMClient(
            config.get('provider'),
            config.get('base_url'),
            config.get('api_key'),
            config.get('model_name'),
            system_prompt,
            [{"role": "user", "content": query}]
        )
        self.worker.response_chunk.connect(self.on_response_chunk)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        
        self.current_response = ""
        self.append_message("AI", "正在检索并生成回答...")

    def on_response_chunk(self, chunk):
        self.current_response += chunk
        # Simple update: replace last line? TextEdit makes this hard.
        # Just append final result for now or stream to a buffer?
        # Let's just accumulate and show at the end for simplicity in this widget, 
        # or reuse the logic from ChatWidget if we want streaming.
        # Given the implementation of append_message, streaming updates are tricky without cursor manipulation.
        # Let's just wait for finish for this specific widget to be safe, or try to update.
        pass

    def on_finished(self):
        # Remove "Thinking..." line if possible, or just print result
        self.chat_history.append(f"{self.current_response}<br><hr>")
        self.btn_ask.setEnabled(True)

# --- Config Widget ---
class AiConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_group = QGroupBox("模型连接配置")
        form_layout = QFormLayout(form_group)
        
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["DeepSeek", "Moonshot (Kimi)", "OpenAI", "Ollama (本地)", "自定义"])
        self.combo_provider.currentTextChanged.connect(self.on_provider_changed)
        
        self.edit_base_url = QLineEdit()
        self.edit_base_url.setPlaceholderText("例如: https://api.deepseek.com/v1")
        
        self.edit_api_key = QLineEdit()
        self.edit_api_key.setEchoMode(QLineEdit.Password)
        self.edit_api_key.setPlaceholderText("输入 API Key")
        
        self.edit_model = QLineEdit()
        self.edit_model.setPlaceholderText("例如: deepseek-chat")
        
        self.text_system_prompt = QTextEdit()
        self.text_system_prompt.setPlaceholderText("设置 AI 的人设，例如：你是一个采购数据分析助手...")
        self.text_system_prompt.setMaximumHeight(100)
        
        form_layout.addRow("服务提供商:", self.combo_provider)
        form_layout.addRow("Base URL:", self.edit_base_url)
        form_layout.addRow("API Key:", self.edit_api_key)
        form_layout.addRow("模型名称:", self.edit_model)
        form_layout.addRow("系统提示词:", self.text_system_prompt)
        
        layout.addWidget(form_group)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_save.clicked.connect(self.save_config)
        self.btn_save.setStyleSheet("background-color: #2F80ED; color: white; padding: 8px;")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
        layout.addStretch()

    def on_provider_changed(self, text):
        if text == "DeepSeek":
            self.edit_base_url.setText("https://api.deepseek.com/v1")
            self.edit_model.setText("deepseek-chat")
        elif text == "Moonshot (Kimi)":
            self.edit_base_url.setText("https://api.moonshot.cn/v1")
            self.edit_model.setText("moonshot-v1-8k")
        elif text == "OpenAI":
            self.edit_base_url.setText("https://api.openai.com/v1")
            self.edit_model.setText("gpt-3.5-turbo")
        elif text == "Ollama (本地)":
            self.edit_base_url.setText("http://localhost:11434/v1")
            self.edit_model.setText("deepseek-r1:7b")

    def load_config(self):
        config = database.get_ai_config()
        if config:
            self.combo_provider.setCurrentText(config.get('provider', 'DeepSeek'))
            self.edit_base_url.setText(config.get('base_url', ''))
            self.edit_api_key.setText(config.get('api_key', ''))
            self.edit_model.setText(config.get('model_name', ''))
            self.text_system_prompt.setText(config.get('system_prompt', ''))
        else:
            # Defaults
            self.on_provider_changed("DeepSeek")
            self.text_system_prompt.setText("你是一个专业的采购管理助手，可以协助用户分析采购数据、撰写商务文书和提供决策建议。")

    def save_config(self):
        database.save_ai_config(
            'default',
            self.combo_provider.currentText(),
            self.edit_base_url.text().strip(),
            self.edit_api_key.text().strip(),
            self.edit_model.text().strip(),
            self.text_system_prompt.toPlainText().strip()
        )
        QMessageBox.information(self, "成功", "配置已保存")

# --- Chat Widget ---
class AiChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.messages = [] # List of {"role": "user"|"assistant", "content": "..."}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Chat History Area
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("font-size: 14px; line-height: 1.5;")
        layout.addWidget(self.chat_history, 1)
        
        # Tools / Context Injection Bar
        tools_layout = QHBoxLayout()
        self.btn_feed_plan = QPushButton("📊 投喂月度计划")
        self.btn_feed_plan.clicked.connect(self.feed_monthly_plan)
        
        self.btn_feed_price = QPushButton("💰 投喂价格历史")
        self.btn_feed_price.clicked.connect(self.feed_price_history)

        self.btn_feed_quote = QPushButton("📈 投喂历史报价")
        self.btn_feed_quote.clicked.connect(self.feed_historical_quotes)

        self.btn_feed_purchase = QPushButton("📋 投喂采购计划")
        self.btn_feed_purchase.clicked.connect(self.feed_purchase_plan)

        self.btn_feed_contract = QPushButton("📜 投喂合同数据")
        self.btn_feed_contract.clicked.connect(self.feed_contract_data)

        self.btn_feed_inbound = QPushButton("📦 投喂入库数据")
        self.btn_feed_inbound.clicked.connect(self.feed_inbound_data)

        self.btn_feed_invoice = QPushButton("🧾 投喂发票数据")
        self.btn_feed_invoice.clicked.connect(self.feed_invoice_data)

        self.btn_feed_settlement = QPushButton("💳 投喂结算数据")
        self.btn_feed_settlement.clicked.connect(self.feed_settlement_data)
        
        self.btn_clear = QPushButton("🗑️ 清空对话")
        self.btn_clear.clicked.connect(self.clear_chat)
        
        tools_layout.addWidget(self.btn_feed_plan)
        tools_layout.addWidget(self.btn_feed_price)
        tools_layout.addWidget(self.btn_feed_quote)
        tools_layout.addWidget(self.btn_feed_purchase)
        tools_layout.addWidget(self.btn_feed_contract)
        tools_layout.addWidget(self.btn_feed_inbound)
        tools_layout.addWidget(self.btn_feed_invoice)
        tools_layout.addWidget(self.btn_feed_settlement)
        
        tools_layout.addStretch()
        tools_layout.addWidget(self.btn_clear)
        layout.addLayout(tools_layout)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setPlaceholderText("输入问题，Ctrl+Enter 发送...")
        self.input_text.installEventFilter(self) # For key press handling
        
        self.btn_send = QPushButton("发送")
        self.btn_send.setFixedSize(80, 100)
        self.btn_send.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.btn_send.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.btn_send)
        layout.addLayout(input_layout)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self.input_text and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ControlModifier):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def append_message(self, role, content):
        color = "blue" if role == "user" else "black"
        align = "right" if role == "user" else "left"
        bg_color = "#E3F2FD" if role == "user" else "#F5F5F5"
        
        name = "我" if role == "user" else "AI"
        
        html = f"""
        <div style='margin: 10px; text-align: {align};'>
            <span style='font-weight: bold; color: {color};'>{name}:</span><br>
            <div style='background-color: {bg_color}; padding: 10px; border-radius: 10px; display: inline-block; text-align: left;'>
                {content.replace(chr(10), "<br>")}
            </div>
        </div>
        """
        # Append without adding extra newlines if possible, but QTextEdit handles HTML block logic
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html)
        cursor.insertBlock()
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()

    def send_message(self):
        content = self.input_text.toPlainText().strip()
        if not content:
            return
            
        # UI update
        self.input_text.clear()
        self.append_message("user", content)
        self.messages.append({"role": "user", "content": content})
        
        # Lock UI
        self.btn_send.setEnabled(False)
        self.input_text.setEnabled(False)
        
        # Get config
        config = database.get_ai_config()
        if not config or not config.get('api_key'):
            # Allow local ollama without key
            if config and "Ollama" in config.get('provider', ''):
                pass
            else:
                self.append_message("assistant", "⚠️ 请先在【配置】页设置 API Key 和模型信息。")
                self.btn_send.setEnabled(True)
                self.input_text.setEnabled(True)
                return

        # Prepare streaming UI
        self.current_response = ""
        self.append_message("assistant", "Thinking...")
        
        # Remove "Thinking..." line roughly by manipulating cursor or just appending?
        # Simpler: just append the start of the real message next.
        # Actually, let's create a placeholder block.
        
        self.worker = LLMClient(
            config.get('provider'),
            config.get('base_url'),
            config.get('api_key'),
            config.get('model_name'),
            config.get('system_prompt'),
            self.messages
        )
        self.worker.response_chunk.connect(self.on_response_chunk)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_response_chunk(self, chunk):
        if not self.current_response:
            # First chunk, replace "Thinking..." or just clear last block if we could.
            # For simplicity, we just append to the current block if we can, or just let it be.
            # Let's clean up the "Thinking..." text first if possible.
            # A simple hack: reload the whole text? No, too slow.
            # We will just append the chunk.
            pass
            
        self.current_response += chunk
        
        # Update the last block (AI response)
        # This is tricky with HTML appending. 
        # Easier approach: Use a temporary plain text buffer for the current streaming message?
        # Or: Just delete the last "Thinking..." block and insert the accumulated response.
        
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        # Delete previous char? No.
        # Just insert plain text for now.
        cursor.insertText(chunk)
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()

    def on_finished(self):
        self.messages.append({"role": "assistant", "content": self.current_response})
        self.btn_send.setEnabled(True)
        self.input_text.setEnabled(True)
        # Add a separator
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        self.chat_history.setTextCursor(cursor)

    def on_error(self, err_msg):
        self.append_message("assistant", f"❌ 请求出错: {err_msg}")
        self.btn_send.setEnabled(True)
        self.input_text.setEnabled(True)

    def clear_chat(self):
        self.chat_history.clear()
        self.messages = []

    def feed_monthly_plan(self):
        # Fetch current active plan data
        # For simplicity, fetch the latest 50 items from monthly_plans
        try:
            conn = database._connect()
            cur = conn.cursor()
            cur.execute("SELECT plan_month, department, item_name, spec_model, unit, plan_qty, plan_budget FROM monthly_plans ORDER BY id DESC LIMIT 50")
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "暂无月度计划数据")
                return
                
            csv_text = "月份,部门,名称,规格,单位,数量,预算\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 50 条月度计划数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def feed_price_history(self):
        # Ask user for item name
        from PySide6.QtWidgets import QInputDialog
        item, ok = QInputDialog.getText(self, "投喂价格历史", "请输入物品名称:")
        if ok and item:
            try:
                # Reuse fetch logic if available, or raw sql
                conn = database._connect()
                cur = conn.cursor()
                cur.execute("SELECT item_name, spec_model, audit_price, supplier, quote_date FROM historical_quotes WHERE item_name LIKE ? ORDER BY quote_date DESC LIMIT 20", (f"%{item}%",))
                rows = cur.fetchall()
                conn.close()
                
                if not rows:
                    QMessageBox.information(self, "提示", f"未找到 '{item}' 的历史价格")
                    return
                    
                csv_text = "物品,规格,审核价,供应商,日期\n"
                for r in rows:
                    csv_text += ",".join([str(x) for x in r]) + "\n"
                    
                msg = f"已投喂 '{item}' 的历史价格数据:\n```csv\n{csv_text}\n```\n请分析该物品的价格趋势。"
                self.input_text.setText(msg)
            except Exception as e:
                QMessageBox.warning(self, "错误", str(e))

    def feed_purchase_plan(self):
        try:
            conn = database._connect()
            cur = conn.cursor()
            # orders table schema: 
            # id, date, order_no, model, quantity, price, total, sales_order, production_order, purchase_request, status, remarks, spec_id
            # Wait, let's check ui_contract.py again. 
            # Line 1373: 0:id, 1:date, 2:no, 3:model, 4:qty, 5:price, 6:total, 7:sales, 8:prod, 9:purch, 10:status, 11:remark, 12:spec_id
            # The query "SELECT yymm, category, unit, date, task_name, number FROM orders" is definitely wrong.
            # Based on ui_contract.py, table is contract_orders? No, ui_contract.py handles contract_orders.
            # But the user said "Purchase Plan". In this system, "Purchase Plan" usually refers to "monthly_plans".
            # The previous tool call fixed feed_monthly_plan.
            # The user asked for "Purchase Plan" button AGAIN? Or maybe "Order Execution"?
            # Let's assume "Purchase Plan" -> "monthly_plans" (which is already implemented as feed_monthly_plan).
            # But wait, the user added "feed_purchase_plan" button separately.
            # If "Purchase Plan" means "monthly_plans", then feed_monthly_plan is enough.
            # If "Purchase Plan" means "contract_orders" (Execution Orders), then let's query contract_orders.
            # However, looking at the error report context, the user might be referring to "Purchase Plan" as "monthly_plans" but the code used "orders".
            # Actually, "orders" table does NOT exist in the provided database.py schema snippet!
            # The snippet shows "contract_orders", "inbound_orders".
            # Let's assume the user wants "Contract Execution Orders" (contract_orders) for "Purchase Plan"? 
            # OR, maybe the user actually wants "monthly_plans" but I added a DUPLICATE button with WRONG SQL?
            # Let's check the button text: "📋 投喂采购计划".
            # The previous button was "📊 投喂月度计划" (feed_monthly_plan).
            # "采购计划" often implies "monthly_plans".
            # If so, they are the same.
            # BUT, if the user means "Contract Orders" (Execution), let's query `contract_orders`.
            # Let's check `contract_orders` schema in database.py or by inference.
            # database.py snippet:
            # contract_orders: id, contract_id, spec_id, order_no, quantity, status
            # Let's try to query `contract_orders` joined with `contracts` and `contract_specs` to get meaningful data.
            
            # RE-READING INTENT: "投喂采购计划数据" -> Maybe "Contract Orders"?
            # Let's use `contract_orders` for now.
            
            cur.execute("""
                SELECT 
                    co.order_no, c.contract_number, c.supplier, cs.spec_model, co.quantity, co.status, co.created_at
                FROM contract_orders co
                LEFT JOIN contracts c ON co.contract_id = c.id
                LEFT JOIN contract_specs cs ON co.spec_id = cs.id
                ORDER BY co.id DESC LIMIT 50
            """)
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "暂无采购订单数据")
                return
                
            csv_text = "订单号,合同号,供应商,规格型号,数量,状态,创建时间\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 50 条采购订单数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def feed_contract_data(self):
        try:
            conn = database._connect()
            cur = conn.cursor()
            # contracts table: id, contract_number, name, category, supplier, sign_date, end_date, amount, status, ...
            # My previous query: SELECT contract_no, name, supplier, amount, signing_date, status FROM contracts
            # Column mapping: contract_no -> contract_number, signing_date -> sign_date
            cur.execute("SELECT contract_number, name, supplier, amount, sign_date, status FROM contracts ORDER BY id DESC LIMIT 50")
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "暂无合同数据")
                return
                
            csv_text = "合同号,名称,供应商,金额,签订日期,状态\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 50 条合同数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def feed_inbound_data(self):
        try:
            conn = database._connect()
            cur = conn.cursor()
            cur.execute("SELECT inbound_no, contract_no, order_no, spec_model, inbound_qty, inbound_date, operator FROM inbound_orders ORDER BY id DESC LIMIT 50")
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "暂无入库数据")
                return
                
            csv_text = "入库单号,合同号,订单号,规格型号,入库数量,入库日期,操作人\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 50 条入库数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def feed_invoice_data(self):
        try:
            conn = database._connect()
            cur = conn.cursor()
            cur.execute("SELECT invoice_code, invoice_number, date, seller_name, total_amount, status FROM invoices ORDER BY id DESC LIMIT 50")
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "暂无发票数据")
                return
                
            csv_text = "发票代码,发票号码,日期,销售方,总金额,状态\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 50 条发票数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def feed_settlement_data(self):
        try:
            conn = database._connect()
            cur = conn.cursor()
            cur.execute("SELECT reconciliation_no, supplier, status, total_amount, created_at FROM reconciliations ORDER BY id DESC LIMIT 50")
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "暂无结算数据")
                return
                
            csv_text = "对账单号,供应商,状态,总金额,创建时间\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 50 条结算数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def feed_historical_quotes(self):
        # Directly fetch all historical quotes (limit to reasonable amount to avoid token overflow)
        # Let's say latest 200 records
        try:
            conn = database._connect()
            cur = conn.cursor()
            cur.execute("SELECT item_name, spec_model, audit_price, supplier, quote_date FROM historical_quotes ORDER BY quote_date DESC LIMIT 200")
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "历史报价库为空")
                return
                
            csv_text = "物品,规格,报价,供应商,日期\n"
            for r in rows:
                csv_text += ",".join([str(x) for x in r]) + "\n"
                
            msg = f"已投喂最近 200 条历史报价数据:\n```csv\n{csv_text}\n```\n请基于以上数据进行分析。"
            self.input_text.setText(msg)
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

# --- Data Analysis Widget (Text-to-SQL) ---
class AiAnalysisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Query Input Area
        input_group = QGroupBox("智能查询")
        input_layout = QVBoxLayout(input_group)
        
        self.input_query = QTextEdit()
        self.input_query.setPlaceholderText("请输入您的查询需求，例如：\n- 统计上个月各供应商的合同总金额\n- 查一下‘螺纹钢’最近5次的采购价格\n- 列出所有未完成对账的供应商")
        self.input_query.setMaximumHeight(80)
        
        btn_layout = QHBoxLayout()
        self.btn_execute = QPushButton("执行查询")
        self.btn_execute.setStyleSheet("background-color: #2F80ED; color: white; padding: 8px 16px; font-weight: bold;")
        self.btn_execute.clicked.connect(self.execute_analysis)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_execute)
        
        input_layout.addWidget(self.input_query)
        input_layout.addLayout(btn_layout)
        layout.addWidget(input_group)
        
        # 2. Results Area
        result_group = QGroupBox("分析结果")
        result_layout = QVBoxLayout(result_group)
        
        # SQL Preview (Collapsible or small)
        self.lbl_sql = QLabel("生成的 SQL: (暂无)")
        self.lbl_sql.setStyleSheet("color: gray; font-family: Consolas;")
        self.lbl_sql.setWordWrap(True)
        result_layout.addWidget(self.lbl_sql)
        
        # Table Result
        self.table_result = QTableWidget()
        result_layout.addWidget(self.table_result)
        
        # Text Summary
        self.text_summary = QTextEdit()
        self.text_summary.setReadOnly(True)
        self.text_summary.setMaximumHeight(100)
        self.text_summary.setPlaceholderText("AI 分析总结将显示在这里...")
        result_layout.addWidget(self.text_summary)
        
        layout.addWidget(result_group)

    def execute_analysis(self):
        query = self.input_query.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入查询内容")
            return
            
        self.btn_execute.setEnabled(False)
        self.table_result.clear()
        self.table_result.setRowCount(0)
        self.table_result.setColumnCount(0)
        self.lbl_sql.setText("正在思考并生成 SQL...")
        self.text_summary.setText("正在分析数据...")
        
        # Get config
        config = database.get_ai_config()
        if not config or not config.get('api_key'):
            # Allow local ollama without key
            if config and "Ollama" in config.get('provider', ''):
                pass
            else:
                QMessageBox.warning(self, "配置缺失", "请先在【配置】页设置 API Key")
                self.btn_execute.setEnabled(True)
                return

        # Start Worker
        self.worker = SqlGenWorker(config, query)
        self.worker.sql_generated.connect(self.on_sql_generated)
        self.worker.data_fetched.connect(self.on_data_fetched)
        self.worker.analysis_finished.connect(self.on_analysis_finished)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_sql_generated(self, sql):
        self.lbl_sql.setText(f"执行 SQL: {sql}")

    def on_data_fetched(self, headers, rows):
        if not headers:
            self.table_result.setColumnCount(1)
            self.table_result.setHorizontalHeaderLabels(["结果"])
            self.table_result.setRowCount(1)
            self.table_result.setItem(0, 0, QTableWidgetItem("无数据"))
            return

        self.table_result.setColumnCount(len(headers))
        self.table_result.setHorizontalHeaderLabels(headers)
        self.table_result.setRowCount(len(rows))
        
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table_result.setItem(r, c, QTableWidgetItem(str(val)))
        
        self.table_result.resizeColumnsToContents()

    def on_analysis_finished(self, summary):
        self.text_summary.setText(summary)
        self.btn_execute.setEnabled(True)

    def on_error(self, msg):
        QMessageBox.critical(self, "错误", msg)
        self.btn_execute.setEnabled(True)
        self.lbl_sql.setText("SQL 生成失败")
        self.text_summary.clear()

class SqlGenWorker(QThread):
    sql_generated = Signal(str)
    data_fetched = Signal(list, list)
    analysis_finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, config, user_query):
        super().__init__()
        self.config = config
        self.user_query = user_query
        # Database Schema Context
        self.schema_context = """
        Table: contracts (id, contract_number, name, supplier, sign_date, amount, status)
        Table: contract_orders (id, contract_id, order_no, quantity, status, created_at)
        Table: monthly_plans (id, plan_month, department, item_name, spec_model, plan_qty, plan_budget)
        Table: inbound_orders (id, inbound_no, supplier, inbound_date)
        Table: invoices (id, invoice_no, supplier, total_amount, status)
        Table: reconciliations (id, reconciliation_no, supplier, total_amount, status)
        Table: historical_quotes (id, item_name, spec_model, audit_price, supplier, quote_date)
        """

    def run(self):
        try:
            # Step 1: Text-to-SQL
            system_prompt = f"""
            You are a SQLite expert. Given the following database schema, write a SQL query to answer the user's question.
            Schema:
            {self.schema_context}
            
            Rules:
            1. Return ONLY the SQL query. No markdown, no explanation.
            2. Use LIKE for fuzzy matching names.
            3. Use 'now' or date() for current date relative queries if needed.
            4. If the question cannot be answered by the schema, select 'SELECT "Cannot answer"' as a string.
            5. IMPORTANT: For table `monthly_plans`, the column `plan_month` stores values like "2601", "2602". If user asks for "2602计划周" or "2602月", match `plan_month = '2602'`.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.user_query}
            ]
            
            sql = self.call_llm(messages, stream=False).strip().replace("```sql", "").replace("```", "").strip()
            self.sql_generated.emit(sql)
            
            if "Cannot answer" in sql:
                self.error_occurred.emit("无法根据现有数据回答该问题")
                return

            # Step 2: Execute SQL
            conn = database._connect()
            cur = conn.cursor()
            try:
                cur.execute(sql)
                headers = [description[0] for description in cur.description]
                rows = cur.fetchall()
            except Exception as e:
                conn.close()
                self.error_occurred.emit(f"SQL 执行错误: {e}")
                return
            conn.close()
            
            self.data_fetched.emit(headers, rows)
            
            # Step 3: Summarize Results (if rows exist)
            if rows:
                # Limit rows for summary context to avoid token overflow
                data_preview = str(headers) + "\n"
                for r in rows[:10]:
                    data_preview += str(r) + "\n"
                
                summary_prompt = f"""
                User Question: {self.user_query}
                SQL Result (first 10 rows):
                {data_preview}
                
                Please provide a concise summary of these results in Chinese.
                """
                
                summary_msgs = [
                    {"role": "system", "content": "You are a helpful data analyst."},
                    {"role": "user", "content": summary_prompt}
                ]
                summary = self.call_llm(summary_msgs, stream=False)
                self.analysis_finished.emit(summary)
            else:
                self.analysis_finished.emit("未查询到相关数据。")

        except Exception as e:
            self.error_occurred.emit(str(e))

    def call_llm(self, messages, stream=False):
        headers = {
            "Authorization": f"Bearer {self.config.get('api_key')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.get('model_name'),
            "messages": messages,
            "stream": False
        }
        endpoint = f"{self.config.get('base_url')}/chat/completions"
        if self.config.get('base_url').endswith("/"):
            endpoint = f"{self.config.get('base_url')}chat/completions"
            
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# --- Main Module ---
class AiAssistantModule(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.chat_tab = AiChatWidget()
        self.analysis_tab = AiAnalysisWidget()
        self.knowledge_tab = AiKnowledgeWidget()
        self.config_tab = AiConfigWidget()
        
        self.tabs.addTab(self.chat_tab, "🤖 智能对话")
        self.tabs.addTab(self.analysis_tab, "📊 数据分析")
        self.tabs.addTab(self.knowledge_tab, "📚 知识库")
        self.tabs.addTab(self.config_tab, "⚙️ 模型配置")
        
        layout.addWidget(self.tabs)
