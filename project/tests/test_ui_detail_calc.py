import unittest
import time
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt
from ui_detail import DetailWidget


class TestUIDetailCalc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _next_detail(self, yymm, cat):
        return f"{yymm}{cat}-1"

    def test_realtime_update(self):
        w = DetailWidget("2601", "MP", "", self._next_detail)
        w.add_row()
        r = 0
        w.table.setItem(r, 3, w.table.item(r, 3) or QTableWidgetItem(""))
        w.table.setItem(r, 5, w.table.item(r, 5) or QTableWidgetItem(""))
        w.table.item(r, 3).setText("4")
        w.table.item(r, 5).setText("12.5")
        self.app.processEvents()
        it = w.table.item(r, 6)
        self.assertIsNotNone(it)
        self.assertEqual(it.text(), "50.00")
        self.assertFalse(bool(it.flags() & Qt.ItemIsEditable))

    def test_batch_compute(self):
        w = DetailWidget("2601", "MP", "", self._next_detail)
        for _ in range(50):
            w.add_row()
        t0 = time.perf_counter()
        for r in range(w.table.rowCount()):
            w.table.setItem(r, 3, w.table.item(r, 3) or QTableWidgetItem(""))
            w.table.setItem(r, 5, w.table.item(r, 5) or QTableWidgetItem(""))
            w.table.item(r, 3).setText("2")
            w.table.item(r, 5).setText("3")
        self.app.processEvents()
        t1 = time.perf_counter()
        self.assertLess((t1 - t0) * 1000, 1000)


if __name__ == "__main__":
    unittest.main()
