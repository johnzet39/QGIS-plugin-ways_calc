from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QTableWidgetItem, QListWidgetItem, QApplication
from qgis.PyQt.QtCore import Qt, QVariant

class CommonTools:
    
    @staticmethod
    def createTableItem(column_name, layer, value):
        idx_field = layer.fields().indexFromName(column_name)
        if idx_field > -1:
            value = CommonTools.representFieldValueByType(idx_field, layer, value)
        item = QTableWidgetItem()
        item.setData(Qt.EditRole, value)
        return item


    @staticmethod
    def representFieldValueByType(column_idx, layer, value):
        if value is None:
            return ''

        field_type = layer.editorWidgetSetup(column_idx).type()

        # подставляем значения в соответствии с заданными справочниками в виджетах
        if field_type == 'ValueMap':
            valuemap = layer.editorWidgetSetup(column_idx).config()['map']
            # почему-то некоторые "Карты значений" представлены в виде словарей,
            # а некоторые в виде списков словарей. Объединяем последние в словари
            if isinstance(valuemap, list): 
                newvaluemap = {}
                for d in valuemap:
                    newvaluemap[list(d.keys())[0]] = d[list(d.keys())[0]]
                valuemap = newvaluemap

            # если число как строка или float, то преобразуем его в int.
            # т.е. '1' или 1.0 в 1 
            if isinstance(value, str):
                if value.isnumeric():
                    value = int(value)
            if isinstance(value, float):
                value = int(value)
            # значение из словаря
            value = list(valuemap.keys())[list(valuemap.values()).index(str(value))]
        return value


    @staticmethod
    def populateTableByClickedFeatures(layer, table):
        header_labels_list = []
        header_labels_list.append('feature_id')
        header_labels_list.append('geometry')

        # if addattributes is not None:
        #     for att in next(iter(addattributes.values())):
        #         header_labels_list.append(att)

        field_aliases_dict = layer.attributeAliases()
        for k in field_aliases_dict.keys():
            field = field_aliases_dict[k] if field_aliases_dict[k] else k
            header_labels_list.append(field)

        layer_current_selected_fs = []
        for feature in layer.selectedFeatures():
            feature_attributes_dict = {}
            feature_attributes_dict["feature_id"] = feature.id()
            feature_attributes_dict["geometry"] = feature.geometry().asWkt()

            # if addattributes is not None:
            #     for atkey, atvalue in addattributes[feature.id()].items():
            #         feature_attributes_dict[atkey] = atvalue

            for field_name in field_aliases_dict.keys():
                feature_attributes_dict[field_name] = feature[field_name]
            layer_current_selected_fs.append(feature_attributes_dict)

        features_cnt = layer.selectedFeatureCount()
        columns_cnt = len(header_labels_list)
        table.setRowCount(features_cnt)
        table.setColumnCount(columns_cnt)

        for rownum in range(features_cnt):
            for f_idx, fieldname in enumerate(layer_current_selected_fs[0].keys()):
                attr_value = layer_current_selected_fs[rownum][fieldname]
                # item = self.createTableItem(rownum, fieldname, self.layer_current, attr_value)
                item = CommonTools.createTableItem(fieldname, layer, attr_value)
                table.setItem(rownum, f_idx, item)

        table.setHorizontalHeaderLabels(header_labels_list)
        table.resizeColumnsToContents()
        if len(header_labels_list) > 2:
            table.setColumnHidden(0, True)
        table.setColumnHidden(1, True)
        return layer_current_selected_fs


    def populateTableByFeatures(layer, table):
        pass


    @staticmethod
    def clearFiltersLayout(layout):
        for i in reversed(range(layout.count())):
            if layout.itemAt(i).layout():
                CommonTools.clearFieldsLayout(layout.itemAt(i).layout())
                layout.itemAt(i).layout().setParent(None)
            elif layout.itemAt(i).widget():
                layout.itemAt(i).widget().setParent(None)  


    @staticmethod
    def addFilter(field, layer, layout, settings_layer):
        filter_label = QtWidgets.QLabel()
        filter_label.setObjectName(f"label_{field}")
        filter_label.setText(settings_layer["filters_fields"][field]["label"])
        
        filter_widget = CommonTools.__createWidget(field, layer, settings_layer)
        
        layout.addRow(filter_label, filter_widget)


    @staticmethod
    def __createWidget(field, layer, settings_layer):
        settings_field = settings_layer["filters_fields"][field]
        widget_type = settings_field["widget_type"]
        filter_widget = getattr(QtWidgets, widget_type)()
        filter_widget.setObjectName(field)

        widget_options = settings_field["widget_options"]
        for wo in widget_options:
            value = widget_options[wo]
            try:
                value = int(value)
            except:
                try:
                    value = float(value)
                except:
                    pass
            getattr(filter_widget, wo)(value)

        if settings_field["source_type"] == "own":
            idx_field = layer.fields().indexFromName(field)
            if not idx_field > 0:
                print(f"Field {field} does not found in layer")
            field_type = layer.editorWidgetSetup(idx_field).type()
            if field_type == 'ValueMap':
                valuemap = layer.editorWidgetSetup(idx_field).config()['map']

                # по какой-то неведомой причине какие-то 
                # карты значений в виде списка, 
                # какие-то в виде словарей
                if isinstance(valuemap, list): 
                    newvaluemap = {}
                    for d in valuemap:
                        newvaluemap[list(d.keys())[0]] = d[list(d.keys())[0]]
                    valuemap = newvaluemap

                for key, value in valuemap.items():
                    if widget_type == "QListWidget":
                        item = QListWidgetItem(key)
                        item.setData(Qt.UserRole, QVariant(value))
                        filter_widget.addItem(item)
                    elif widget_type == "QComboBox":
                        filter_widget.addItem(key, QVariant(value))
                        filter_widget.setCurrentIndex(-1)

        elif settings_field["source_type"] == "custom":
            if widget_type == "QComboBox":
                filter_widget.setCurrentIndex(-1)
                filter_widget.addItem(None, QVariant(None))

        return filter_widget


    @staticmethod
    def findWidgetByName(layout, widget_name):
        for i in reversed(range(layout.count())): 
            if layout.itemAt(i).widget():
                widget = layout.itemAt(i).widget()
                if widget.objectName() == widget_name:
                    return widget
    
    @staticmethod
    def getFilterValues(fieldname, layout):
        value = None
        widget= CommonTools.findWidgetByName(layout, fieldname)
        if widget:
            if widget.metaObject().className() == "QSpinBox":
                value = widget.value()
            if widget.metaObject().className() == "QDoubleSpinBox":
                value = widget.value()
            elif widget.metaObject().className() == "QListWidget":
                value = [item.data(Qt.UserRole) for item in widget.selectedItems()]
            elif widget.metaObject().className() == "QComboBox":
                value = widget.currentData(Qt.UserRole)
        return value

    @staticmethod
    def copyResult(dockWidget, exclude_idx_copyresult):
        table = dockWidget.tableResult
        colcount = table.columnCount()
        rowcount = table.rowCount()
        rowStrings = []
        rowStrings.append('"' + dockWidget.labelResult.text().replace('\n', ' ') + '"')
        columns_idx_list = list(range(colcount))

        for idx in (reversed(exclude_idx_copyresult)):
            del columns_idx_list[idx]
        headers = [table.horizontalHeaderItem(col).text() for col in columns_idx_list]
        headers_row = '\t'.join('"' + item + '"' for item in headers)
        rowStrings.append(headers_row)

        for rowIndex in range(rowcount):
            rowItemsStrings = []
            for columnIndex in columns_idx_list:
                item = table.item(rowIndex, columnIndex)
                itemText = '""'
                if item:
                    itemText = '"' + item.text().replace('"', '""') + '"'
                rowItemsStrings.append(itemText)
            rowStrings.append('\t'.join(rowItemsStrings))
        result_string = '\n'.join(rowStrings)
        QApplication.clipboard().setText(result_string)