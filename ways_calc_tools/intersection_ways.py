"""
/***************************************************************************
 WaysCalc
                                 A QGIS plugin
 ways calculator
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-02-25
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Zlatanov Evgeniy
        email                : johnzet@yandex.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QObject, QVariant
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import (QAction, QTableWidgetItem, QListWidget,
                                 QListWidgetItem, QDialogButtonBox, QApplication)
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes, QgsRectangle,
    QgsMapLayerProxyModel,
    QgsGeometry,
    QgsFeatureRequest,
    QgsExpression,
    QgsTask,
    QgsApplication,
    QgsMessageLog,
    Qgis
)
from qgis.gui import (
        QgsMapToolEmitPoint,
        QgsHighlight
)
# Initialize Qt resources from file resources.py

# Import the code for the DockWidget
from ..ways_calc_select_layers_dialog import WaysCalcSelectLayerDialog
from ..ways_calc_click_res_dialog import WaysCalcClickResDialog
from .infrastructure import CommonTools

import json
import os
from collections import OrderedDict

class IntersectionWays:
    def __init__(self, iface, dockWidget):
        print("__init__")
        self.iface = iface
        self.dockWidget = dockWidget
        self.plugin_dir = os.path.dirname(__file__)

        self.map_clicked_dlg = WaysCalcClickResDialog()
        self.sel_layer_dlg = WaysCalcSelectLayerDialog()
        self.buttonOk = self.map_clicked_dlg.button_box.button( QDialogButtonBox.Ok )
        self.filter_layout = self.map_clicked_dlg.groupBox_filter.layout()

        self.inters_layer = None # слой сравнения
        self.current_layer = None # текущий выбранный слой
        self.current_layer_selected_fs = None # объекты, которые попали под курсор на карте (лист словарей)

        self.settings = None
        self.settings_layer = None

        #highlights
        self.mapclicked_h_list = []
        self.intersected_h_list = []
        self.intersection_h_list = []

        self.exclude_idx_copyresult = [1,2] # исключить поля при копировании результатов

        self.MESSAGE_CATEGORY = "IntersectionWays"

        self.onLoadModule()


    def onLoadModule(self):
        self.map_clicked_dlg.tableClickedWays.itemSelectionChanged.connect(self.onMapClickedTableSelChanged)
        self.dockWidget.tableResult.itemSelectionChanged.connect(self.onResultTableSelChanged)
        self.dockWidget.visibilityChanged.connect(self.onDockVisibilityChanged)
        self.map_clicked_dlg.pushButton_reset.clicked.connect(self.resetClickedWaysFilters)
        self.dockWidget.copyButton.clicked.connect(self.copyResult)
        self.initSettings()


    def onUnLoadModule(self):
        self.map_clicked_dlg.tableClickedWays.itemSelectionChanged.disconnect(self.onMapClickedTableSelChanged)
        self.dockWidget.tableResult.itemSelectionChanged.disconnect(self.onResultTableSelChanged)        
        self.dockWidget.visibilityChanged.disconnect(self.onDockVisibilityChanged)
        self.map_clicked_dlg.pushButton_reset.clicked.disconnect(self.resetClickedWaysFilters)
        self.dockWidget.copyButton.clicked.disconnect(self.copyResult)
        
        self.clearAllHighlights()


    def copyResult(self):
        CommonTools.copyResult(self.dockWidget, self.exclude_idx_copyresult)


    def initSettings(self):
        with open(os.path.join(self.plugin_dir, "..\settings.json"), "r") as read_file:
            self.settings = json.load(read_file)


    def resetClickedWaysFilters(self):
        self.clearFiltersDlg() # очистить форму от фильтров
        self.addFiltersDlg() # добавить фильтры на форму


    def onDockVisibilityChanged(self):
        try:
            ltw = self.iface.layerTreeView()
            ltw.refreshLayerSymbology(self.inters_layer.id())
        except:
            pass
        if self.dockWidget.isHidden():
            self.clearAllHighlights()
            self.setFilterLayer(self.inters_layer)
            self.current_layer.removeSelection()


    def onResultTableSelChanged(self):
        cur_row_index = self.dockWidget.tableResult.currentRow()
        if cur_row_index > -1:
            self.clearHighlight(self.intersected_h_list)
            self.clearHighlight(self.intersection_h_list)

            f_geometry = QgsGeometry()
            f_geometry = QgsGeometry.fromWkt(
                    self.dockWidget.tableResult.item(cur_row_index, 1).text())
            h = QgsHighlight(self.iface.mapCanvas(), f_geometry, self.inters_layer)
            h.setColor(QColor(26, 200, 0, 220))
            h.setWidth(6)
            h.setFillColor(QColor(26, 200, 0, 150))
            self.intersected_h_list.append(h)

            if_geometry = QgsGeometry()
            if_geometry = QgsGeometry.fromWkt(
                    self.dockWidget.tableResult.item(cur_row_index, 2).text())
            ih = QgsHighlight(self.iface.mapCanvas(), if_geometry, self.inters_layer)
            ih.setColor(QColor(230,0,0,220))
            ih.setWidth(6)
            ih.setFillColor(QColor(230,0,0,150))
            self.intersection_h_list.append(ih)


    def onMapClickedTableSelChanged(self):
        cur_row_index = self.map_clicked_dlg.tableClickedWays.currentRow()
        if cur_row_index > -1:
            self.clearAllHighlights()

            f_geometry = QgsGeometry()
            f_geometry = QgsGeometry.fromWkt(
                    self.map_clicked_dlg.tableClickedWays.item(cur_row_index, 1).text())

            h = QgsHighlight(self.iface.mapCanvas(), f_geometry, self.current_layer)
            h.setColor(QColor(0, 15, 183, 220))
            h.setWidth(6)
            h.setFillColor(QColor(0, 15, 183, 150))
            self.mapclicked_h_list.append(h)

        self.setButtonOkStatus()


    def setButtonOkStatus(self):
        if self.map_clicked_dlg.tableClickedWays.currentRow() > -1:
            self.buttonOk.setEnabled(True)
        else:
            self.buttonOk.setEnabled(False)


    def clearAllHighlights(self):
        self.clearHighlight(self.mapclicked_h_list)
        self.clearHighlight(self.intersected_h_list)
        self.clearHighlight(self.intersection_h_list)


    def clearHighlight(self, highlight_list):
        for i, h in enumerate(highlight_list):
            highlight_list.pop(i)
            self.iface.mapCanvas().scene().removeItem(h)


    def __del__(self):
        print('deleted')


    def initLayerWays(self, current_layer = None):
        self.sel_layer_dlg.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)
        if current_layer is not None:
            if current_layer.geometryType() ==  QgsWkbTypes.LineGeometry:
                self.sel_layer_dlg.mMapLayerComboBox.setLayer(current_layer)
        self.sel_layer_dlg.show()
        result = self.sel_layer_dlg.exec_()
        if result:
            self.inters_layer = self.sel_layer_dlg.mMapLayerComboBox.currentLayer()
            self.settings_layer = self.settings["modules"]["intersection_ways"]["layers"].get(
                    self.inters_layer.name(), self.settings["modules"]["intersection_ways"]["layers"].get("*")
                    )
            self.clearFiltersDlg() # очистить форму от фильтров
            self.addFiltersDlg() # добавить фильтры на форму


    def checkLayers(self):
        current_layer = self.iface.activeLayer()
        if (current_layer is not None and
                type(current_layer) == QgsVectorLayer and
                current_layer.geometryType() ==  QgsWkbTypes.LineGeometry):
            self.current_layer = current_layer
        else:
            self.iface.messageBar().pushMessage(f'Выберите векторный линейный слой, содержащий объект сравнения', f'', duration=5, level=2)
            return False

        try:
            self.inters_layer.id()
        except:
            self.initLayerWays(current_layer)

        if self.current_layer is None or self.inters_layer is None:
            return False
        return True
    
    
    def insersection_take_way(self, point):
        self.current_layer.removeSelection()
        width = self.iface.mapCanvas().mapUnitsPerPixel() * 5
        rect = QgsRectangle(point.x() - width,
            point.y() - width,
            point.x() + width,
            point.y() + width)
        self.current_layer.selectByRect(rect)

        if self.current_layer.selectedFeatureCount() > 0:
            # self.iface.messageBar().clearWidgets()
            self.showClickedFeaturesList()


    def showClickedFeaturesList(self):
        self.populateComboByLayers()

        table = self.map_clicked_dlg.tableClickedWays
        table.reset()
        self.current_layer_selected_fs = []
        self.current_layer_selected_fs = CommonTools.populateTableByClickedFeatures(
                                                self.current_layer, table)

        self.current_layer.removeSelection()

        self.setButtonOkStatus()
        self.map_clicked_dlg.setWindowFlags(
                                self.map_clicked_dlg.windowFlags() |
                                Qt.WindowStaysOnTopHint |
                                Qt.WindowMinMaxButtonsHint)
        self.map_clicked_dlg.show()
        result = self.map_clicked_dlg.exec_()
        if result:
            self.createTaskCalcIntersects()
        else:
            self.clearAllHighlights()


    def createTaskCalcIntersects(self):
        taskManager = QgsApplication.taskManager()
        self.task1 = QgsTask.fromFunction(
            'IntersectionWays', self.calcIntersects, on_finished=self.completed)
        taskManager.addTask(self.task1)


    def completed(self, exception, result=None):
        if result:
            self.populateTableResult(self.dockWidget.tableResult, result)

            QgsMessageLog.logMessage(
                    'Task completed',
                    self.MESSAGE_CATEGORY, Qgis.Info)
            self.dockWidget.show()
        else:
            QgsMessageLog.logMessage(
                    'Completed with no exception and no result ' \
                    '(probably the task was manually canceled by the user)',
                    self.MESSAGE_CATEGORY, Qgis.Warning)


    def stopped(self, task):
        QgsMessageLog.logMessage(
            'Task "{name}" was cancelled'.format(name=task.description()),
            self.MESSAGE_CATEGORY, Qgis.Info)


    def clearFiltersDlg(self):
        CommonTools.clearFiltersLayout(self.filter_layout)


    def addFiltersDlg(self):
        if self.settings["modules"].get("intersection_ways") is not None:
            if self.settings_layer is not None:
                ava_filters_fields = self.settings_layer.get("filters_fields")
                if ava_filters_fields is not None:
                    for field in ava_filters_fields:
                        CommonTools.addFilter(
                            field,
                            self.inters_layer,
                            self.filter_layout,
                            self.settings_layer)


    def populateComboByLayers(self):
        widget= CommonTools.findWidgetByName(self.filter_layout, "_by_addition_layer")
        if widget:
            widget.clear()
            widget.addItem(None, QVariant(None))

            addlayers = self.getAdditionalLayerData()
            if addlayers:
                for laydata in addlayers:
                    layer = laydata["layer"]
                    widget.addItem(layer.name(), QVariant(layer))
                widget.setCurrentIndex(-1)
                widget.setEnabled(True)
            else:
                widget.setEnabled(False)


    def calcIntersects(self, task):
        try:
            QgsMessageLog.logMessage('Started task {}'.format(task.description()),
                                    self.MESSAGE_CATEGORY, Qgis.Info)

            self.setFilterLayer(self.inters_layer)

            filters_dict = {}
            if self.settings_layer is not None:
                for fieldname in self.settings_layer.get("filters_fields"):
                    filters_dict[fieldname] = CommonTools.getFilterValues(fieldname, self.filter_layout)

            current_feature_idx = self.map_clicked_dlg.tableClickedWays.currentRow()
            current_feature_id = int(self.map_clicked_dlg.tableClickedWays.item(current_feature_idx, 0).text())
            current_feature = self.current_layer.getFeature(current_feature_id)
            current_feature_geom = current_feature.geometry()
            current_feature_length = round(current_feature_geom.length(), 2)
            percent_inters = int(filters_dict.get("_percent", "0"))
            buffer_size = float(filters_dict.get("_buffer_size", "0.01"))
            layer_by_percent = (filters_dict.get("_by_addition_layer")) # слой, по пересечению объектов которых будет высчитываться процент пересечения
            current_feature_buf = current_feature_geom.buffer(buffer_size, 5)
            il_objects_result_dict = {} # конечный результат отобранных пересекаемых объектов
            il_fields_aliases_dict = self.inters_layer.attributeAliases() # алиасы полей слоя
            additional_layers = self.getAdditionalLayerData() # дополнительные пересекаемые слои (для вычисления количества общих пересечений)

            if layer_by_percent: # если сравнение по общим объектам дополнительного слоя
                self.dockWidget.labelResult.setText(f"Слой <{self.inters_layer.name()}>.\n"
                                                    f"Результат отбора по общим объектам в слое <{layer_by_percent.name()}>.\n"
                                                    f"(Id объекта: {current_feature_id}. Длина объекта: {current_feature_length}) м.")
            else: # если сравнение по длине
                self.dockWidget.labelResult.setText(f"Слой <{self.inters_layer.name()}>.\n"
                                                    f"Результат отбора по длине пересечений.\n"
                                                    f"(Id объекта: {current_feature_id}. Длина объекта: {current_feature_length} м.)")

            # генерация фильтра для получения всех объектов слоя
            filter_expression = self.generateFilterExpression(filters_dict)
            if filter_expression:
                expr = QgsExpression(filter_expression)
                request = QgsFeatureRequest(expr)
                inters_layer_features = list(self.inters_layer.getFeatures(request))
            else:
                inters_layer_features = list(self.inters_layer.getFeatures())
            fcnt = (len((inters_layer_features))) # общее число (отфильтрованных) объектов в слое

            for idx, intfeat in enumerate(inters_layer_features):
                if intfeat.id() == current_feature_id and self.current_layer == self.inters_layer: #отсекаем сравниваемую линию
                    continue
                if intfeat.geometry().intersects(current_feature_buf):
                    task.setProgress(idx/float(fcnt)*100)
                    if task.isCanceled():
                        self.stopped(task)
                        return

                    intfeat_buffer = intfeat.geometry().buffer(buffer_size, 5) # буфер пересекающихся линий, для отображения пересечений
                    intersection_buffer = QgsGeometry(intfeat_buffer).intersection(current_feature_buf) # для отображения пересечений
                    intersection_line = QgsGeometry(intfeat.geometry()).intersection(current_feature_buf) # части текущей линии, которые попали в буфер сравниваемого объекта

                    intfeat_length = intfeat.geometry().length()
                    intersection_line_length = intersection_line.length()
                    attrs_add_layers_for_intfeat = None # Количество пересекаемых объектов из дополнительных слоев
                    attrs_add_layers_for_intersection = None # Количество общих пересекаемых объектов из дополнительных слоев

                    
                    if layer_by_percent: # если сравнивать по общим пересекаемыым объектам, а не по длине
                        attrs_add_layers_for_intfeat = self.getAdditionalLayersAttrs(
                                                                additional_layers,
                                                                intfeat.geometry(),
                                                                'Объекты в ')
                        attrs_add_layers_for_intersection = self.getAdditionalLayersAttrs(
                                                                additional_layers,
                                                                intersection_line,
                                                                'Общее в ')
                        cnt_intfeat_by_layer = attrs_add_layers_for_intfeat['Объекты в '+layer_by_percent.name()]
                        cnt_intersection_by_layer = attrs_add_layers_for_intersection['Общее в '+layer_by_percent.name()]

                        if cnt_intfeat_by_layer == 0:
                            result_percent_inters = 0
                        else:
                            result_percent_inters = (cnt_intersection_by_layer/cnt_intfeat_by_layer)*100
                    else: # если сравнивать по длине
                        # процент - отношение длины пересечения к длине пересекаемого пути
                        result_percent_inters = (intersection_line_length/intfeat_length) * 100 

                    if result_percent_inters >= percent_inters:
                        attrs_sys = {
                            "feature_id": intfeat.id(),
                            "WKT_inters_feature": intfeat.geometry().asWkt(),
                            "WKT_intersection_line": intersection_line.asWkt()
                        }
                        attrs_calculated = {
                            "Длина объекта": round(intfeat_length, 2),
                            "Длина пересечения": round(intersection_line_length, 2),
                            "Процент пересечения": round(result_percent_inters, 2)
                        }
                        attrs_feature_layer = self.getDictFeaturesAttributes(intfeat, il_fields_aliases_dict)

                        if not attrs_add_layers_for_intfeat:
                            attrs_add_layers_for_intfeat = self.getAdditionalLayersAttrs(
                                                                additional_layers,
                                                                intfeat.geometry(), 
                                                                'Объекты в ')
                        if not attrs_add_layers_for_intersection:
                            attrs_add_layers_for_intersection = self.getAdditionalLayersAttrs(
                                                                additional_layers,
                                                                intersection_line,
                                                                'Общее в ')
                        feat_attrs={}
                        feat_attrs = {**attrs_sys,
                                    **attrs_feature_layer,
                                    **attrs_calculated,
                                    **attrs_add_layers_for_intfeat,
                                    **attrs_add_layers_for_intersection} # объединение высчитываемых атрибутов и атрибутов слоя (объекта)

                        il_objects_result_dict[intfeat.id()] = feat_attrs
            il_objects_result_dict = OrderedDict(sorted(il_objects_result_dict.items(), 
                                    key=lambda kv: kv[1]["Процент пересечения"], reverse=True))
            self.setFilterLayer(self.inters_layer, list(il_objects_result_dict.keys()))
            return il_objects_result_dict        
        except Exception as e:
            exc_type, exc_obj, exc_tb = os.system.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            message = f"{exc_tb.tb_lineno}, {str(e)},  {exc_type}, {fname}"
            QgsMessageLog.logMessage(message, self.MESSAGE_CATEGORY, Qgis.Info)


    def generateFilterExpression(self, filters_dict):
        expressions_list = []

        for key, value in filters_dict.items():
            if key.startswith('_'):
                continue
            if isinstance(value, list):
                if len(value) > 0:
                    unionvalue = ', '.join("'" + item + "'" for item in value)
                    expressions_list.append(f"{key} in ({unionvalue})")
            if isinstance(value, str):
                expressions_list.append(f"{key} like {value}")
            if isinstance(value, int):
                expressions_list.append(f"{key} = {int(value)}")
            if isinstance(value, float):
                expressions_list.append(f"{key} = {float(value)}")
        
        if len(expressions_list) > 0:
            expression = " and ".join(expressions_list)
            return expression
        return None


    def getDictFeaturesAttributes(self, intfeat, fields_aliases_dict):
        feature_attributes = {}
        if self.settings_layer is not None:
            result_fields = self.settings_layer.get("result_fields")
            if result_fields is not None:
                for rf in result_fields:
                    field_idx = self.inters_layer.fields().indexFromName(rf)
                    if field_idx > -1:
                        field = fields_aliases_dict[rf] if fields_aliases_dict[rf] else rf
                        value = CommonTools.representFieldValueByType(field_idx, self.inters_layer, intfeat[rf])
                        feature_attributes[field] = value
                return feature_attributes
        for key, value in fields_aliases_dict.items():
            field = value if value else key
            field_idx = self.inters_layer.fields().indexFromName(key)
            feature_attributes[field] = CommonTools.representFieldValueByType(field_idx, self.inters_layer, intfeat[key])
        return feature_attributes


    def populateTableResult(self, table, objects_dict):
        table.reset()
        table.sortItems(-1)
        if not objects_dict:
            print("not found")
            return

        first_feature_data = list(objects_dict.items())[0][1]

        headers_labels_list = list(first_feature_data.keys())
        columns_cnt = len(headers_labels_list)
        rows_cnt = len(list(objects_dict.keys()))
        table.setRowCount(rows_cnt)
        table.setColumnCount(columns_cnt)

        for rownum, f_id in enumerate(objects_dict):
            attr_values_list = list(objects_dict[f_id].values())
            for columnnum, attr_value in enumerate(attr_values_list):
                item = QTableWidgetItem()
                item.setData(Qt.EditRole, attr_value)
                table.setItem(rownum, columnnum, item)

        table.setHorizontalHeaderLabels(headers_labels_list)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.setColumnHidden(0, True)
        table.setColumnHidden(1, True)
        table.setColumnHidden(2, True)


    def setFilterLayer(self, layer, features_ids=None):
        subsetstring = ""
        if features_ids is not None:
            if len(features_ids) > 0:
                if self.settings_layer:
                    id_field = self.settings_layer.get('id_field', '$id')
                else:
                    id_field = '$id'
                ids_string = ", ".join(map(str, features_ids))
                subsetstring = f"{id_field} in ({ids_string})"
        layer.setSubsetString(subsetstring)


    def getAdditionalLayerData(self):
        if self.settings_layer:
            additional_layers_data_list = []

            additional_layers = None
            try:
                additional_layers = self.settings_layer["filters_fields"]["_by_addition_layer"]["additional_layers"]
            except:
                pass
            if additional_layers:
                for layer_name in additional_layers:
                    layers = QgsProject.instance().mapLayersByName(layer_name)
                    if len(layers) > 1:
                        print(f"В проекте более одного слоя с именем {layer_name}")
                        break
                    if len(layers) == 0:
                        print(f"В проекте не найдено ни одного слоя с именем {layer_name}")
                        break
                    layer = layers[0]

                    add_buf_field = additional_layers[layer_name].get("buffer_field")
                    additional_layers_data_list.append({"layer": layer, "add_buf_field": add_buf_field})
            return additional_layers_data_list


    def getAdditionalLayersAttrs(self, layers_data_list, geometry, prefix_name):
        attributes_dict = {}

        for layer_data in layers_data_list:
            layer = layer_data["layer"]
            features = layer.getFeatures(geometry.boundingBox())

            cnt_intersects = 0
            add_buf_field = layer_data["add_buf_field"]
            for feat in features:
                if add_buf_field:
                    buffer_size = (feat[add_buf_field])
                    if not (isinstance(feat[add_buf_field], int) or isinstance(feat[add_buf_field], float)):
                        buffer_size = 0
                    if geometry.intersects(feat.geometry().buffer(buffer_size, 5)):
                        cnt_intersects += 1
                else:
                    if geometry.intersects(feat.geometry()):
                        cnt_intersects += 1

            attributes_dict[prefix_name + layer.name()] = cnt_intersects

        return attributes_dict


