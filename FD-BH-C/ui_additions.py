# 这个文件包含要添加到 Ui_bhc.py 的函数
# 运行此脚本将自动追加到 Ui_bhc.py

FUNCTIONS_TO_ADD = '''
    # ==================== 缺失的回调函数 ====================

    def on_direction_clicked(self):
        """切换磁场方向（正/负）"""
        try:
            self.tesla_positive = self.DirectionToggle.isChecked()
            self.DirectionToggle.setText("+" if self.tesla_positive else "-")
            self.update_displays()
        except Exception:
            pass

    def on_power_clicked(self):
        """电源开关"""
        try:
            self.power_on = not self.power_on
            if not self.power_on:
                self.LCD_Current.display("-----")
                self.LCD_Tesla.display("-----")
            else:
                self.update_displays()
        except Exception:
            pass

    def on_probe_slider_changed(self, value):
        """探针滑条变化回调"""
        try:
            # 映射 0..200 -> -15..+15 mm
            self.probe_display_mm = (value - 100) * 0.15
            # 物理有效范围限制在 ±10 mm
            self.probe_physical_mm = max(-10.0, min(10.0, self.probe_display_mm))
            # 更新显示
            self.ProbePosBox.setText(str(int(round(self.probe_display_mm))) + " mm")
            self.update_displays()
        except Exception:
            pass

    def on_toggle_raw_display(self, checked):
        """切换原始/校正磁场显示"""
        try:
            self.debug_show_raw = checked
            self.update_displays()
        except Exception:
            pass

    def on_switch_table(self):
        """切换表格 A/B"""
        try:
            if self._current_table == 'A':
                self._current_table = 'B'
                self.SwitchTableButton.setText("切换到表A")
                # 表B显示更多按钮
                self.AutoMeasureButton.setVisible(True)
                self.ExportPNGButton.setVisible(True)
                self.CalibrateButton.setVisible(True)
                self.RunDegaussButton.setVisible(True)
            else:
                self._current_table = 'A'
                self.SwitchTableButton.setText("切换到表B")
                # 表A隐藏部分按钮
                self.AutoMeasureButton.setVisible(False)
                self.ExportPNGButton.setVisible(False)
                self.CalibrateButton.setVisible(False)
                self.RunDegaussButton.setVisible(False)
            self.refresh_data_table(self._current_table)
            self.statusbar.showMessage("已切换到表" + self._current_table)
        except Exception:
            pass

    def refresh_data_table(self, table):
        """刷新表格显示"""
        try:
            self.DataTable.blockSignals(True)
            rows = self.data_manager.get_table(table)
            if table == 'A':
                # 表A: X/mm, B/mT
                self.DataTable.setColumnCount(2)
                self.DataTable.setHorizontalHeaderLabels(['X/mm', 'B/mT'])
                self.DataTable.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    self.DataTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row.get('X/mm', ''))))
                    b_val = row.get('B/mT', '')
                    if isinstance(b_val, (int, float)):
                        b_val = "%.1f" % b_val
                    self.DataTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(b_val)))
            else:
                # 表B: I/mA, B/mT, H/(A/m), remark
                self.DataTable.setColumnCount(4)
                self.DataTable.setHorizontalHeaderLabels(['I/mA', 'B/mT', 'H/(A/m)', '备注'])
                self.DataTable.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    i_val = row.get('I/mA', '')
                    if isinstance(i_val, (int, float)):
                        i_val = "%.1f" % i_val
                    self.DataTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(i_val)))
                    b_val = row.get('B/mT', '')
                    if isinstance(b_val, (int, float)):
                        b_val = "%.1f" % b_val
                    self.DataTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(b_val)))
                    h_val = row.get('H/A_m', row.get('H/(A/m)', ''))
                    if isinstance(h_val, (int, float)):
                        h_val = "%.0f" % h_val
                    self.DataTable.setItem(i, 2, QtWidgets.QTableWidgetItem(str(h_val)))
                    self.DataTable.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row.get('remark', ''))))
            self.DataTable.blockSignals(False)
        except Exception:
            self.DataTable.blockSignals(False)

    def on_table_item_changed(self, item):
        """表格单元格编辑回调"""
        try:
            row = item.row()
            col = item.column()
            value = item.text()
            table = self._current_table
            rows = self.data_manager.get_table(table)
            if row < len(rows):
                if table == 'A':
                    keys = ['X/mm', 'B/mT']
                else:
                    keys = ['I/mA', 'B/mT', 'H/A_m', 'remark']
                if col < len(keys):
                    try:
                        if keys[col] != 'remark':
                            rows[row][keys[col]] = float(value)
                        else:
                            rows[row][keys[col]] = value
                    except ValueError:
                        rows[row][keys[col]] = value
        except Exception:
            pass

    def on_delete_current_row(self):
        """删除当前选中行"""
        try:
            row = self.DataTable.currentRow()
            if row >= 0:
                reply = QtWidgets.QMessageBox.question(
                    None, "确认删除", "确定要删除第 %d 行吗？" % (row+1),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    self.data_manager.delete_row(self._current_table, row)
                    self.refresh_data_table(self._current_table)
                    self.statusbar.showMessage("已删除第 %d 行" % (row+1))
        except Exception:
            pass

    def on_clear_table(self):
        """清空当前表格"""
        try:
            reply = QtWidgets.QMessageBox.question(
                None, "确认清空", "确定要清空表%s吗？此操作不可撤销！" % self._current_table,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.data_manager.clear_table(self._current_table)
                self.refresh_data_table(self._current_table)
                self.statusbar.showMessage("已清空表" + self._current_table)
        except Exception:
            pass

    def on_auto_measure(self):
        """自动测量（占位）"""
        try:
            self.statusbar.showMessage("自动测量功能开发中...")
        except Exception:
            pass

    def on_export_png(self):
        """导出PNG图像"""
        try:
            if self.plot_widget:
                path, _ = QFileDialog.getSaveFileName(None, "导出PNG", "", "PNG Files (*.png)")
                if path:
                    self.plot_widget.export_png(path)
                    self.statusbar.showMessage("已导出到 " + path)
        except Exception:
            pass

    def on_run_degauss_and_measure(self):
        """退磁并测量（占位）"""
        try:
            self.statusbar.showMessage("退磁并测量功能开发中...")
        except Exception:
            pass

    def check_auto_zero(self):
        """检查自动调零条件（占位）"""
        pass

    def apply_random_field_offset(self, offset_mT):
        """应用随机磁场偏移"""
        try:
            self.ambient_offset_mT = float(offset_mT)
            self.update_displays()
        except Exception:
            pass

    def on_import_csv(self):
        """导入CSV文件"""
        try:
            path, _ = QFileDialog.getOpenFileName(None, "导入CSV", "", "CSV Files (*.csv)")
            if path:
                table, count = self.data_manager.import_csv(path)
                self._current_table = table
                self.refresh_data_table(table)
                self.statusbar.showMessage("已导入 %d 行到表%s" % (count, table))
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "导入失败", "导入CSV失败: " + str(e))

    def on_export_csv(self):
        """导出CSV文件"""
        try:
            path, _ = QFileDialog.getSaveFileName(None, "导出CSV", "", "CSV Files (*.csv)")
            if path:
                count = self.data_manager.export_csv(self._current_table, path)
                self.statusbar.showMessage("已导出 %d 行到 %s" % (count, path))
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "导出失败", "导出CSV失败: " + str(e))

    def on_save_session(self):
        """保存会话"""
        try:
            path, _ = QFileDialog.getSaveFileName(None, "保存会话", "", "JSON Files (*.json)")
            if path:
                self.data_manager.save_session(path)
                self.statusbar.showMessage("会话已保存到 " + path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "保存失败", "保存会话失败: " + str(e))

    def on_load_session(self):
        """加载会话"""
        try:
            path, _ = QFileDialog.getOpenFileName(None, "加载会话", "", "JSON Files (*.json)")
            if path:
                self.data_manager.load_session(path)
                self.refresh_data_table(self._current_table)
                self.statusbar.showMessage("已加载会话 " + path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "加载失败", "加载会话失败: " + str(e))
'''

if __name__ == "__main__":
    # 追加到 Ui_bhc.py
    with open("Ui_bhc.py", "a", encoding="utf-8") as f:
        f.write(FUNCTIONS_TO_ADD)
    print("Functions appended to Ui_bhc.py")
