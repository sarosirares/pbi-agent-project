/*
 *  Power BI Visualizations
 *
 *  Copyright (c) Microsoft Corporation
 *  All rights reserved.
 *  MIT License
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy
 *  of this software and associated documentation files (the ""Software""), to deal
 *  in the Software without restriction, including without limitation the rights
 *  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *  copies of the Software, and to permit persons to whom the Software is
 *  furnished to do so, subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be included in
 *  all copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 *  THE SOFTWARE.
 */

var powerbi;
(function (powerbi) {
    var visuals;
    (function (visuals) {
        var ChicletSlicer1448559807354;
        (function (ChicletSlicer1448559807354) {
            var createClassAndSelector = jsCommon.CssConstants.createClassAndSelector;
            var PixelConverter = jsCommon.PixelConverter;
            var createEnumType = powerbi.createEnumType;
            var DataViewObjects = powerbi.DataViewObjects;
            var VisualDataRoleKind = powerbi.VisualDataRoleKind;
            var DataViewAnalysis = powerbi.DataViewAnalysis;
            var TextMeasurementService = powerbi.TextMeasurementService;
            // powerbi.data
            var SemanticFilter = powerbi.data.SemanticFilter;
            var SQExprConverter = powerbi.data.SQExprConverter;
            var Selector = powerbi.data.Selector;
            var valueFormatter = powerbi.visuals.valueFormatter;
            var createInteractivityService = powerbi.visuals.createInteractivityService;
            var isCategoryColumnSelected = powerbi.visuals.isCategoryColumnSelected;
            var converterHelper = powerbi.visuals.converterHelper;
            var SelectionIdBuilder = powerbi.visuals.SelectionIdBuilder;
            var TableViewFactory;
            (function (TableViewFactory) {
                function createTableView(options) {
                    return new TableView(options);
                }
                TableViewFactory.createTableView = createTableView;
            })(TableViewFactory = ChicletSlicer1448559807354.TableViewFactory || (ChicletSlicer1448559807354.TableViewFactory = {}));
            /**
             * A UI Virtualized List, that uses the D3 Enter, Update & Exit pattern to update rows.
             * It can create lists containing either HTML or SVG elements.
             */
            var TableView = (function () {
                function TableView(options) {
                    // make a copy of options so that it is not modified later by caller
                    this.options = $.extend(true, {}, options);
                    this.options.baseContainer
                        .style('overflow-y', 'auto')
                        .attr('drag-resize-disabled', true);
                    this.scrollContainer = options.baseContainer
                        .append('div')
                        .attr('class', 'scrollRegion');
                    this.visibleGroupContainer = this.scrollContainer
                        .append('div')
                        .attr('class', 'visibleGroup');
                    TableView.SetDefaultOptions(options);
                }
                TableView.SetDefaultOptions = function (options) {
                    options.rowHeight = options.rowHeight || TableView.defaultRowHeight;
                };
                Object.defineProperty(TableView.prototype, "computedColumns", {
                    get: function () {
                        return this.computedOptions
                            ? this.computedOptions.columns
                            : 0;
                    },
                    enumerable: true,
                    configurable: true
                });
                Object.defineProperty(TableView.prototype, "computedRows", {
                    get: function () {
                        return this.computedOptions
                            ? this.computedOptions.rows
                            : 0;
                    },
                    enumerable: true,
                    configurable: true
                });
                TableView.prototype.rowHeight = function (rowHeight) {
                    this.options.rowHeight = Math.ceil(rowHeight);
                    return this;
                };
                TableView.prototype.columnWidth = function (columnWidth) {
                    this.options.columnWidth = Math.ceil(columnWidth);
                    return this;
                };
                TableView.prototype.orientation = function (orientation) {
                    this.options.orientation = orientation;
                    return this;
                };
                TableView.prototype.rows = function (rows) {
                    this.options.rows = Math.ceil(rows);
                    return this;
                };
                TableView.prototype.columns = function (columns) {
                    this.options.columns = Math.ceil(columns);
                    return this;
                };
                TableView.prototype.data = function (data, getDatumIndex, dataReset) {
                    if (dataReset === void 0) { dataReset = false; }
                    this._data = data;
                    this.getDatumIndex = getDatumIndex;
                    this.setTotalRows();
                    if (dataReset) {
                        $(this.options.baseContainer.node()).scrollTop(0);
                    }
                    return this;
                };
                TableView.prototype.viewport = function (viewport) {
                    this.options.viewport = viewport;
                    return this;
                };
                TableView.prototype.empty = function () {
                    this._data = [];
                    this.render();
                    return this;
                };
                TableView.prototype.setTotalRows = function () {
                    var count = this._data.length, rows = Math.min(this.options.rows, count), columns = Math.min(this.options.columns, count);
                    if ((columns > 0) && (rows > 0)) {
                        this._totalColumns = columns;
                        this._totalRows = rows;
                    }
                    else if (rows > 0) {
                        this._totalRows = rows;
                        this._totalColumns = Math.ceil(count / rows);
                    }
                    else if (columns > 0) {
                        this._totalColumns = columns;
                        this._totalRows = Math.ceil(count / columns);
                    }
                    else {
                        this._totalColumns = TableView.defaultColumns;
                        this._totalRows = Math.ceil(count / TableView.defaultColumns);
                    }
                };
                TableView.prototype.getGroupedData = function () {
                    var options = this.options, groupedData = [], totalRows = options.rows, totalColumns = options.columns, totalItems = this._data.length, totalRows = options.rows > totalItems
                        ? totalItems
                        : options.rows, totalColumns = options.columns > totalItems
                        ? totalItems
                        : options.columns;
                    if (totalColumns === 0 && totalRows === 0) {
                        if (options.orientation === Orientation.HORIZONTAL) {
                            totalColumns = totalItems;
                            totalRows = 1;
                        }
                        else {
                            totalColumns = 1;
                            totalRows = totalItems;
                        }
                    }
                    else if (totalColumns === 0 && totalRows > 0) {
                        totalColumns = Math.ceil(totalItems / totalRows);
                    }
                    else if (totalColumns > 0 && totalRows === 0) {
                        totalRows = Math.ceil(totalItems / totalColumns);
                    }
                    if (this.options.orientation === Orientation.VERTICAL) {
                        var n = totalRows;
                        totalRows = totalColumns;
                        totalColumns = n;
                    }
                    else if (this.options.orientation === Orientation.HORIZONTAL) {
                        if (totalRows === 0) {
                            totalRows = this._totalRows;
                        }
                        if (totalColumns === 0) {
                            totalColumns = this._totalColumns;
                        }
                    }
                    var m = 0, k = 0;
                    for (var i = 0; i < totalRows; i++) {
                        if (this.options.orientation === Orientation.VERTICAL
                            && options.rows === 0
                            && totalItems % options.columns > 0
                            && options.columns <= totalItems) {
                            if (totalItems % options.columns > i) {
                                m = i * Math.ceil(totalItems / options.columns);
                                k = m + Math.ceil(totalItems / options.columns);
                                this.addDataToArray(groupedData, this._data, m, k);
                            }
                            else {
                                this.addDataToArray(groupedData, this._data, k, k + Math.floor(totalItems / options.columns));
                                k = k + Math.floor(totalItems / options.columns);
                            }
                        }
                        else if (this.options.orientation === Orientation.HORIZONTAL
                            && options.columns === 0
                            && totalItems % options.rows > 0
                            && options.rows <= totalItems) {
                            if (totalItems % options.rows > i) {
                                m = i * Math.ceil(totalItems / options.rows);
                                k = m + Math.ceil(totalItems / options.rows);
                                this.addDataToArray(groupedData, this._data, m, k);
                            }
                            else {
                                this.addDataToArray(groupedData, this._data, k, k + Math.floor(totalItems / options.rows));
                                k = k + Math.floor(totalItems / options.rows);
                            }
                        }
                        else {
                            var k = i * totalColumns;
                            this.addDataToArray(groupedData, this._data, k, k + totalColumns);
                        }
                    }
                    this.computedOptions = this.getComputedOptions(groupedData, this.options.orientation);
                    return {
                        data: groupedData,
                        totalColumns: totalColumns,
                        totalRows: totalRows
                    };
                };
                TableView.prototype.addDataToArray = function (array, data, start, end) {
                    if (!array || !data) {
                        return;
                    }
                    var elements = data.slice(start, end);
                    if (elements && elements.length > 0) {
                        array.push(elements);
                    }
                };
                TableView.prototype.getComputedOptions = function (data, orientation) {
                    var rows, columns = 0;
                    rows = data
                        ? data.length
                        : 0;
                    for (var i = 0; i < rows; i++) {
                        var currentRow = data[i];
                        if (currentRow && currentRow.length > columns) {
                            columns = currentRow.length;
                        }
                    }
                    if (orientation === Orientation.HORIZONTAL) {
                        return {
                            columns: columns,
                            rows: rows
                        };
                    }
                    else {
                        return {
                            columns: rows,
                            rows: columns
                        };
                    }
                };
                TableView.prototype.render = function () {
                    var options = this.options, visibleGroupContainer = this.visibleGroupContainer, rowHeight = options.rowHeight || TableView.defaultRowHeight, groupedData = this.getGroupedData(), rowSelection, cellSelection;
                    rowSelection = visibleGroupContainer
                        .selectAll(TableView.RowSelector.selector)
                        .data(groupedData.data);
                    rowSelection
                        .enter()
                        .append("div")
                        .classed(TableView.RowSelector.class, true);
                    cellSelection = rowSelection
                        .selectAll(TableView.CellSelector.selector)
                        .data(function (dataPoints) {
                        return dataPoints;
                    });
                    cellSelection
                        .enter()
                        .append('div')
                        .classed(TableView.CellSelector.class, true);
                    cellSelection.call(function (selection) {
                        options.enter(selection);
                    });
                    cellSelection.call(function (selection) {
                        options.update(selection);
                    });
                    cellSelection.style({
                        'height': (rowHeight > 0) ? rowHeight + 'px' : 'auto'
                    });
                    if (this.options.orientation === Orientation.VERTICAL) {
                        var realColumnNumber = 0;
                        for (var i = 0; i < groupedData.data.length; i++) {
                            if (groupedData.data[i].length !== 0)
                                realColumnNumber = i + 1;
                        }
                        cellSelection.style({ 'width': '100%' });
                        rowSelection
                            .style({
                            'width': (options.columnWidth > 0)
                                ? options.columnWidth + 'px'
                                : (100 / realColumnNumber) + '%'
                        });
                    }
                    else {
                        cellSelection.style({
                            'width': (options.columnWidth > 0)
                                ? options.columnWidth + 'px'
                                : (100 / groupedData.totalColumns) + '%'
                        });
                        rowSelection.style({ 'width': null });
                    }
                    cellSelection
                        .exit()
                        .remove();
                    rowSelection
                        .exit()
                        .call(function (d) { return options.exit(d); })
                        .remove();
                };
                TableView.RowSelector = createClassAndSelector('row');
                TableView.CellSelector = createClassAndSelector('cell');
                TableView.defaultRowHeight = 0;
                TableView.defaultColumns = 1;
                return TableView;
            }());
            ChicletSlicer1448559807354.TableView = TableView;
            // TODO: Generate these from above, defining twice just introduces potential for error
            ChicletSlicer1448559807354.chicletSlicerProps = {
                general: {
                    orientation: { objectName: 'general', propertyName: 'orientation' },
                    columns: { objectName: 'general', propertyName: 'columns' },
                    rows: { objectName: 'general', propertyName: 'rows' },
                    showDisabled: { objectName: 'general', propertyName: 'showDisabled' },
                    multiselect: { objectName: 'general', propertyName: 'multiselect' },
                    forcedSelection: { objectName: 'general', propertyName: 'forcedSelection' },
                    selection: { objectName: 'general', propertyName: 'selection' },
                    selfFilterEnabled: { objectName: 'general', propertyName: 'selfFilterEnabled' },
                },
                header: {
                    show: { objectName: 'header', propertyName: 'show' },
                    title: { objectName: 'header', propertyName: 'title' },
                    fontColor: { objectName: 'header', propertyName: 'fontColor' },
                    background: { objectName: 'header', propertyName: 'background' },
                    outline: { objectName: 'header', propertyName: 'outline' },
                    textSize: { objectName: 'header', propertyName: 'textSize' },
                    outlineColor: { objectName: 'header', propertyName: 'outlineColor' },
                    outlineWeight: { objectName: 'header', propertyName: 'outlineWeight' }
                },
                rows: {
                    fontColor: { objectName: 'rows', propertyName: 'fontColor' },
                    textSize: { objectName: 'rows', propertyName: 'textSize' },
                    height: { objectName: 'rows', propertyName: 'height' },
                    width: { objectName: 'rows', propertyName: 'width' },
                    background: { objectName: 'rows', propertyName: 'background' },
                    transparency: { objectName: 'rows', propertyName: 'transparency' },
                    selectedColor: { objectName: 'rows', propertyName: 'selectedColor' },
                    hoverColor: { objectName: 'rows', propertyName: 'hoverColor' },
                    unselectedColor: { objectName: 'rows', propertyName: 'unselectedColor' },
                    disabledColor: { objectName: 'rows', propertyName: 'disabledColor' },
                    outline: { objectName: 'rows', propertyName: 'outline' },
                    outlineColor: { objectName: 'rows', propertyName: 'outlineColor' },
                    outlineWeight: { objectName: 'rows', propertyName: 'outlineWeight' },
                    padding: { objectName: 'rows', propertyName: 'padding' },
                    borderStyle: { objectName: 'rows', propertyName: 'borderStyle' },
                },
                images: {
                    imageSplit: { objectName: 'images', propertyName: 'imageSplit' },
                    stretchImage: { objectName: 'images', propertyName: 'stretchImage' },
                    bottomImage: { objectName: 'images', propertyName: 'bottomImage' },
                },
                selectedPropertyIdentifier: { objectName: 'general', propertyName: 'selected' },
                filterPropertyIdentifier: { objectName: 'general', propertyName: 'filter' },
                formatString: { objectName: 'general', propertyName: 'formatString' },
                hasSavedSelection: true,
            };
            var ChicletBorderStyle;
            (function (ChicletBorderStyle) {
                ChicletBorderStyle.ROUNDED = 'Rounded';
                ChicletBorderStyle.CUT = 'Cut';
                ChicletBorderStyle.SQUARE = 'Square';
                ChicletBorderStyle.type = createEnumType([
                    { value: ChicletBorderStyle.ROUNDED, displayName: ChicletBorderStyle.ROUNDED },
                    { value: ChicletBorderStyle.CUT, displayName: ChicletBorderStyle.CUT },
                    { value: ChicletBorderStyle.SQUARE, displayName: ChicletBorderStyle.SQUARE },
                ]);
            })(ChicletBorderStyle || (ChicletBorderStyle = {}));
            var ChicletSlicerShowDisabled;
            (function (ChicletSlicerShowDisabled) {
                ChicletSlicerShowDisabled.INPLACE = 'Inplace';
                ChicletSlicerShowDisabled.BOTTOM = 'Bottom';
                ChicletSlicerShowDisabled.HIDE = 'Hide';
                ChicletSlicerShowDisabled.type = createEnumType([
                    { value: ChicletSlicerShowDisabled.INPLACE, displayName: ChicletSlicerShowDisabled.INPLACE },
                    { value: ChicletSlicerShowDisabled.BOTTOM, displayName: ChicletSlicerShowDisabled.BOTTOM },
                    { value: ChicletSlicerShowDisabled.HIDE, displayName: ChicletSlicerShowDisabled.HIDE },
                ]);
            })(ChicletSlicerShowDisabled || (ChicletSlicerShowDisabled = {}));
            var Orientation;
            (function (Orientation) {
                Orientation.HORIZONTAL = 'Horizontal';
                Orientation.VERTICAL = 'Vertical';
                Orientation.type = createEnumType([
                    { value: Orientation.HORIZONTAL, displayName: Orientation.HORIZONTAL },
                    { value: Orientation.VERTICAL, displayName: Orientation.VERTICAL }
                ]);
            })(Orientation || (Orientation = {}));
            var ChicletSlicer = (function () {
                function ChicletSlicer(options) {
                    if (options) {
                        if (options.behavior) {
                            this.behavior = options.behavior;
                        }
                    }
                    if (!this.behavior) {
                        this.behavior = new ChicletSlicerWebBehavior();
                    }
                }
                ChicletSlicer.DefaultStyleProperties = function () {
                    return {
                        general: {
                            orientation: Orientation.VERTICAL,
                            columns: 3,
                            rows: 0,
                            multiselect: true,
                            forcedSelection: false,
                            showDisabled: ChicletSlicerShowDisabled.INPLACE,
                            selection: null,
                            selfFilterEnabled: false
                        },
                        margin: {
                            top: 50,
                            bottom: 50,
                            right: 50,
                            left: 50
                        },
                        header: {
                            borderBottomWidth: 1,
                            show: true,
                            outline: 'BottomOnly',
                            fontColor: '#a6a6a6',
                            background: null,
                            textSize: 10,
                            outlineColor: '#a6a6a6',
                            outlineWeight: 1,
                            title: '',
                        },
                        headerText: {
                            marginLeft: 8,
                            marginTop: 0
                        },
                        slicerText: {
                            textSize: 10,
                            height: 0,
                            width: 0,
                            fontColor: '#666666',
                            hoverColor: '#212121',
                            selectedColor: '#BDD7EE',
                            unselectedColor: '#ffffff',
                            disabledColor: 'grey',
                            marginLeft: 8,
                            outline: 'Frame',
                            background: null,
                            transparency: 0,
                            outlineColor: '#000000',
                            outlineWeight: 1,
                            padding: 3,
                            borderStyle: 'Cut',
                        },
                        slicerItemContainer: {
                            // The margin is assigned in the less file. This is needed for the height calculations.
                            marginTop: 5,
                            marginLeft: 0,
                        },
                        images: {
                            imageSplit: 50,
                            stretchImage: false,
                            bottomImage: false
                        }
                    };
                };
                /**
                 * Public to testability.
                 */
                ChicletSlicer.getValidImageSplit = function (imageSplit) {
                    if (imageSplit < ChicletSlicer.MinImageSplit) {
                        return ChicletSlicer.MinImageSplit;
                    }
                    else if (imageSplit > ChicletSlicer.MaxImageSplit) {
                        return ChicletSlicer.MaxImageSplit;
                    }
                    else {
                        return imageSplit;
                    }
                };
                ChicletSlicer.converter = function (dataView, searchText, interactivityService) {
                    if (!dataView ||
                        !dataView.categorical ||
                        !dataView.categorical.categories ||
                        !dataView.categorical.categories[0] ||
                        !dataView.categorical.categories[0].values ||
                        !(dataView.categorical.categories[0].values.length > 0)) {
                        return;
                    }
                    var converter = new ChicletSlicerChartConversion.ChicletSlicerConverter(dataView, interactivityService);
                    converter.convert();
                    var slicerData, defaultSettings = this.DefaultStyleProperties(), objects = dataView.metadata.objects;
                    if (objects) {
                        defaultSettings.general.orientation = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.orientation, defaultSettings.general.orientation);
                        defaultSettings.general.columns = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.columns, defaultSettings.general.columns);
                        defaultSettings.general.rows = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.rows, defaultSettings.general.rows);
                        defaultSettings.general.multiselect = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.multiselect, defaultSettings.general.multiselect);
                        defaultSettings.general.forcedSelection = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.forcedSelection, defaultSettings.general.forcedSelection);
                        defaultSettings.general.showDisabled = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.showDisabled, defaultSettings.general.showDisabled);
                        defaultSettings.general.selection = DataViewObjects.getValue(dataView.metadata.objects, ChicletSlicer1448559807354.chicletSlicerProps.general.selection, defaultSettings.general.selection);
                        defaultSettings.general.selfFilterEnabled = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.general.selfFilterEnabled, defaultSettings.general.selfFilterEnabled);
                        defaultSettings.header.show = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.show, defaultSettings.header.show);
                        defaultSettings.header.title = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.title, defaultSettings.header.title);
                        defaultSettings.header.fontColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.fontColor, defaultSettings.header.fontColor);
                        defaultSettings.header.background = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.background, defaultSettings.header.background);
                        defaultSettings.header.textSize = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.textSize, defaultSettings.header.textSize);
                        defaultSettings.header.outline = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.outline, defaultSettings.header.outline);
                        defaultSettings.header.outlineColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.outlineColor, defaultSettings.header.outlineColor);
                        defaultSettings.header.outlineWeight = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.header.outlineWeight, defaultSettings.header.outlineWeight);
                        defaultSettings.slicerText.textSize = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.textSize, defaultSettings.slicerText.textSize);
                        defaultSettings.slicerText.height = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.height, defaultSettings.slicerText.height);
                        defaultSettings.slicerText.width = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.width, defaultSettings.slicerText.width);
                        defaultSettings.slicerText.selectedColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.selectedColor, defaultSettings.slicerText.selectedColor);
                        defaultSettings.slicerText.hoverColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.hoverColor, defaultSettings.slicerText.hoverColor);
                        defaultSettings.slicerText.unselectedColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.unselectedColor, defaultSettings.slicerText.unselectedColor);
                        defaultSettings.slicerText.disabledColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.disabledColor, defaultSettings.slicerText.disabledColor);
                        defaultSettings.slicerText.background = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.background, defaultSettings.slicerText.background);
                        defaultSettings.slicerText.transparency = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.transparency, defaultSettings.slicerText.transparency);
                        defaultSettings.slicerText.fontColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.fontColor, defaultSettings.slicerText.fontColor);
                        defaultSettings.slicerText.outline = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.outline, defaultSettings.slicerText.outline);
                        defaultSettings.slicerText.outlineColor = DataViewObjects.getFillColor(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.outlineColor, defaultSettings.slicerText.outlineColor);
                        defaultSettings.slicerText.outlineWeight = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.outlineWeight, defaultSettings.slicerText.outlineWeight);
                        defaultSettings.slicerText.padding = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.padding, defaultSettings.slicerText.padding);
                        defaultSettings.slicerText.borderStyle = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.rows.borderStyle, defaultSettings.slicerText.borderStyle);
                        defaultSettings.images.imageSplit = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.images.imageSplit, defaultSettings.images.imageSplit);
                        defaultSettings.images.stretchImage = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.images.stretchImage, defaultSettings.images.stretchImage);
                        defaultSettings.images.bottomImage = DataViewObjects.getValue(objects, ChicletSlicer1448559807354.chicletSlicerProps.images.bottomImage, defaultSettings.images.bottomImage);
                    }
                    if (defaultSettings.general.selfFilterEnabled && searchText) {
                        searchText = searchText.toLowerCase();
                        converter.dataPoints.forEach(function (x) { return x.filtered = x.category.toLowerCase().indexOf(searchText) < 0; });
                    }
                    var categories = dataView.categorical.categories[0];
                    slicerData = {
                        categorySourceName: categories.source.displayName,
                        formatString: valueFormatter.getFormatString(categories.source, ChicletSlicer1448559807354.chicletSlicerProps.formatString),
                        slicerSettings: defaultSettings,
                        slicerDataPoints: converter.dataPoints,
                        identityFields: converter.identityFields
                    };
                    // Override hasSelection if a objects contained more scopeIds than selections we found in the data
                    slicerData.hasSelectionOverride = converter.hasSelectionOverride;
                    return slicerData;
                };
                ChicletSlicer.prototype.init = function (options) {
                    this.element = options.element;
                    this.currentViewport = options.viewport;
                    if (this.behavior) {
                        this.interactivityService = createInteractivityService(options.host);
                    }
                    this.hostServices = options.host;
                    this.hostServices.canSelect = ChicletSlicer.canSelect;
                    this.settings = ChicletSlicer.DefaultStyleProperties();
                    this.initContainer();
                };
                ChicletSlicer.canSelect = function (args) {
                    var selectors = _.map(args.visualObjects, function (visualObject) {
                        return Selector.convertSelectorsByColumnToSelector(visualObject.selectorsByColumn);
                    });
                    // We can't have multiple selections if any include more than one identity
                    if (selectors && (selectors.length > 1)) {
                        if (selectors.some(function (value) { return value && value.data && value.data.length > 1; })) {
                            return false;
                        }
                    }
                    // Todo: check for cases of trying to select a category and a series (not the intersection)
                    return true;
                };
                ChicletSlicer.prototype.update = function (options) {
                    if (!options ||
                        !options.dataViews ||
                        !options.dataViews[0] ||
                        !options.viewport) {
                        return;
                    }
                    var existingDataView = this.dataView;
                    this.dataView = options.dataViews[0];
                    var resetScrollbarPosition = true;
                    if (existingDataView) {
                        resetScrollbarPosition = !DataViewAnalysis.hasSameCategoryIdentity(existingDataView, this.dataView);
                    }
                    if (options.viewport.height === this.currentViewport.height
                        && options.viewport.width === this.currentViewport.width) {
                        this.waitingForData = false;
                    }
                    else {
                        this.currentViewport = options.viewport;
                    }
                    this.updateInternal(resetScrollbarPosition);
                };
                ChicletSlicer.prototype.onResizing = function (finalViewport) {
                    this.currentViewport = finalViewport;
                    this.updateInternal(false /* resetScrollbarPosition */);
                };
                ChicletSlicer.prototype.enumerateObjectInstances = function (options) {
                    var data = this.slicerData;
                    if (!data) {
                        return;
                    }
                    switch (options.objectName) {
                        case 'rows':
                            return this.enumerateRows(data);
                        case 'header':
                            return this.enumerateHeader(data);
                        case 'general':
                            return this.enumerateGeneral(data);
                        case 'images':
                            return this.enumerateImages(data);
                    }
                };
                ChicletSlicer.prototype.enumerateHeader = function (data) {
                    var slicerSettings = this.settings;
                    return [{
                            selector: null,
                            objectName: 'header',
                            properties: {
                                show: slicerSettings.header.show,
                                title: slicerSettings.header.title,
                                fontColor: slicerSettings.header.fontColor,
                                background: slicerSettings.header.background,
                                textSize: slicerSettings.header.textSize,
                                outline: slicerSettings.header.outline,
                                outlineColor: slicerSettings.header.outlineColor,
                                outlineWeight: slicerSettings.header.outlineWeight
                            }
                        }];
                };
                ChicletSlicer.prototype.enumerateRows = function (data) {
                    var slicerSettings = this.settings;
                    return [{
                            selector: null,
                            objectName: 'rows',
                            properties: {
                                textSize: slicerSettings.slicerText.textSize,
                                height: slicerSettings.slicerText.height,
                                width: slicerSettings.slicerText.width,
                                background: slicerSettings.slicerText.background,
                                transparency: slicerSettings.slicerText.transparency,
                                selectedColor: slicerSettings.slicerText.selectedColor,
                                hoverColor: slicerSettings.slicerText.hoverColor,
                                unselectedColor: slicerSettings.slicerText.unselectedColor,
                                disabledColor: slicerSettings.slicerText.disabledColor,
                                outline: slicerSettings.slicerText.outline,
                                outlineColor: slicerSettings.slicerText.outlineColor,
                                outlineWeight: slicerSettings.slicerText.outlineWeight,
                                fontColor: slicerSettings.slicerText.fontColor,
                                padding: slicerSettings.slicerText.padding,
                                borderStyle: slicerSettings.slicerText.borderStyle,
                            }
                        }];
                };
                ChicletSlicer.prototype.enumerateGeneral = function (data) {
                    var slicerSettings = this.settings;
                    return [{
                            selector: null,
                            objectName: 'general',
                            properties: {
                                orientation: slicerSettings.general.orientation,
                                columns: slicerSettings.general.columns,
                                rows: slicerSettings.general.rows,
                                showDisabled: slicerSettings.general.showDisabled,
                                multiselect: slicerSettings.general.multiselect,
                                forcedSelection: slicerSettings.general.forcedSelection,
                                selfFilterEnabled: slicerSettings.general.selfFilterEnabled
                            }
                        }];
                };
                ChicletSlicer.prototype.enumerateImages = function (data) {
                    var slicerSettings = this.settings;
                    return [{
                            selector: null,
                            objectName: 'images',
                            properties: {
                                imageSplit: slicerSettings.images.imageSplit,
                                stretchImage: slicerSettings.images.stretchImage,
                                bottomImage: slicerSettings.images.bottomImage,
                            }
                        }];
                };
                ChicletSlicer.prototype.updateInternal = function (resetScrollbarPosition) {
                    var _this = this;
                    var data = ChicletSlicer.converter(this.dataView, this.searchInput.val(), this.interactivityService);
                    if (!data) {
                        this.tableView.empty();
                        return;
                    }
                    if (this.interactivityService) {
                        this.interactivityService.applySelectionStateToData(data.slicerDataPoints);
                    }
                    data.slicerSettings.header.outlineWeight = data.slicerSettings.header.outlineWeight < 0
                        ? 0
                        : data.slicerSettings.header.outlineWeight;
                    data.slicerSettings.slicerText.outlineWeight = data.slicerSettings.slicerText.outlineWeight < 0
                        ? 0
                        : data.slicerSettings.slicerText.outlineWeight;
                    data.slicerSettings.slicerText.padding = data.slicerSettings.slicerText.padding < 0
                        ? 0
                        : data.slicerSettings.slicerText.padding;
                    data.slicerSettings.slicerText.padding = data.slicerSettings.slicerText.padding > ChicletSlicer.MaxCellPadding
                        ? ChicletSlicer.MaxCellPadding
                        : data.slicerSettings.slicerText.padding;
                    data.slicerSettings.slicerText.height = data.slicerSettings.slicerText.height < 0
                        ? 0
                        : data.slicerSettings.slicerText.height;
                    data.slicerSettings.slicerText.width = data.slicerSettings.slicerText.width < 0
                        ? 0
                        : data.slicerSettings.slicerText.width;
                    data.slicerSettings.images.imageSplit = ChicletSlicer.getValidImageSplit(data.slicerSettings.images.imageSplit);
                    data.slicerSettings.general.columns = data.slicerSettings.general.columns < 0
                        ? 0
                        : data.slicerSettings.general.columns;
                    data.slicerSettings.general.rows = data.slicerSettings.general.rows < 0
                        ? 0
                        : data.slicerSettings.general.rows;
                    data.slicerSettings.general.getSavedSelection = function () {
                        try {
                            return JSON.parse(_this.slicerData.slicerSettings.general.selection) || [];
                        }
                        catch (ex) {
                            return [];
                        }
                    };
                    data.slicerSettings.general.setSavedSelection = function (filter, selectionIds) {
                        _this.isSelectionSaved = true;
                        _this.hostServices.persistProperties({
                            merge: [{
                                    objectName: "general",
                                    selector: null,
                                    properties: {
                                        filter: filter || null,
                                        selection: selectionIds && JSON.stringify(selectionIds) || ""
                                    }
                                }]
                        });
                    };
                    if (this.slicerData) {
                        if (this.isSelectionSaved) {
                            this.isSelectionLoaded = true;
                        }
                        else {
                            this.isSelectionLoaded = this.slicerData.slicerSettings.general.selection === data.slicerSettings.general.selection;
                        }
                    }
                    else {
                        this.isSelectionLoaded = false;
                    }
                    this.slicerData = data;
                    this.settings = this.slicerData.slicerSettings;
                    this.updateSlicerBodyDimensions();
                    if (this.settings.general.showDisabled === ChicletSlicerShowDisabled.BOTTOM) {
                        data.slicerDataPoints.sort(function (a, b) {
                            if (a.selectable === b.selectable) {
                                return 0;
                            }
                            else if (a.selectable && !b.selectable) {
                                return -1;
                            }
                            else {
                                return 1;
                            }
                        });
                    }
                    else if (this.settings.general.showDisabled === ChicletSlicerShowDisabled.HIDE) {
                        data.slicerDataPoints = data.slicerDataPoints.filter(function (x) { return x.selectable; });
                    }
                    var height = this.settings.slicerText.height;
                    if (height === 0) {
                        var extraSpaceForCell = ChicletSlicer.cellTotalInnerPaddings + ChicletSlicer.cellTotalInnerBorders, textProperties = ChicletSlicer.getChicletTextProperties(this.settings.slicerText.textSize);
                        height = TextMeasurementService.estimateSvgTextHeight(textProperties) +
                            TextMeasurementService.estimateSvgTextBaselineDelta(textProperties) +
                            extraSpaceForCell;
                        var hasImage = _.any(data.slicerDataPoints, function (dataPoint) {
                            return dataPoint.imageURL !== '' && typeof dataPoint.imageURL !== "undefined";
                        });
                        if (hasImage) {
                            height += 100;
                        }
                    }
                    this.tableView
                        .rowHeight(height)
                        .columnWidth(this.settings.slicerText.width)
                        .orientation(this.settings.general.orientation)
                        .rows(this.settings.general.rows)
                        .columns(this.settings.general.columns)
                        .data(data.slicerDataPoints.filter(function (x) { return !x.filtered; }), function (d) { return $.inArray(d, data.slicerDataPoints); }, resetScrollbarPosition)
                        .viewport(this.getSlicerBodyViewport(this.currentViewport))
                        .render();
                    this.updateSearchHeader();
                };
                ChicletSlicer.prototype.initContainer = function () {
                    var _this = this;
                    var settings = this.settings, slicerBodyViewport = this.getSlicerBodyViewport(this.currentViewport);
                    var slicerContainer = d3.select(this.element.get(0))
                        .append('div')
                        .classed(ChicletSlicer.ContainerSelector.class, true);
                    this.slicerHeader = slicerContainer
                        .append('div')
                        .classed(ChicletSlicer.HeaderSelector.class, true);
                    this.slicerHeader
                        .append('span')
                        .classed(ChicletSlicer.ClearSelector.class, true)
                        .attr('title', 'Clear');
                    this.slicerHeader
                        .append('div')
                        .classed(ChicletSlicer.HeaderTextSelector.class, true)
                        .style({
                        'margin-left': PixelConverter.toString(settings.headerText.marginLeft),
                        'margin-top': PixelConverter.toString(settings.headerText.marginTop),
                        'border-style': this.getBorderStyle(settings.header.outline),
                        'border-color': settings.header.outlineColor,
                        'border-width': this.getBorderWidth(settings.header.outline, settings.header.outlineWeight),
                        'font-size': PixelConverter.fromPoint(settings.header.textSize),
                    });
                    this.createSearchHeader($(slicerContainer.node()));
                    this.slicerBody = slicerContainer
                        .append('div')
                        .classed(ChicletSlicer.BodySelector.class, true)
                        .classed(ChicletSlicer.SlicerBodyHorizontalSelector.class, settings.general.orientation === Orientation.HORIZONTAL)
                        .classed(ChicletSlicer.SlicerBodyVerticalSelector.class, settings.general.orientation === Orientation.VERTICAL)
                        .style({
                        'height': PixelConverter.toString(slicerBodyViewport.height),
                        'width': '100%',
                    });
                    var rowEnter = function (rowSelection) {
                        _this.enterSelection(rowSelection);
                    };
                    var rowUpdate = function (rowSelection) {
                        _this.updateSelection(rowSelection);
                    };
                    var rowExit = function (rowSelection) {
                        rowSelection.remove();
                    };
                    var tableViewOptions = {
                        rowHeight: this.getRowHeight(),
                        columnWidth: this.settings.slicerText.width,
                        orientation: this.settings.general.orientation,
                        rows: this.settings.general.rows,
                        columns: this.settings.general.columns,
                        enter: rowEnter,
                        exit: rowExit,
                        update: rowUpdate,
                        loadMoreData: function () { return _this.onLoadMoreData(); },
                        scrollEnabled: true,
                        viewport: this.getSlicerBodyViewport(this.currentViewport),
                        baseContainer: this.slicerBody,
                    };
                    this.tableView = TableViewFactory.createTableView(tableViewOptions);
                };
                ChicletSlicer.prototype.enterSelection = function (rowSelection) {
                    var settings = this.settings;
                    var ulItemElement = rowSelection
                        .selectAll('ul')
                        .data(function (dataPoint) {
                        return [dataPoint];
                    });
                    ulItemElement
                        .enter()
                        .append('ul');
                    ulItemElement
                        .exit()
                        .remove();
                    var listItemElement = ulItemElement
                        .selectAll(ChicletSlicer.ItemContainerSelector.selector)
                        .data(function (dataPoint) {
                        return [dataPoint];
                    });
                    listItemElement
                        .enter()
                        .append('li')
                        .classed(ChicletSlicer.ItemContainerSelector.class, true);
                    listItemElement.style({
                        'margin-left': PixelConverter.toString(settings.slicerItemContainer.marginLeft)
                    });
                    var slicerImgWrapperSelection = listItemElement
                        .selectAll(ChicletSlicer.SlicerImgWrapperSelector.selector)
                        .data(function (dataPoint) {
                        return [dataPoint];
                    });
                    slicerImgWrapperSelection
                        .enter()
                        .append('img')
                        .classed(ChicletSlicer.SlicerImgWrapperSelector.class, true);
                    slicerImgWrapperSelection
                        .exit()
                        .remove();
                    var slicerTextWrapperSelection = listItemElement
                        .selectAll(ChicletSlicer.SlicerTextWrapperSelector.selector)
                        .data(function (dataPoint) {
                        return [dataPoint];
                    });
                    slicerTextWrapperSelection
                        .enter()
                        .append('div')
                        .classed(ChicletSlicer.SlicerTextWrapperSelector.class, true);
                    var labelTextSelection = slicerTextWrapperSelection
                        .selectAll(ChicletSlicer.LabelTextSelector.selector)
                        .data(function (dataPoint) {
                        return [dataPoint];
                    });
                    labelTextSelection
                        .enter()
                        .append('span')
                        .classed(ChicletSlicer.LabelTextSelector.class, true);
                    labelTextSelection.style({
                        'font-size': PixelConverter.fromPoint(settings.slicerText.textSize),
                    });
                    labelTextSelection
                        .exit()
                        .remove();
                    slicerTextWrapperSelection
                        .exit()
                        .remove();
                    listItemElement
                        .exit()
                        .remove();
                };
                ;
                ChicletSlicer.prototype.updateSelection = function (rowSelection) {
                    var _this = this;
                    var settings = this.settings, data = this.slicerData;
                    if (data && settings) {
                        this.slicerHeader
                            .classed('hidden', !settings.header.show);
                        this.slicerHeader
                            .select(ChicletSlicer.HeaderTextSelector.selector)
                            .text(settings.header.title.trim() !== ""
                            ? settings.header.title.trim()
                            : this.slicerData.categorySourceName)
                            .style({
                            'border-style': this.getBorderStyle(settings.header.outline),
                            'border-color': settings.header.outlineColor,
                            'border-width': this.getBorderWidth(settings.header.outline, settings.header.outlineWeight),
                            'color': settings.header.fontColor,
                            'background-color': settings.header.background,
                            'font-size': PixelConverter.fromPoint(settings.header.textSize),
                        });
                        this.slicerBody
                            .classed(ChicletSlicer.SlicerBodyHorizontalSelector.class, settings.general.orientation === Orientation.HORIZONTAL)
                            .classed(ChicletSlicer.SlicerBodyVerticalSelector.class, settings.general.orientation === Orientation.VERTICAL);
                        var slicerText = rowSelection.selectAll(ChicletSlicer.LabelTextSelector.selector), textProperties = ChicletSlicer.getChicletTextProperties(settings.slicerText.textSize), formatString = data.formatString;
                        slicerText.text(function (d) {
                            var maxWidth = 0;
                            textProperties.text = valueFormatter.format(d.category, formatString);
                            if (_this.settings.slicerText.width === 0) {
                                var slicerBodyViewport = _this.getSlicerBodyViewport(_this.currentViewport);
                                maxWidth = (slicerBodyViewport.width / (_this.tableView.computedColumns || 1)) -
                                    ChicletSlicer.chicletTotalInnerRightLeftPaddings -
                                    ChicletSlicer.cellTotalInnerBorders -
                                    settings.slicerText.outlineWeight;
                                return TextMeasurementService.getTailoredTextOrDefault(textProperties, maxWidth);
                            }
                            else {
                                maxWidth = _this.settings.slicerText.width -
                                    ChicletSlicer.chicletTotalInnerRightLeftPaddings -
                                    ChicletSlicer.cellTotalInnerBorders -
                                    settings.slicerText.outlineWeight;
                                return TextMeasurementService.getTailoredTextOrDefault(textProperties, maxWidth);
                            }
                        });
                        rowSelection
                            .style({
                            'padding': PixelConverter.toString(settings.slicerText.padding)
                        });
                        rowSelection
                            .selectAll(ChicletSlicer.SlicerImgWrapperSelector.selector)
                            .style({
                            'max-height': settings.images.imageSplit + '%',
                            'display': function (dataPoint) { return (dataPoint.imageURL)
                                ? 'flex'
                                : 'none'; }
                        })
                            .classed({
                            'hidden': function (dataPoint) {
                                if (!(dataPoint.imageURL)) {
                                    return true;
                                }
                                if (settings.images.imageSplit < 10) {
                                    return true;
                                }
                            },
                            'stretchImage': settings.images.stretchImage,
                            'bottomImage': settings.images.bottomImage
                        })
                            .attr('src', function (d) {
                            return d.imageURL ? d.imageURL : '';
                        });
                        rowSelection.selectAll('.slicer-text-wrapper')
                            .style('height', function (d) {
                            return d.imageURL
                                ? (100 - settings.images.imageSplit) + '%'
                                : '100%';
                        })
                            .classed('hidden', function (d) {
                            if (settings.images.imageSplit > 90) {
                                return true;
                            }
                        });
                        rowSelection.selectAll('.slicerItemContainer').style({
                            'color': settings.slicerText.fontColor,
                            'border-style': this.getBorderStyle(settings.slicerText.outline),
                            'border-color': settings.slicerText.outlineColor,
                            'border-width': this.getBorderWidth(settings.slicerText.outline, settings.slicerText.outlineWeight),
                            'font-size': PixelConverter.fromPoint(settings.slicerText.textSize),
                            'border-radius': this.getBorderRadius(settings.slicerText.borderStyle)
                        });
                        if (settings.slicerText.background) {
                            var backgroundColor = explore.util.hexToRGBString(settings.slicerText.background, (100 - settings.slicerText.transparency) / 100);
                            this.slicerBody.style('background-color', backgroundColor);
                        }
                        else {
                            this.slicerBody.style('background-color', null);
                        }
                        if (this.interactivityService && this.slicerBody) {
                            this.interactivityService.applySelectionStateToData(data.slicerDataPoints);
                            var slicerBody = this.slicerBody.attr('width', this.currentViewport.width), slicerItemContainers = slicerBody.selectAll(ChicletSlicer.ItemContainerSelector.selector), slicerItemLabels = slicerBody.selectAll(ChicletSlicer.LabelTextSelector.selector), slicerItemInputs = slicerBody.selectAll(ChicletSlicer.InputSelector.selector), slicerClear = this.slicerHeader.select(ChicletSlicer.ClearSelector.selector);
                            var behaviorOptions = {
                                dataPoints: data.slicerDataPoints,
                                slicerItemContainers: slicerItemContainers,
                                slicerItemLabels: slicerItemLabels,
                                slicerItemInputs: slicerItemInputs,
                                slicerClear: slicerClear,
                                interactivityService: this.interactivityService,
                                slicerSettings: data.slicerSettings,
                                isSelectionLoaded: this.isSelectionLoaded,
                                identityFields: data.identityFields
                            };
                            this.interactivityService.bind(data.slicerDataPoints, this.behavior, behaviorOptions, {
                                overrideSelectionFromData: true,
                                hasSelectionOverride: data.hasSelectionOverride,
                            });
                            this.behavior.styleSlicerInputs(rowSelection.select(ChicletSlicer.ItemContainerSelector.selector), this.interactivityService.hasSelection());
                        }
                        else {
                            this.behavior.styleSlicerInputs(rowSelection.select(ChicletSlicer.ItemContainerSelector.selector), false);
                        }
                    }
                };
                ;
                ChicletSlicer.prototype.createSearchHeader = function (container) {
                    var _this = this;
                    this.searchHeader = $("<div>")
                        .appendTo(container)
                        .addClass("searchHeader")
                        .addClass("collapsed");
                    $("<div>").appendTo(this.searchHeader)
                        .attr("title", "Search")
                        .addClass("search");
                    var counter = 0;
                    this.searchInput = $("<input>").appendTo(this.searchHeader)
                        .attr("type", "text")
                        .attr("drag-resize-disabled", "true")
                        .addClass("searchInput")
                        .on("input", function () { return _this.hostServices.persistProperties({
                        merge: [{
                                objectName: "general",
                                selector: null,
                                properties: {
                                    counter: counter++
                                }
                            }]
                    }); });
                };
                ChicletSlicer.prototype.updateSearchHeader = function () {
                    this.searchHeader.toggleClass("show", this.slicerData.slicerSettings.general.selfFilterEnabled);
                    this.searchHeader.toggleClass("collapsed", !this.slicerData.slicerSettings.general.selfFilterEnabled);
                };
                ChicletSlicer.prototype.onLoadMoreData = function () {
                    if (!this.waitingForData && this.dataView.metadata && this.dataView.metadata.segment) {
                        this.hostServices.loadMoreData();
                        this.waitingForData = true;
                    }
                };
                ChicletSlicer.prototype.getSlicerBodyViewport = function (currentViewport) {
                    var settings = this.settings, headerHeight = (settings.header.show) ? this.getHeaderHeight() : 0, borderHeight = settings.header.outlineWeight, height = currentViewport.height - (headerHeight + borderHeight + settings.header.borderBottomWidth), width = currentViewport.width - ChicletSlicer.WidthOfScrollbar;
                    return {
                        height: Math.max(height, ChicletSlicer.MinSizeOfViewport),
                        width: Math.max(width, ChicletSlicer.MinSizeOfViewport)
                    };
                };
                ChicletSlicer.prototype.updateSlicerBodyDimensions = function () {
                    var slicerViewport = this.getSlicerBodyViewport(this.currentViewport);
                    this.slicerBody
                        .style({
                        'height': PixelConverter.toString(slicerViewport.height),
                        'width': '100%',
                    });
                };
                ChicletSlicer.getChicletTextProperties = function (textSize) {
                    return {
                        fontFamily: ChicletSlicer.DefaultFontFamily,
                        fontSize: PixelConverter.fromPoint(textSize || ChicletSlicer.DefaultFontSizeInPt),
                    };
                };
                ChicletSlicer.prototype.getHeaderHeight = function () {
                    return TextMeasurementService.estimateSvgTextHeight(ChicletSlicer.getChicletTextProperties(this.settings.header.textSize));
                };
                ChicletSlicer.prototype.getRowHeight = function () {
                    var textSettings = this.settings.slicerText;
                    return textSettings.height !== 0
                        ? textSettings.height
                        : TextMeasurementService.estimateSvgTextHeight(ChicletSlicer.getChicletTextProperties(textSettings.textSize));
                };
                ChicletSlicer.prototype.getBorderStyle = function (outlineElement) {
                    return outlineElement === '0px' ? 'none' : 'solid';
                };
                ChicletSlicer.prototype.getBorderWidth = function (outlineElement, outlineWeight) {
                    switch (outlineElement) {
                        case 'None':
                            return '0px';
                        case 'BottomOnly':
                            return '0px 0px ' + outlineWeight + 'px 0px';
                        case 'TopOnly':
                            return outlineWeight + 'px 0px 0px 0px';
                        case 'TopBottom':
                            return outlineWeight + 'px 0px ' + outlineWeight + 'px 0px';
                        case 'LeftRight':
                            return '0px ' + outlineWeight + 'px 0px ' + outlineWeight + 'px';
                        case 'Frame':
                            return outlineWeight + 'px';
                        default:
                            return outlineElement.replace("1", outlineWeight.toString());
                    }
                };
                ChicletSlicer.prototype.getBorderRadius = function (borderType) {
                    switch (borderType) {
                        case ChicletBorderStyle.ROUNDED:
                            return "10px";
                        case ChicletBorderStyle.SQUARE:
                            return "0px";
                        default:
                            return "5px";
                    }
                };
                ChicletSlicer.capabilities = {
                    dataRoles: [
                        {
                            name: 'Category',
                            kind: VisualDataRoleKind.Grouping,
                            displayName: 'Category',
                        },
                        {
                            name: 'Values',
                            kind: VisualDataRoleKind.Measure,
                            displayName: 'Values',
                        },
                        {
                            name: 'Image',
                            kind: VisualDataRoleKind.Grouping,
                            displayName: 'Image',
                        },
                    ],
                    objects: {
                        general: {
                            displayName: 'General',
                            properties: {
                                selection: {
                                    displayName: "Selection",
                                    type: { text: true }
                                },
                                orientation: {
                                    displayName: 'Orientation',
                                    type: { enumeration: Orientation.type }
                                },
                                columns: {
                                    displayName: 'Columns',
                                    type: { numeric: true }
                                },
                                rows: {
                                    displayName: 'Rows',
                                    type: { numeric: true }
                                },
                                showDisabled: {
                                    displayName: 'Show Disabled',
                                    type: { enumeration: ChicletSlicerShowDisabled.type }
                                },
                                multiselect: {
                                    displayName: 'Multiple selection',
                                    type: { bool: true }
                                },
                                forcedSelection: {
                                    displayName: 'Forced selection',
                                    type: { bool: true }
                                },
                                selected: {
                                    type: { bool: true }
                                },
                                filter: {
                                    type: { filter: {} }
                                },
                                selfFilter: {
                                    type: { filter: { selfFilter: true } }
                                },
                                selfFilterEnabled: {
                                    type: { operations: { searchEnabled: true } }
                                },
                                formatString: {
                                    type: { formatting: { formatString: true } }
                                },
                            },
                        },
                        header: {
                            displayName: 'Header',
                            properties: {
                                show: {
                                    displayName: 'Show',
                                    type: { bool: true }
                                },
                                title: {
                                    displayName: 'Title',
                                    type: { text: true }
                                },
                                fontColor: {
                                    displayName: 'Font color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                background: {
                                    displayName: 'Background',
                                    type: { fill: { solid: { color: true } } }
                                },
                                outline: {
                                    displayName: 'Outline',
                                    type: { formatting: { outline: true } }
                                },
                                textSize: {
                                    displayName: 'Text Size',
                                    type: { numeric: true }
                                },
                                outlineColor: {
                                    displayName: 'Outline Color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                outlineWeight: {
                                    displayName: 'Outline Weight',
                                    type: { numeric: true }
                                }
                            }
                        },
                        rows: {
                            displayName: 'Chiclets',
                            properties: {
                                fontColor: {
                                    displayName: 'Text color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                textSize: {
                                    displayName: 'Text Size',
                                    type: { numeric: true }
                                },
                                height: {
                                    displayName: 'Height',
                                    type: { numeric: true }
                                },
                                width: {
                                    displayName: 'Width',
                                    type: { numeric: true }
                                },
                                selectedColor: {
                                    displayName: 'Selected Color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                hoverColor: {
                                    displayName: 'Hover Color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                unselectedColor: {
                                    displayName: 'Unselected Color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                disabledColor: {
                                    displayName: 'Disabled Color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                background: {
                                    displayName: 'Background',
                                    type: { fill: { solid: { color: true } } }
                                },
                                transparency: {
                                    displayName: "Transparency",
                                    description: "Set transparency for background color",
                                    type: { numeric: true }
                                },
                                outline: {
                                    displayName: 'Outline',
                                    type: { formatting: { outline: true } }
                                },
                                outlineColor: {
                                    displayName: 'Outline Color',
                                    type: { fill: { solid: { color: true } } }
                                },
                                outlineWeight: {
                                    displayName: 'Outline Weight',
                                    type: { numeric: true }
                                },
                                borderStyle: {
                                    displayName: 'Outline Style',
                                    type: { enumeration: ChicletBorderStyle.type }
                                },
                                padding: {
                                    displayName: 'Padding',
                                    type: { numeric: true }
                                },
                            }
                        },
                        images: {
                            displayName: 'Images',
                            properties: {
                                imageSplit: {
                                    displayName: 'Image Split',
                                    type: { numeric: true }
                                },
                                stretchImage: {
                                    displayName: 'Stretch image',
                                    type: { bool: true }
                                },
                                bottomImage: {
                                    displayName: 'Bottom image',
                                    type: { bool: true }
                                },
                            }
                        },
                    },
                    dataViewMappings: [{
                            conditions: [
                                {
                                    'Category': { max: 1 },
                                    'Image': { min: 0, max: 1 },
                                    'Values': { min: 0, max: 1 }
                                }
                            ],
                            categorical: {
                                categories: {
                                    for: { in: 'Category' },
                                    dataReductionAlgorithm: { top: { count: 10000 } }
                                },
                                values: {
                                    group: {
                                        by: 'Image',
                                        select: [{ bind: { to: 'Values' } }],
                                        dataReductionAlgorithm: { top: { count: 10000 } }
                                    }
                                },
                                includeEmptyGroups: true
                            }
                        }],
                    supportsHighlight: true,
                    sorting: {
                        default: {},
                    },
                    suppressDefaultTitle: true,
                };
                ChicletSlicer.DefaultFontFamily = "'Segoe UI', 'wf_segoe-ui_normal', helvetica, arial, sans-serif";
                ChicletSlicer.DefaultFontSizeInPt = 11;
                ChicletSlicer.cellTotalInnerPaddings = 8;
                ChicletSlicer.cellTotalInnerBorders = 2;
                ChicletSlicer.chicletTotalInnerRightLeftPaddings = 14;
                ChicletSlicer.MinImageSplit = 0;
                ChicletSlicer.MaxImageSplit = 100;
                ChicletSlicer.MaxCellPadding = 20;
                ChicletSlicer.MinSizeOfViewport = 0;
                ChicletSlicer.WidthOfScrollbar = 17;
                ChicletSlicer.ItemContainerSelector = createClassAndSelector('slicerItemContainer');
                ChicletSlicer.SlicerImgWrapperSelector = createClassAndSelector('slicer-img-wrapper');
                ChicletSlicer.SlicerTextWrapperSelector = createClassAndSelector('slicer-text-wrapper');
                ChicletSlicer.SlicerBodyHorizontalSelector = createClassAndSelector('slicerBody-horizontal');
                ChicletSlicer.SlicerBodyVerticalSelector = createClassAndSelector('slicerBody-vertical');
                ChicletSlicer.HeaderTextSelector = createClassAndSelector('headerText');
                ChicletSlicer.ContainerSelector = createClassAndSelector('chicletSlicer');
                ChicletSlicer.LabelTextSelector = createClassAndSelector('slicerText');
                ChicletSlicer.HeaderSelector = createClassAndSelector('slicerHeader');
                ChicletSlicer.InputSelector = createClassAndSelector('slicerCheckbox');
                ChicletSlicer.ClearSelector = createClassAndSelector('clear');
                ChicletSlicer.BodySelector = createClassAndSelector('slicerBody');
                return ChicletSlicer;
            }());
            ChicletSlicer1448559807354.ChicletSlicer = ChicletSlicer;
            var ChicletSlicerChartConversion;
            (function (ChicletSlicerChartConversion) {
                var ChicletSlicerConverter = (function () {
                    function ChicletSlicerConverter(dataView, interactivityService) {
                        var dataViewCategorical = dataView.categorical;
                        this.dataViewCategorical = dataViewCategorical;
                        this.dataViewMetadata = dataView.metadata;
                        if (dataViewCategorical.categories && dataViewCategorical.categories.length > 0) {
                            this.category = dataViewCategorical.categories[0];
                            this.categoryIdentities = this.category.identity;
                            this.categoryValues = this.category.values;
                            this.identityFields = this.category.identityFields;
                            this.categoryFormatString = valueFormatter.getFormatString(this.category.source, ChicletSlicer1448559807354.chicletSlicerProps.formatString);
                        }
                        this.dataPoints = [];
                        this.interactivityService = interactivityService;
                        this.hasSelectionOverride = false;
                    }
                    ChicletSlicerConverter.prototype.convert = function () {
                        this.dataPoints = [];
                        this.numberOfCategoriesSelectedInData = 0;
                        // If category exists, we render labels using category values. If not, we render labels
                        // using measure labels.
                        if (this.categoryValues) {
                            var objects = this.dataViewMetadata ? this.dataViewMetadata.objects : undefined;
                            var isInvertedSelectionMode = undefined;
                            var numberOfScopeIds;
                            if (objects && objects.general && objects.general.filter) {
                                if (!this.identityFields)
                                    return;
                                var filter = objects.general.filter;
                                var scopeIds = SQExprConverter.asScopeIdsContainer(filter, this.identityFields);
                                if (scopeIds) {
                                    isInvertedSelectionMode = scopeIds.isNot;
                                    numberOfScopeIds = scopeIds.scopeIds ? scopeIds.scopeIds.length : 0;
                                }
                                else {
                                    isInvertedSelectionMode = false;
                                }
                            }
                            if (this.interactivityService) {
                                if (isInvertedSelectionMode === undefined) {
                                    // The selection state is read from the Interactivity service in case of SelectAll or Clear when query doesn't update the visual
                                    isInvertedSelectionMode = this.interactivityService.isSelectionModeInverted();
                                }
                                else {
                                    this.interactivityService.setSelectionModeInverted(isInvertedSelectionMode);
                                }
                            }
                            var hasSelection = undefined;
                            for (var idx = 0; idx < this.categoryValues.length; idx++) {
                                var selected = isCategoryColumnSelected(ChicletSlicer1448559807354.chicletSlicerProps.selectedPropertyIdentifier, this.category, idx);
                                if (selected != null) {
                                    hasSelection = selected;
                                    break;
                                }
                            }
                            var dataViewCategorical = this.dataViewCategorical;
                            var formatStringProp = ChicletSlicer1448559807354.chicletSlicerProps.formatString;
                            var value = -Infinity;
                            var imageURL = '';
                            for (var categoryIndex = 0, categoryCount = this.categoryValues.length; categoryIndex < categoryCount; categoryIndex++) {
                                //var categoryIdentity = this.category.identity ? this.category.identity[categoryIndex] : null;
                                var categoryIsSelected = isCategoryColumnSelected(ChicletSlicer1448559807354.chicletSlicerProps.selectedPropertyIdentifier, this.category, categoryIndex);
                                var selectable = true;
                                if (hasSelection != null) {
                                    if (isInvertedSelectionMode) {
                                        if (this.category.objects == null)
                                            categoryIsSelected = undefined;
                                        if (categoryIsSelected != null) {
                                            categoryIsSelected = hasSelection;
                                        }
                                        else if (categoryIsSelected == null)
                                            categoryIsSelected = !hasSelection;
                                    }
                                    else {
                                        if (categoryIsSelected == null) {
                                            categoryIsSelected = !hasSelection;
                                        }
                                    }
                                }
                                if (categoryIsSelected) {
                                    this.numberOfCategoriesSelectedInData++;
                                }
                                var categoryValue = this.categoryValues[categoryIndex];
                                var categoryLabel = valueFormatter.format(categoryValue, this.categoryFormatString);
                                if (this.dataViewCategorical.values) {
                                    // Series are either measures in the multi-measure case, or the single series otherwise
                                    for (var seriesIndex = 0; seriesIndex < this.dataViewCategorical.values.length; seriesIndex++) {
                                        var seriesData = dataViewCategorical.values[seriesIndex];
                                        if (seriesData.values[categoryIndex] != null) {
                                            value = seriesData.values[categoryIndex];
                                            if (seriesData.highlights) {
                                                selectable = !(seriesData.highlights[categoryIndex] === null);
                                            }
                                            if (seriesData.source.groupName && seriesData.source.groupName !== '') {
                                                imageURL = converterHelper.getFormattedLegendLabel(seriesData.source, dataViewCategorical.values, formatStringProp);
                                                if (!/^(ftp|http|https):\/\/[^ "]+$/.test(imageURL)) {
                                                    imageURL = undefined;
                                                }
                                            }
                                        }
                                    }
                                }
                                var categorySelectionId = SelectionIdBuilder.builder().withCategory(this.category, categoryIndex).createSelectionId();
                                this.dataPoints.push({
                                    identity: categorySelectionId,
                                    category: categoryLabel,
                                    imageURL: imageURL,
                                    value: value,
                                    selected: categoryIsSelected,
                                    selectable: selectable
                                });
                            }
                            if (numberOfScopeIds != null && numberOfScopeIds > this.numberOfCategoriesSelectedInData) {
                                this.hasSelectionOverride = true;
                            }
                        }
                    };
                    return ChicletSlicerConverter;
                }());
                ChicletSlicerChartConversion.ChicletSlicerConverter = ChicletSlicerConverter;
            })(ChicletSlicerChartConversion || (ChicletSlicerChartConversion = {}));
            //TODO: This module should be removed once TextMeasruementService exports the "estimateSvgTextBaselineDelta" function.
            var ChicletSlicerTextMeasurementHelper;
            (function (ChicletSlicerTextMeasurementHelper) {
                var spanElement;
                var svgTextElement;
                var canvasCtx;
                function estimateSvgTextBaselineDelta(textProperties) {
                    var rect = estimateSvgTextRect(textProperties);
                    return rect.y + rect.height;
                }
                ChicletSlicerTextMeasurementHelper.estimateSvgTextBaselineDelta = estimateSvgTextBaselineDelta;
                function ensureDOM() {
                    if (spanElement)
                        return;
                    spanElement = $('<span/>');
                    $('body').append(spanElement);
                    //The style hides the svg element from the canvas, preventing canvas from scrolling down to show svg black square.
                    svgTextElement = d3.select($('body').get(0))
                        .append('svg')
                        .style({
                        'height': '0px',
                        'width': '0px',
                        'position': 'absolute'
                    })
                        .append('text');
                    canvasCtx = $('<canvas/>').get(0).getContext("2d");
                }
                function measureSvgTextRect(textProperties) {
                    debug.assertValue(textProperties, 'textProperties');
                    ensureDOM();
                    svgTextElement.style(null);
                    svgTextElement
                        .text(textProperties.text)
                        .attr({
                        'visibility': 'hidden',
                        'font-family': textProperties.fontFamily,
                        'font-size': textProperties.fontSize,
                        'font-weight': textProperties.fontWeight,
                        'font-style': textProperties.fontStyle,
                        'white-space': textProperties.whiteSpace || 'nowrap'
                    });
                    // We're expecting the browser to give a synchronous measurement here
                    // We're using SVGTextElement because it works across all browsers
                    return svgTextElement.node().getBBox();
                }
                function estimateSvgTextRect(textProperties) {
                    debug.assertValue(textProperties, 'textProperties');
                    var estimatedTextProperties = {
                        fontFamily: textProperties.fontFamily,
                        fontSize: textProperties.fontSize,
                        text: "M",
                    };
                    var rect = measureSvgTextRect(estimatedTextProperties);
                    return rect;
                }
            })(ChicletSlicerTextMeasurementHelper = ChicletSlicer1448559807354.ChicletSlicerTextMeasurementHelper || (ChicletSlicer1448559807354.ChicletSlicerTextMeasurementHelper = {}));
            var ChicletSlicerWebBehavior = (function () {
                function ChicletSlicerWebBehavior() {
                }
                ChicletSlicerWebBehavior.prototype.bindEvents = function (options, selectionHandler) {
                    var _this = this;
                    var slicers = this.slicers = options.slicerItemContainers;
                    this.slicerItemLabels = options.slicerItemLabels;
                    this.slicerItemInputs = options.slicerItemInputs;
                    var slicerClear = options.slicerClear;
                    this.dataPoints = options.dataPoints;
                    this.interactivityService = options.interactivityService;
                    this.slicerSettings = options.slicerSettings;
                    this.options = options;
                    if (!this.options.isSelectionLoaded) {
                        this.loadSelection(selectionHandler);
                    }
                    slicers.on("mouseover", function (d) {
                        if (d.selectable) {
                            d.mouseOver = true;
                            d.mouseOut = false;
                            _this.renderMouseover();
                        }
                    });
                    slicers.on("mouseout", function (d) {
                        if (d.selectable) {
                            d.mouseOver = false;
                            d.mouseOut = true;
                            _this.renderMouseover();
                        }
                    });
                    slicers.on("click", function (dataPoint, index) {
                        if (!dataPoint.selectable) {
                            return;
                        }
                        d3.event.preventDefault();
                        var settings = _this.slicerSettings;
                        var selectedIndexes = jQuery.map(_this.dataPoints, function (dataPoint, index) {
                            if (dataPoint.selected) {
                                return index;
                            }
                            ;
                        });
                        if (settings.general.forcedSelection && selectedIndexes.length === 1) {
                            var availableDataPoints = jQuery.map(_this.dataPoints, function (dataPoint, index) {
                                if (!dataPoint.filtered) {
                                    return dataPoint;
                                }
                                ;
                            });
                            if (availableDataPoints[index]
                                && _this.dataPoints[selectedIndexes[0]].identity === availableDataPoints[index].identity) {
                                return;
                            }
                        }
                        if (d3.event.altKey && settings.general.multiselect) {
                            var selIndex = selectedIndexes.length > 0
                                ? (selectedIndexes[selectedIndexes.length - 1])
                                : 0;
                            if (selIndex > index) {
                                var temp = index;
                                index = selIndex;
                                selIndex = temp;
                            }
                            selectionHandler.handleClearSelection();
                            for (var i = selIndex; i <= index; i++) {
                                selectionHandler.handleSelection(_this.dataPoints[i], true /* isMultiSelect */);
                            }
                        }
                        else if ((d3.event.ctrlKey || d3.event.metaKey) && settings.general.multiselect) {
                            selectionHandler.handleSelection(dataPoint, true /* isMultiSelect */);
                        }
                        else {
                            selectionHandler.handleSelection(dataPoint, false /* isMultiSelect */);
                        }
                        _this.saveSelection(selectionHandler);
                    });
                    slicerClear.on("click", function (d) {
                        selectionHandler.handleClearSelection();
                        _this.saveSelection(selectionHandler);
                    });
                    this.forceSelection(selectionHandler);
                };
                ChicletSlicerWebBehavior.prototype.forceSelection = function (selectionHandler) {
                    if (!this.slicerSettings.general.forcedSelection) {
                        return;
                    }
                    var selectedIndexes = jQuery.map(this.dataPoints, function (dataPoint, index) {
                        if (dataPoint.selected) {
                            return index;
                        }
                        ;
                    });
                    if (selectedIndexes.length === 0) {
                        for (var i = 0; i < this.dataPoints.length; i++) {
                            var dataPoint = this.dataPoints[i];
                            if (dataPoint.selectable && !dataPoint.filtered) {
                                selectionHandler.handleSelection(dataPoint, false);
                                this.saveSelection(selectionHandler);
                                break;
                            }
                        }
                    }
                };
                ChicletSlicerWebBehavior.prototype.loadSelection = function (selectionHandler) {
                    selectionHandler.handleClearSelection();
                    var savedSelectionIds = this.slicerSettings.general.getSavedSelection();
                    if (savedSelectionIds.length) {
                        var selectedDataPoints = this.dataPoints.filter(function (d) { return savedSelectionIds.some(function (x) { return d.identity.getKey() === x; }); });
                        selectedDataPoints.forEach(function (x) { return selectionHandler.handleSelection(x, true); });
                        selectionHandler.persistSelectionFilter(ChicletSlicer1448559807354.chicletSlicerProps.filterPropertyIdentifier);
                    }
                };
                ChicletSlicerWebBehavior.getFilterFromSelectors = function (selectedIds, isSelectionModeInverted, identityFields) {
                    var selectors = [], filter;
                    if (selectedIds.length > 0) {
                        selectors = _.chain(selectedIds)
                            .filter(function (value) { return value.hasIdentity(); })
                            .map(function (value) { return value.getSelector(); })
                            .value();
                    }
                    if (selectors.length) {
                        filter = Selector.filterFromSelector(selectors, isSelectionModeInverted);
                    }
                    else if (identityFields) {
                        filter = SemanticFilter.getAnyValueFilter(identityFields);
                    }
                    return filter;
                };
                ChicletSlicerWebBehavior.prototype.saveSelection = function (selectionHandler) {
                    var filter, selectedIds, selectionIdKeys, identityFields;
                    selectedIds = selectionHandler.selectedIds;
                    identityFields = this.options ? this.options.identityFields : [];
                    filter = ChicletSlicerWebBehavior.getFilterFromSelectors(selectedIds, this.interactivityService.isSelectionModeInverted(), identityFields);
                    selectionIdKeys = selectedIds.map(function (x) { return x.getKey(); });
                    this.slicerSettings.general.setSavedSelection(filter, selectionIdKeys);
                };
                ChicletSlicerWebBehavior.prototype.renderSelection = function (hasSelection) {
                    if (!hasSelection && !this.interactivityService.isSelectionModeInverted()) {
                        this.slicers.style('background', this.slicerSettings.slicerText.unselectedColor);
                    }
                    else {
                        this.styleSlicerInputs(this.slicers, hasSelection);
                    }
                };
                ChicletSlicerWebBehavior.prototype.renderMouseover = function () {
                    var _this = this;
                    this.slicerItemLabels.style({
                        'color': function (d) {
                            if (d.mouseOver)
                                return _this.slicerSettings.slicerText.hoverColor;
                            if (d.mouseOut) {
                                if (d.selected)
                                    return _this.slicerSettings.slicerText.fontColor;
                                else
                                    return _this.slicerSettings.slicerText.fontColor;
                            }
                        }
                    });
                };
                ChicletSlicerWebBehavior.prototype.styleSlicerInputs = function (slicers, hasSelection) {
                    var settings = this.slicerSettings;
                    var selectedItems = [];
                    slicers.each(function (d) {
                        // get selected items
                        if (d.selectable && d.selected) {
                            selectedItems.push(d);
                        }
                        d3.select(this).style({
                            'background': d.selectable ? (d.selected ? settings.slicerText.selectedColor : settings.slicerText.unselectedColor)
                                : settings.slicerText.disabledColor
                        });
                        d3.select(this).classed('slicerItem-disabled', !d.selectable);
                    });
                };
                return ChicletSlicerWebBehavior;
            }());
            ChicletSlicer1448559807354.ChicletSlicerWebBehavior = ChicletSlicerWebBehavior;
            var explore;
            (function (explore) {
                var util;
                (function (util) {
                    function hexToRGBString(hex, transparency) {
                        // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
                        var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
                        hex = hex.replace(shorthandRegex, function (m, r, g, b) {
                            return r + r + g + g + b + b;
                        });
                        // Hex format which return the format r-g-b
                        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
                        var rgb = result ? {
                            r: parseInt(result[1], 16),
                            g: parseInt(result[2], 16),
                            b: parseInt(result[3], 16)
                        } : null;
                        // Wrong input
                        if (rgb === null) {
                            return '';
                        }
                        if (!transparency && transparency !== 0) {
                            return "rgb(" + rgb.r + "," + rgb.g + "," + rgb.b + ")";
                        }
                        else {
                            return "rgba(" + rgb.r + "," + rgb.g + "," + rgb.b + "," + transparency + ")";
                        }
                    }
                    util.hexToRGBString = hexToRGBString;
                })(util = explore.util || (explore.util = {}));
            })(explore || (explore = {}));
        })(ChicletSlicer1448559807354 = visuals.ChicletSlicer1448559807354 || (visuals.ChicletSlicer1448559807354 = {}));
    })(visuals = powerbi.visuals || (powerbi.visuals = {}));
})(powerbi || (powerbi = {}));
var powerbi;
(function (powerbi) {
    var visuals;
    (function (visuals) {
        var plugins;
        (function (plugins) {
            plugins.ChicletSlicer1448559807354 = {
                name: 'ChicletSlicer1448559807354',
                class: 'ChicletSlicer1448559807354',
                capabilities: powerbi.visuals.ChicletSlicer1448559807354.ChicletSlicer.capabilities,
                custom: true,
                create: function () { return new powerbi.visuals.ChicletSlicer1448559807354.ChicletSlicer(); }
            };
        })(plugins = visuals.plugins || (visuals.plugins = {}));
    })(visuals = powerbi.visuals || (powerbi.visuals = {}));
})(powerbi || (powerbi = {}));
