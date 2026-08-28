import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: root

    width: 1536
    height: 980
    minimumWidth: 1120
    minimumHeight: 720
    visible: true
    color: "#FFFFFF"
    title: "Resolved Layers · Variant Inference — Computational Health Lab"

    readonly property color ink: "#101522"
    readonly property color secondary: "#566176"
    readonly property color blue: "#0B42E7"
    readonly property color rule: "#D8DEE8"
    readonly property color softRule: "#E8ECF2"
    readonly property int evidenceWidth: Math.max(398, Math.min(468, width * 0.305))

    FileDialog {
        id: sourceDialog
        title: "Open Source Dataset"
        nameFilters: ["CSV files (*.csv)", "All files (*)"]
        onAccepted: sourceController.openSource(selectedFile.toString())
    }

    Rectangle {
        id: appBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 70
        color: "#FFFFFF"
        border.width: 1
        border.color: root.rule

        Item {
            id: identityCrop
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.verticalCenter: parent.verticalCenter
            width: 176
            height: 55
            clip: true
            visible: sourceController.identityReferenceUrl !== ""

            Image {
                x: -10
                y: -4
                width: 1536
                height: 1024
                source: sourceController.identityReferenceUrl
                fillMode: Image.Stretch
                smooth: true
                mipmap: true
            }
        }

        Text {
            visible: !identityCrop.visible
            anchors.left: parent.left
            anchors.leftMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            text: "Computational\nHealth Lab"
            color: root.ink
            font.family: "Arial"
            font.pixelSize: 15
            lineHeight: 0.92
        }

        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: 214
            anchors.verticalCenter: parent.verticalCenter
            width: 1
            height: 38
            color: "#AEB6C3"
        }

        Text {
            anchors.left: parent.left
            anchors.leftMargin: 242
            anchors.verticalCenter: parent.verticalCenter
            text: "Resolved Layers"
            color: root.ink
            font.family: "Arial"
            font.pixelSize: 20
            font.weight: Font.Medium
        }

        ActionButton {
            id: archiveButton
            anchors.right: parent.right
            anchors.rightMargin: 28
            anchors.verticalCenter: parent.verticalCenter
            width: 126
            height: 38
            quiet: true
            text: "Run Archive"
            enabled: false
        }
    }

    Item {
        id: workspace
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: appBar.bottom
        anchors.bottom: parent.bottom

        Item {
            id: sourceDesk
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width - root.evidenceWidth

            Text {
                id: pageTitle
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.top: parent.top
                anchors.topMargin: 25
                text: "Source Review"
                color: root.ink
                font.family: "Arial"
                font.pixelSize: 28
                font.weight: Font.Medium
            }

            Item {
                anchors.left: pageTitle.right
                anchors.leftMargin: 20
                anchors.verticalCenter: pageTitle.verticalCenter
                width: statusLabel.implicitWidth + 24
                height: 24

                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    color: sourceController.statusKind === "success" ? "#14AE62" : sourceController.statusKind === "error" ? "#CC3B32" : sourceController.statusKind === "warning" ? "#D58A00" : "#A3ACB9"
                }

                Text {
                    id: statusLabel
                    anchors.left: parent.left
                    anchors.leftMargin: 21
                    anchors.verticalCenter: parent.verticalCenter
                    text: sourceController.statusMessage
                    color: root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                    elide: Text.ElideRight
                    width: Math.min(implicitWidth, sourceDesk.width - pageTitle.width - 130)
                }
            }

            Rectangle {
                id: sourceCard
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.top: pageTitle.bottom
                anchors.topMargin: 24
                width: sourceController.hasSource ? 330 : 360
                height: 82
                color: "#FFFFFF"
                border.width: 1
                border.color: root.rule
                radius: 5

                Item {
                    anchors.left: parent.left
                    anchors.leftMargin: 16
                    anchors.verticalCenter: parent.verticalCenter
                    width: 42
                    height: 48

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.width: 2
                        border.color: "#697386"
                        radius: 2
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 5
                        text: "CSV"
                        color: "#263043"
                        font.family: "Arial"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }
                }

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 76
                    anchors.right: parent.right
                    anchors.rightMargin: 14
                    anchors.top: parent.top
                    anchors.topMargin: 17
                    text: sourceController.hasSource ? sourceController.fileName : "No Source Dataset open"
                    color: root.ink
                    elide: Text.ElideMiddle
                    font.family: "Arial"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 76
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 16
                    text: sourceController.hasSource ? sourceController.rowCount.toLocaleString() + " rows  ·  " + sourceController.columnCount.toLocaleString() + " columns" : "Open a CSV to review source evidence"
                    color: root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                }
            }

            Row {
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.verticalCenter: sourceCard.verticalCenter
                spacing: 12

                Rectangle {
                    visible: sourceController.hasSource
                    width: 220
                    height: 40
                    color: "#FFFFFF"
                    border.width: 1
                    border.color: columnSearch.activeFocus ? root.blue : root.rule
                    radius: 5

                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 14
                        anchors.verticalCenter: parent.verticalCenter
                        visible: !columnSearch.text
                        text: "Search columns…"
                        color: "#7B8493"
                        font.family: "Arial"
                        font.pixelSize: 13
                    }
                    TextInput {
                        id: columnSearch
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 12
                        verticalAlignment: TextInput.AlignVCenter
                        color: root.ink
                        selectByMouse: true
                        clip: true
                        font.family: "Arial"
                        font.pixelSize: 13
                        onTextChanged: sourceController.filterColumns(text)
                    }
                }

                ActionButton {
                    visible: sourceController.hasSource
                    width: 90
                    text: "All columns"
                    onClicked: {
                        columnSearch.text = ""
                        sourceController.resetColumns()
                    }
                }

                ActionButton {
                    width: 148
                    text: sourceController.hasSource ? "Open another CSV" : "Open CSV"
                    primary: !sourceController.hasSource
                    onClicked: sourceDialog.open()
                }
            }

            Rectangle {
                id: tableFrame
                visible: sourceController.hasSource
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: sourceCard.bottom
                anchors.topMargin: 18
                anchors.bottom: footer.top
                anchors.bottomMargin: 18
                color: "#FFFFFF"
                border.width: 1
                border.color: root.rule
                radius: 3
                clip: true

                HorizontalHeaderView {
                    id: headerView
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 58
                    syncView: tableView
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        implicitWidth: 150
                        implicitHeight: 58
                        color: "#F8FAFC"
                        border.width: 1
                        border.color: root.softRule

                        Text {
                            anchors.fill: parent
                            anchors.margins: 8
                            text: model.display
                            color: root.ink
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            wrapMode: Text.Wrap
                            font.family: "Arial"
                            font.pixelSize: 12
                            lineHeight: 1.15
                        }
                    }
                }

                TableView {
                    id: tableView
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: headerView.bottom
                    anchors.bottom: parent.bottom
                    model: sourceTableModel
                    clip: true
                    reuseItems: true
                    boundsBehavior: Flickable.StopAtBounds
                    columnSpacing: -1
                    rowSpacing: -1
                    columnWidthProvider: function(column) { return column === 0 ? 102 : 150 }
                    rowHeightProvider: function() { return 41 }

                    delegate: Rectangle {
                        required property int row
                        required property int column
                        implicitWidth: column === 0 ? 102 : 150
                        implicitHeight: 41
                        color: row % 2 === 0 ? "#FFFFFF" : "#FBFCFE"
                        border.width: 1
                        border.color: root.softRule

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            text: model.display
                            color: model.display === "—" ? "#8B94A3" : root.ink
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                            font.family: "Arial"
                            font.pixelSize: 12
                        }
                    }

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                        contentItem: Rectangle { implicitWidth: 7; radius: 3; color: "#AEB8C8" }
                        background: Rectangle { color: "#F2F4F7" }
                    }
                    ScrollBar.horizontal: ScrollBar {
                        policy: ScrollBar.AsNeeded
                        contentItem: Rectangle { implicitHeight: 7; radius: 3; color: "#AEB8C8" }
                        background: Rectangle { color: "#F2F4F7" }
                    }
                }
            }

            Item {
                id: footer
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.bottom: parent.bottom
                height: 39

                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: sourceController.hasSource ? "Previewing " + sourceController.rowCount.toLocaleString() + " Source Rows" : "Source remains local and read-only"
                    color: root.secondary
                    font.family: "Arial"
                    font.pixelSize: 12
                }

                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Source Row identity preserved"
                    color: root.secondary
                    font.family: "Arial"
                    font.pixelSize: 12
                }
            }
        }

        Rectangle {
            id: evidencePane
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: root.evidenceWidth
            color: "#FBFCFE"
            border.width: 1
            border.color: root.rule

            Flickable {
                id: evidenceScroll
                anchors.fill: parent
                contentWidth: width
                contentHeight: evidenceColumn.implicitHeight + 44
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                    contentItem: Rectangle { implicitWidth: 6; radius: 3; color: "#AEB8C8" }
                    background: Rectangle { color: "transparent" }
                }

                Column {
                    id: evidenceColumn
                    x: 24
                    y: 27
                    width: evidenceScroll.width - 48
                    spacing: 0

                    SectionTitle { text: "Source Identity" }
                    Item { width: 1; height: 14 }
                    EvidenceRow { width: parent.width; label: "File name"; value: sourceController.fileName }
                    EvidenceRow { width: parent.width; label: "Rows · Columns"; value: sourceController.hasSource ? sourceController.rowCount.toLocaleString() + " · " + sourceController.columnCount.toLocaleString() : "—" }
                    EvidenceRow { width: parent.width; label: "SHA-256 checksum"; value: sourceController.checksum; wrapValue: true }
                    EvidenceRow { width: parent.width; label: "Detected delimiter"; value: sourceController.delimiter }
                    EvidenceRow { width: parent.width; label: "Encoding"; value: sourceController.encoding }
                    EvidenceRow { width: parent.width; label: "Last modified"; value: sourceController.lastModified }

                    Rectangle { width: parent.width; height: 1; color: root.rule }
                    Item { width: 1; height: 19 }
                    SectionTitle { text: "Inference Contract Fit" }
                    Item { width: 1; height: 14 }
                    EvidenceRow { width: parent.width; label: "Model Package"; value: sourceController.packageName; wrapValue: true }
                    EvidenceRow { width: parent.width; label: "Required features"; value: sourceController.hasSource && sourceController.packageVersion !== "—" ? sourceController.requiredCount.toString() : "—" }
                    EvidenceRow { width: parent.width; label: "Available in source"; value: sourceController.hasSource && sourceController.packageVersion !== "—" ? sourceController.availableRequiredCount.toString() : "—" }
                    EvidenceRow { width: parent.width; label: "Missing required"; value: sourceController.hasSource && sourceController.packageVersion !== "—" ? sourceController.missingRequiredCount.toString() : "—"; valueColor: sourceController.missingRequiredCount > 0 ? "#B52921" : root.ink }
                    EvidenceRow { width: parent.width; label: "Missing omissible"; value: sourceController.hasSource && sourceController.packageVersion !== "—" ? sourceController.missingOmissibleCount.toString() : "—" }
                    EvidenceRow { width: parent.width; label: "Surplus columns"; value: sourceController.hasSource && sourceController.packageVersion !== "—" ? sourceController.surplusCount.toString() : "—" }
                    EvidenceRow { width: parent.width; label: "Contract status"; value: sourceController.contractStatus; wrapValue: true; valueColor: sourceController.blockingCount > 0 ? "#B52921" : "#14804A" }
                    Text {
                        width: parent.width
                        text: sourceController.contractDetail
                        color: root.secondary
                        wrapMode: Text.Wrap
                        font.family: "Arial"
                        font.pixelSize: 11
                        lineHeight: 1.2
                    }
                    Text {
                        topPadding: 9
                        bottomPadding: 17
                        text: "View contract details"
                        color: root.blue
                        font.family: "Arial"
                        font.pixelSize: 12
                    }

                    Rectangle { width: parent.width; height: 1; color: root.rule }
                    Item { width: 1; height: 19 }
                    SectionTitle { text: "Transformation Audit" }
                    Item { width: 1; height: 14 }
                    EvidenceRow { width: parent.width; label: "Type handling"; value: sourceController.typeHandling; wrapValue: true }
                    EvidenceRow { width: parent.width; label: "Missing-value behavior"; value: sourceController.missingValueHandling; wrapValue: true }
                    EvidenceRow { width: parent.width; label: "Category mapping"; value: sourceController.categoryMapping; wrapValue: true }
                    EvidenceRow { width: parent.width; label: "Column mapping"; value: sourceController.columnMapping; wrapValue: true }
                    EvidenceRow { width: parent.width; label: "Row filtering"; value: sourceController.rowFiltering }
                    Text {
                        topPadding: 8
                        bottomPadding: 17
                        text: "View audit log"
                        color: root.blue
                        font.family: "Arial"
                        font.pixelSize: 12
                    }

                    Rectangle { width: parent.width; height: 1; color: root.rule }
                    Item { width: 1; height: 19 }
                    SectionTitle { text: "Confirm & Run" }
                    Item { width: 1; height: 10 }
                    Text {
                        width: parent.width
                        text: "Confirm that this exact Source Dataset and the disclosed contract findings are correct before requesting prediction."
                        color: root.ink
                        wrapMode: Text.Wrap
                        font.family: "Arial"
                        font.pixelSize: 12
                        lineHeight: 1.25
                    }

                    Item {
                        width: parent.width
                        height: 53
                        opacity: sourceController.canConfirm ? 1 : 0.55
                        activeFocusOnTab: sourceController.canConfirm
                        Accessible.role: Accessible.CheckBox
                        Accessible.name: "I reviewed this source and confirm it is correct for prediction"
                        Accessible.checked: sourceController.confirmed
                        Keys.onPressed: function(event) {
                            if (sourceController.canConfirm && event.key === Qt.Key_Space) {
                                sourceController.setConfirmed(!sourceController.confirmed)
                                event.accepted = true
                            }
                        }

                        Rectangle {
                            id: checkMarkBox
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: 20
                            height: 20
                            color: sourceController.confirmed ? root.blue : "#FFFFFF"
                            border.width: 1
                            border.color: parent.activeFocus || sourceController.confirmed ? root.blue : "#778197"
                            radius: 2

                            Item {
                                anchors.centerIn: parent
                                width: 12
                                height: 10
                                visible: sourceController.confirmed

                                Rectangle {
                                    x: 1
                                    y: 5
                                    width: 5
                                    height: 2
                                    radius: 1
                                    rotation: 45
                                    color: "#FFFFFF"
                                }
                                Rectangle {
                                    x: 4
                                    y: 4
                                    width: 9
                                    height: 2
                                    radius: 1
                                    rotation: -48
                                    color: "#FFFFFF"
                                }
                            }
                        }
                        Text {
                            anchors.left: checkMarkBox.right
                            anchors.leftMargin: 12
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: "I reviewed this source and confirm it is correct for prediction"
                            color: root.ink
                            wrapMode: Text.Wrap
                            font.family: "Arial"
                            font.pixelSize: 12
                        }
                        TapHandler {
                            enabled: sourceController.canConfirm
                            onTapped: {
                                parent.forceActiveFocus()
                                sourceController.setConfirmed(!sourceController.confirmed)
                            }
                        }
                    }

                    ActionButton {
                        width: parent.width
                        height: 44
                        primary: true
                        enabled: sourceController.runEnabled
                        text: sourceController.runButtonText
                        onClicked: sourceController.requestRun()
                    }
                }
            }
        }
    }
}
