import unittest
import pandas as pd
from PySide6.QtWidgets import QApplication, QComboBox
from ui_detail import DetailWidget, ALLOWED_METHODS, ALLOWED_CHANNELS
import database


class TestImportTemplateAndValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _next_detail(self, yymm, cat):
        return f"{yymm}{cat}-1"

    def test_plan_release_unassigned_combo(self):
        w = DetailWidget("2601", "MP", "", self._next_detail)
        w.add_row()
        combo = w.table.cellWidget(0, 9)
        self.assertIsInstance(combo, QComboBox)
        self.assertIn("未分配", [combo.itemText(i) for i in range(combo.count())])
        combo.setCurrentText("未分配")
        val = w._display_value(0, 9)
        self.assertEqual(val, "")

    def test_import_with_new_fields(self):
        w = DetailWidget("2601", "MP", "", self._next_detail)
        df = pd.DataFrame([
            {
                "采购标的": "测试物料",
                "规格型号": "型号A",
                "采购数量": "2",
                "单位": "件",
                "单价(元)": "10.5",
                "采购方式": ALLOWED_METHODS[-1],
                "采购途径": ALLOWED_CHANNELS[1],
                "计划发放": "",
                "备注": "中英Mixed备注，符号!@#，换行\n第二行",
            }
        ])
        w._import_from_dataframe(df)
        self.app.processEvents()
        self.assertEqual(w.table.rowCount(), 1)
        self.assertEqual(w.table.item(0, 5).text(), "10.5")
        self.assertEqual(w.table.item(0, 3).text(), "2")
        # total calculated
        self.assertEqual(w.table.item(0, 6).text(), "21.00")
        # remark imported with newline
        self.assertIn("第二行", w.table.item(0, 14).text())

    def test_import_with_recommendation_applied(self):
        # Monkeypatch database recommendation and purchasers
        old_find = getattr(database, "find_recommendation", None)
        old_fetch = getattr(database, "fetch_purchasers", None)
        database.find_recommendation = lambda text: ("张三", "框架协议", "能建商城")
        database.fetch_purchasers = lambda: ["张三", "李胜"]
        try:
            w = DetailWidget("2601", "MP", "", self._next_detail)
            df = pd.DataFrame([
                {
                    "采购标的": "测试物料X",  # will trigger recommendation
                    "规格型号": "型号B",
                    "采购数量": "1",
                    "单位": "个",
                    "单价(元)": "100",
                    "采购方式": "",           # leave empty to apply recommendation
                    "采购途径": "",           # leave empty to apply recommendation
                    "计划发放": "未分配",       # treat as empty and apply recommendation
                }
            ])
            w._import_from_dataframe(df)
            self.app.processEvents()
            # plan release combo
            combo = w.table.cellWidget(0, 9)
            self.assertEqual(combo.currentText(), "张三")
            # method combo
            mcombo = w.table.cellWidget(0, 7)
            self.assertEqual(mcombo.currentText(), "框架协议")
            # channel cell
            self.assertEqual(w.table.item(0, 8).text(), "能建商城")
        finally:
            if old_find:
                database.find_recommendation = old_find
            if old_fetch:
                database.fetch_purchasers = old_fetch

    def test_import_remark_length_limit(self):
        w = DetailWidget("2601", "MP", "", self._next_detail)
        long_text = "A" * 600
        df = pd.DataFrame([
            {
                "采购标的": "物料",
                "规格型号": "X",
                "采购数量": "1",
                "单位": "个",
                "单价(元)": "1",
                "采购方式": ALLOWED_METHODS[1],
                "采购途径": ALLOWED_CHANNELS[1],
                "计划发放": "",
                "备注": long_text,
            }
        ])
        w._import_from_dataframe(df)
        self.app.processEvents()
        self.assertEqual(len(w.table.item(0, 14).text()), 500)


if __name__ == "__main__":
    unittest.main()
