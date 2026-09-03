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
    readonly property color pathogenic: "#263B72"
    readonly property color benign: "#6D9B91"
    readonly property color amber: "#8A590E"
    readonly property color rule: "#D8DEE8"
    readonly property color softRule: "#E8ECF2"
    readonly property int evidenceWidth: Math.max(398, Math.min(468, width * 0.305))

    function percent(count, total) {
        return total > 0 ? (100 * count / total).toFixed(1) + "%" : "0.0%"
    }

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

        // Identity lockup: the approved symbol beside live wordmark text.
        // A baked raster wordmark cannot stay legible at app-bar size, where its
        // cap height falls to about ten pixels, so only the symbol is an image.
        Row {
            id: identityLockup
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            spacing: 11

            Image {
                id: identitySymbol
                height: 36
                width: height * (implicitHeight > 0 ? implicitWidth / implicitHeight : 0.93)
                anchors.verticalCenter: parent.verticalCenter
                source: sourceController.identitySymbolUrl
                visible: sourceController.identitySymbolUrl !== "" && status === Image.Ready
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                Accessible.role: Accessible.Graphic
                Accessible.name: "Computational Health Lab"
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "Computational Health Lab"
                color: root.ink
                font.family: "Arial"
                font.pixelSize: 14
                font.weight: Font.DemiBold
                font.letterSpacing: 0.1
            }
        }

        Rectangle {
            id: identityDivider
            anchors.left: identityLockup.right
            anchors.leftMargin: 22
            anchors.verticalCenter: parent.verticalCenter
            width: 1
            height: 38
            color: "#AEB6C3"
        }

        Text {
            id: productTitle
            anchors.left: identityDivider.right
            anchors.leftMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            text: "Resolved Layers"
            color: root.ink
            font.family: "Arial"
            font.pixelSize: 20
            font.weight: Font.Medium
        }

        Item {
            id: navigationLane
            anchors.left: productTitle.right
            anchors.leftMargin: 40
            anchors.right: archiveButton.left
            anchors.rightMargin: 40
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }

        Row {
            anchors.horizontalCenter: navigationLane.horizontalCenter
            anchors.bottom: parent.bottom
            spacing: 18

            Item {
                width: 98
                height: 46
                activeFocusOnTab: true
                Accessible.role: Accessible.Button
                Accessible.name: "Source Review"
                Accessible.selected: sourceController.activeSurface === "review"

                Text {
                    anchors.centerIn: parent
                    text: "Source Review"
                    color: sourceController.activeSurface === "review" ? root.ink : root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                    font.weight: sourceController.activeSurface === "review" ? Font.DemiBold : Font.Normal
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 2
                    color: sourceController.activeSurface === "review" ? root.blue : "transparent"
                }
                TapHandler { onTapped: sourceController.setActiveSurface("review") }
                Keys.onReturnPressed: sourceController.setActiveSurface("review")
                Keys.onSpacePressed: sourceController.setActiveSurface("review")
            }

            Item {
                width: 106
                height: 46
                enabled: sourceController.hasSource
                opacity: enabled ? 1 : 0.48
                activeFocusOnTab: enabled
                Accessible.role: Accessible.Button
                Accessible.name: "Dataset Profile"
                Accessible.selected: sourceController.activeSurface === "profile"

                Text {
                    anchors.centerIn: parent
                    text: "Dataset Profile"
                    color: sourceController.activeSurface === "profile" ? root.ink : root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                    font.weight: sourceController.activeSurface === "profile" ? Font.DemiBold : Font.Normal
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 2
                    color: sourceController.activeSurface === "profile" ? root.blue : "transparent"
                }
                TapHandler { enabled: parent.enabled; onTapped: sourceController.setActiveSurface("profile") }
                Keys.onReturnPressed: sourceController.setActiveSurface("profile")
                Keys.onSpacePressed: sourceController.setActiveSurface("profile")
            }

            Item {
                width: 68
                height: 46
                enabled: sourceController.hasResults
                opacity: enabled ? 1 : 0.48
                activeFocusOnTab: enabled
                Accessible.role: Accessible.Button
                Accessible.name: "Results"
                Accessible.selected: sourceController.activeSurface === "results"

                Text {
                    anchors.centerIn: parent
                    text: "Results"
                    color: sourceController.activeSurface === "results" ? root.ink : root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                    font.weight: sourceController.activeSurface === "results" ? Font.DemiBold : Font.Normal
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 2
                    color: sourceController.activeSurface === "results" ? root.blue : "transparent"
                }
                TapHandler { enabled: parent.enabled; onTapped: sourceController.setActiveSurface("results") }
                Keys.onReturnPressed: sourceController.setActiveSurface("results")
                Keys.onSpacePressed: sourceController.setActiveSurface("results")
            }

            Item {
                width: 82
                height: 46
                enabled: sourceController.hasResults
                opacity: enabled ? 1 : 0.48
                activeFocusOnTab: enabled
                Accessible.role: Accessible.Button
                Accessible.name: "Evaluation"
                Accessible.description: "Observed metrics require a checksum-valid source and explicit Ground-Truth Authorization"
                Accessible.selected: sourceController.activeSurface === "evaluation"

                Text {
                    anchors.centerIn: parent
                    text: "Evaluation"
                    color: sourceController.activeSurface === "evaluation" ? root.ink : root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                    font.weight: sourceController.activeSurface === "evaluation" ? Font.DemiBold : Font.Normal
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 2
                    color: sourceController.activeSurface === "evaluation" ? root.blue : "transparent"
                }
                TapHandler { enabled: parent.enabled; onTapped: sourceController.setActiveSurface("evaluation") }
                Keys.onReturnPressed: sourceController.setActiveSurface("evaluation")
                Keys.onSpacePressed: sourceController.setActiveSurface("evaluation")
            }

            Item {
                width: 66
                height: 46
                activeFocusOnTab: true
                Accessible.role: Accessible.Button
                Accessible.name: "Settings"
                Accessible.description: "Install the Model Package this machine uses for prediction"
                Accessible.selected: sourceController.activeSurface === "settings"

                Text {
                    anchors.centerIn: parent
                    text: "Settings"
                    color: sourceController.activeSurface === "settings" ? root.ink : root.secondary
                    font.family: "Arial"
                    font.pixelSize: 13
                    font.weight: sourceController.activeSurface === "settings" ? Font.DemiBold : Font.Normal
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 2
                    color: sourceController.activeSurface === "settings" ? root.blue : "transparent"
                }
                TapHandler { onTapped: sourceController.setActiveSurface("settings") }
                Keys.onReturnPressed: sourceController.setActiveSurface("settings")
                Keys.onSpacePressed: sourceController.setActiveSurface("settings")
            }
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
            enabled: resultsController.archiveCount > 0
            onClicked: {
                resultsController.refreshArchive()
                archivePopup.open()
            }
        }
    }

    Popup {
        id: archivePopup
        x: root.width - width - 28
        y: appBar.height - 5
        width: Math.min(470, root.width - 56)
        height: Math.min(520, root.height - appBar.height - 28)
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        padding: 0

        background: Rectangle {
            color: "#FFFFFF"
            border.width: 1
            border.color: root.rule
            radius: 4
        }

        contentItem: Column {
            spacing: 0

            Item {
                width: parent.width
                height: 68
                Text { x: 20; y: 15; text: "Run Archive"; color: root.ink; font.family: "Arial"; font.pixelSize: 18; font.weight: Font.DemiBold }
                Text { x: 20; y: 40; text: resultsController.archiveCount + " immutable Verified Run" + (resultsController.archiveCount === 1 ? "" : "s"); color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: root.rule }
            }

            ListView {
                width: parent.width
                height: archivePopup.height - 68
                clip: true
                model: runArchiveModel
                boundsBehavior: Flickable.StopAtBounds
                delegate: Item {
                    required property string runId
                    required property string completedAt
                    required property string sourceName
                    required property string packageName
                    required property string packageVersion
                    required property int recordCount
                    required property int pathogenicCount
                    required property int warningCount
                    width: ListView.view.width
                    height: 94
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: "Open Verified Run " + runId

                    Rectangle { anchors.fill: parent; color: hover.hovered ? "#F5F7FB" : "transparent" }
                    Text { x: 20; y: 14; width: parent.width - 40; text: sourceName; elide: Text.ElideMiddle; color: root.ink; font.family: "Arial"; font.pixelSize: 13; font.weight: Font.DemiBold }
                    Text { x: 20; y: 37; width: parent.width - 40; text: recordCount.toLocaleString() + " records  ·  " + pathogenicCount.toLocaleString() + " Pathogenic  ·  " + warningCount + " warnings"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                    Text { x: 20; y: 59; width: parent.width - 40; text: packageName + " " + packageVersion + "  ·  " + completedAt; elide: Text.ElideRight; color: root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: root.softRule }
                    HoverHandler { id: hover }
                    TapHandler { onTapped: { if (sourceController.openArchivedRun(runId)) archivePopup.close() } }
                    Keys.onReturnPressed: { if (sourceController.openArchivedRun(runId)) archivePopup.close() }
                }
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            }
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
            visible: sourceController.activeSurface === "review"
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


        Item {
            id: profileDesk
            visible: sourceController.activeSurface === "profile"
            anchors.fill: parent

            Text {
                id: profileTitle
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.top: parent.top
                anchors.topMargin: 23
                text: "Dataset Profile"
                color: root.ink
                font.family: "Arial"
                font.pixelSize: 27
                font.weight: Font.Medium
            }

            Text {
                anchors.left: profileTitle.right
                anchors.leftMargin: 18
                anchors.baseline: profileTitle.baseline
                text: "Descriptive source evidence · available before prediction"
                color: root.secondary
                font.family: "Arial"
                font.pixelSize: 13
            }

            ActionButton {
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.verticalCenter: profileTitle.verticalCenter
                width: 142
                text: "Open another CSV"
                onClicked: sourceDialog.open()
            }

            Rectangle {
                id: profileSummary
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: profileTitle.bottom
                anchors.topMargin: 17
                height: 62
                color: "#FAFBFD"
                border.width: 1
                border.color: root.rule
                radius: 3

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 0

                    Item {
                        width: parent.width * 0.29
                        height: parent.height
                        Text { anchors.left: parent.left; anchors.top: parent.top; anchors.topMargin: 12; text: sourceController.fileName; color: root.ink; elide: Text.ElideMiddle; width: parent.width - 26; font.family: "Arial"; font.pixelSize: 13; font.weight: Font.DemiBold }
                        Text { anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.bottomMargin: 11; text: "Source Dataset"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                    }
                    Rectangle { width: 1; height: 28; anchors.verticalCenter: parent.verticalCenter; color: root.rule }
                    Item {
                        width: parent.width * 0.20
                        height: parent.height
                        Text { anchors.left: parent.left; anchors.leftMargin: 20; anchors.top: parent.top; anchors.topMargin: 12; text: sourceController.rowCount.toLocaleString() + " × " + sourceController.columnCount.toLocaleString(); color: root.ink; font.family: "Arial"; font.pixelSize: 15; font.weight: Font.DemiBold }
                        Text { anchors.left: parent.left; anchors.leftMargin: 20; anchors.bottom: parent.bottom; anchors.bottomMargin: 11; text: "Rows × columns"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                    }
                    Rectangle { width: 1; height: 28; anchors.verticalCenter: parent.verticalCenter; color: root.rule }
                    Item {
                        width: parent.width * 0.25
                        height: parent.height
                        Text { anchors.left: parent.left; anchors.leftMargin: 20; anchors.top: parent.top; anchors.topMargin: 12; text: sourceController.labelCoverageText; color: sourceController.labelsAuthorized ? root.ink : root.secondary; font.family: "Arial"; font.pixelSize: 13; font.weight: Font.DemiBold }
                        Text { anchors.left: parent.left; anchors.leftMargin: 20; anchors.bottom: parent.bottom; anchors.bottomMargin: 11; text: "Label coverage"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                    }
                    Rectangle { width: 1; height: 28; anchors.verticalCenter: parent.verticalCenter; color: root.rule }
                    Item {
                        width: parent.width * 0.23
                        height: parent.height
                        Text { anchors.left: parent.left; anchors.leftMargin: 20; anchors.top: parent.top; anchors.topMargin: 12; text: sourceController.rowsWithMissing.toLocaleString() + " rows"; color: root.ink; font.family: "Arial"; font.pixelSize: 13; font.weight: Font.DemiBold }
                        Text { anchors.left: parent.left; anchors.leftMargin: 20; anchors.bottom: parent.bottom; anchors.bottomMargin: 11; text: sourceController.missingCellCount.toLocaleString() + " missing cells"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                    }
                }
            }

            Item {
                id: profileAnalysis
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: profileSummary.bottom
                anchors.topMargin: 17
                height: Math.min(292, Math.max(252, parent.height * 0.31))

                Item {
                    id: compositionPane
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * 0.37

                    SectionTitle { id: compositionTitle; text: "Class composition" }
                    Text {
                        anchors.left: compositionTitle.right
                        anchors.leftMargin: 12
                        anchors.baseline: compositionTitle.baseline
                        text: sourceController.labelsAuthorized ? sourceController.authorizedLabelColumn : "Ground truth not authorized"
                        color: root.secondary
                        font.family: "Arial"
                        font.pixelSize: 11
                    }

                    Item {
                        visible: sourceController.labelsAuthorized
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: compositionTitle.bottom
                        anchors.topMargin: 18
                        height: parent.height - 42

                        Rectangle {
                            id: compositionBar
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            height: 22
                            color: "#E8ECF2"
                            radius: 3
                            clip: true

                            Rectangle {
                                anchors.left: parent.left
                                width: parent.width * sourceController.pathogenicShare
                                height: parent.height
                                color: root.pathogenic
                            }
                            Rectangle {
                                anchors.right: parent.right
                                width: parent.width * (1 - sourceController.pathogenicShare)
                                height: parent.height
                                color: root.benign
                            }
                        }

                        Row {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: compositionBar.bottom
                            anchors.topMargin: 15
                            height: 62

                            Repeater {
                                model: [
                                    { key: "pathogenic", label: "Pathogenic", count: sourceController.pathogenicCount, color: root.pathogenic },
                                    { key: "benign", label: "Benign", count: sourceController.benignCount, color: root.benign },
                                    { key: "missing", label: "Missing", count: sourceController.missingLabelCount, color: "#8B94A3" },
                                    { key: "unrecognized", label: "Unrecognized", count: sourceController.unrecognizedLabelCount, color: root.amber }
                                ]

                                Item {
                                    required property var modelData
                                    width: parent.width / 4
                                    height: parent.height
                                    activeFocusOnTab: true
                                    Accessible.role: Accessible.Button
                                    Accessible.name: "Filter records by " + modelData.label

                                    Rectangle { anchors.left: parent.left; anchors.top: parent.top; width: 8; height: 8; radius: 4; color: modelData.color }
                                    Text { anchors.left: parent.left; anchors.top: parent.top; anchors.topMargin: 15; text: modelData.count.toLocaleString(); color: root.ink; font.family: "Arial"; font.pixelSize: 15; font.weight: Font.DemiBold }
                                    Text { anchors.left: parent.left; anchors.bottom: parent.bottom; text: modelData.label + "  " + root.percent(modelData.count, sourceController.rowCount); color: sourceController.classFilter === modelData.key ? root.blue : root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                                    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.rightMargin: 13; height: 2; color: sourceController.classFilter === modelData.key ? root.blue : "transparent" }
                                    TapHandler { onTapped: sourceController.setClassFilter(modelData.key) }
                                    Keys.onReturnPressed: sourceController.setClassFilter(modelData.key)
                                }
                            }
                        }

                        Text {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.topMargin: 116
                            text: "The bar compares the " + sourceController.recognizedLabelCount.toLocaleString() + " explicitly mapped labels only. Missing and unrecognized values remain visible and outside the bar."
                            color: root.secondary
                            wrapMode: Text.Wrap
                            font.family: "Arial"
                            font.pixelSize: 11
                            lineHeight: 1.2
                        }
                    }

                    Item {
                        visible: !sourceController.labelsAuthorized
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: compositionTitle.bottom
                        anchors.topMargin: 18
                        height: 130

                        Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; height: 22; color: "#EDF0F4"; radius: 3 }
                        Text {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.topMargin: 43
                            text: "Class composition is unavailable until a label column and its Pathogenic/Benign values are explicitly authorized. No label-like column is interpreted automatically."
                            color: root.secondary
                            wrapMode: Text.Wrap
                            font.family: "Arial"
                            font.pixelSize: 12
                            lineHeight: 1.25
                        }
                    }
                }

                Rectangle {
                    anchors.left: compositionPane.right
                    anchors.leftMargin: 24
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 1
                    color: root.rule
                }

                Item {
                    id: groupPane
                    anchors.left: compositionPane.right
                    anchors.leftMargin: 49
                    anchors.right: authorizationPane.left
                    anchors.rightMargin: 25
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    SectionTitle { id: groupsTitle; text: "Group breakdown" }
                    SelectField {
                        anchors.right: parent.right
                        anchors.verticalCenter: groupsTitle.verticalCenter
                        width: 164
                        model: sourceController.groupColumns
                        currentIndex: Math.max(0, sourceController.groupColumns.indexOf(sourceController.groupColumn))
                        onActivated: sourceController.selectGroupColumn(currentText)
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: groupsTitle.bottom
                        anchors.topMargin: 13
                        height: 31
                        color: "#F5F7FA"
                        border.width: 1
                        border.color: root.softRule

                        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: "Group"; color: root.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold }
                        Text { x: parent.width * 0.44; anchors.verticalCenter: parent.verticalCenter; text: "Records / share"; color: root.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold }
                        Text { visible: sourceController.labelsAuthorized; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: "P  ·  B  ·  Other"; color: root.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold }
                    }

                    ListView {
                        id: groupList
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: groupsTitle.bottom
                        anchors.topMargin: 44
                        anchors.bottom: parent.bottom
                        clip: true
                        model: groupBreakdownModel
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Item {
                            required property string value
                            required property int index
                            required property string displayValue
                            required property int total
                            required property real share
                            required property string shareText
                            required property int pathogenic
                            required property int benign
                            required property int invalid
                            required property bool hasLabels
                            width: groupList.width
                            height: 38
                            activeFocusOnTab: true
                            Accessible.role: Accessible.Button
                            Accessible.name: "Filter by group " + displayValue

                            Rectangle { anchors.fill: parent; color: sourceController.hasGroupFilter && sourceController.groupFilterValue === value ? "#EEF3FF" : (index % 2 ? "#FBFCFE" : "#FFFFFF") }
                            Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: root.softRule }
                            Text { x: 10; width: parent.width * 0.40; anchors.verticalCenter: parent.verticalCenter; text: displayValue; color: root.ink; elide: Text.ElideRight; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.Medium }
                            Item {
                                x: parent.width * 0.44
                                width: parent.width * 0.25
                                height: parent.height
                                Rectangle { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; width: parent.width * share; height: 3; color: "#AEBBCE" }
                                Text { anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.bottomMargin: 4; text: total.toLocaleString() + "  ·  " + shareText; color: root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                            }
                            Text { visible: hasLabels; anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: pathogenic.toLocaleString() + "  ·  " + benign.toLocaleString() + "  ·  " + invalid.toLocaleString(); color: root.ink; font.family: "Arial"; font.pixelSize: 10 }
                            TapHandler { onTapped: sourceController.setGroupFilter(value) }
                            Keys.onReturnPressed: sourceController.setGroupFilter(value)
                        }
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded; contentItem: Rectangle { implicitWidth: 6; radius: 3; color: "#AEB8C8" } }
                    }
                }

                Rectangle {
                    id: authorizationPane
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: Math.max(322, parent.width * 0.255)
                    color: "#FAFBFD"
                    border.width: 1
                    border.color: root.rule
                    radius: 3

                    SectionTitle { id: authorizationTitle; anchors.left: parent.left; anchors.leftMargin: 17; anchors.top: parent.top; anchors.topMargin: 15; text: "Ground-Truth Authorization" }
                    Text { anchors.left: parent.left; anchors.leftMargin: 17; anchors.right: parent.right; anchors.rightMargin: 17; anchors.top: authorizationTitle.bottom; anchors.topMargin: 7; text: "For descriptive class counts only. Evaluation and F1 remain separate."; color: root.secondary; wrapMode: Text.Wrap; font.family: "Arial"; font.pixelSize: 10 }

                    SelectField {
                        id: labelColumnSelect
                        anchors.left: parent.left
                        anchors.leftMargin: 17
                        anchors.right: parent.right
                        anchors.rightMargin: 17
                        anchors.top: authorizationTitle.bottom
                        anchors.topMargin: 38
                        model: ["Select label column"].concat(sourceController.labelColumns)
                        currentIndex: sourceController.selectedLabelColumn ? Math.max(1, model.indexOf(sourceController.selectedLabelColumn)) : 0
                        onActivated: sourceController.selectLabelColumn(currentIndex === 0 ? "" : currentText)
                    }

                    Row {
                        anchors.left: parent.left
                        anchors.leftMargin: 17
                        anchors.right: parent.right
                        anchors.rightMargin: 17
                        anchors.top: labelColumnSelect.bottom
                        anchors.topMargin: 10
                        spacing: 9

                        SelectField {
                            id: pathogenicSelect
                            width: (parent.width - 9) / 2
                            enabled: sourceController.selectedLabelColumn !== ""
                            model: ["Pathogenic value"].concat(sourceController.labelValues)
                            currentIndex: sourceController.pathogenicMapping ? Math.max(1, model.indexOf(sourceController.pathogenicMapping)) : 0
                        }
                        SelectField {
                            id: benignSelect
                            width: (parent.width - 9) / 2
                            enabled: sourceController.selectedLabelColumn !== ""
                            model: ["Benign value"].concat(sourceController.labelValues)
                            currentIndex: sourceController.benignMapping ? Math.max(1, model.indexOf(sourceController.benignMapping)) : 0
                        }
                    }

                    ActionButton {
                        anchors.left: parent.left
                        anchors.leftMargin: 17
                        anchors.right: parent.right
                        anchors.rightMargin: 17
                        anchors.top: labelColumnSelect.bottom
                        anchors.topMargin: 58
                        height: 30
                        primary: true
                        enabled: pathogenicSelect.currentIndex > 0 && benignSelect.currentIndex > 0 && pathogenicSelect.currentText !== benignSelect.currentText
                        text: sourceController.labelsAuthorized ? "Update authorized mapping" : "Authorize label mapping"
                        onClicked: sourceController.authorizeLabels(pathogenicSelect.currentText, benignSelect.currentText)
                    }

                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 17
                        anchors.right: parent.right
                        anchors.rightMargin: 17
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 13
                        text: sourceController.profileMessage
                        color: sourceController.labelsAuthorized ? "#23704B" : root.secondary
                        wrapMode: Text.Wrap
                        font.family: "Arial"
                        font.pixelSize: 10
                        lineHeight: 1.15
                    }
                }
            }

            Item {
                id: recordsHeader
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: profileAnalysis.bottom
                anchors.topMargin: 15
                height: 42

                Text { id: recordsTitle; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; text: "Exact source records"; color: root.ink; font.family: "Arial"; font.pixelSize: 15; font.weight: Font.DemiBold }
                Text { anchors.left: recordsTitle.right; anchors.leftMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: sourceController.filteredRowCount.toLocaleString() + " of " + sourceController.rowCount.toLocaleString() + " Source Rows"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }

                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8

                    Rectangle {
                        visible: sourceController.classFilter !== ""
                        width: classChipText.implicitWidth + 34
                        height: 27
                        color: "#EEF3FF"
                        border.width: 1
                        border.color: "#C7D5FF"
                        radius: 13
                        Text { id: classChipText; anchors.left: parent.left; anchors.leftMargin: 11; anchors.verticalCenter: parent.verticalCenter; text: "Class: " + sourceController.classFilter.charAt(0).toUpperCase() + sourceController.classFilter.slice(1); color: "#173A9C"; font.family: "Arial"; font.pixelSize: 10 }
                        Item { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 10; height: 10; Rectangle { anchors.centerIn: parent; width: 10; height: 1; rotation: 45; color: "#173A9C" } Rectangle { anchors.centerIn: parent; width: 10; height: 1; rotation: -45; color: "#173A9C" } }
                        TapHandler { onTapped: sourceController.setClassFilter(sourceController.classFilter) }
                    }
                    Rectangle {
                        visible: sourceController.hasGroupFilter
                        width: groupChipText.implicitWidth + 34
                        height: 27
                        color: "#F0F4F3"
                        border.width: 1
                        border.color: "#CAD8D5"
                        radius: 13
                        Text { id: groupChipText; anchors.left: parent.left; anchors.leftMargin: 11; anchors.verticalCenter: parent.verticalCenter; text: sourceController.groupFilterDisplay; color: "#355E56"; font.family: "Arial"; font.pixelSize: 10 }
                        Item { anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter; width: 10; height: 10; Rectangle { anchors.centerIn: parent; width: 10; height: 1; rotation: 45; color: "#355E56" } Rectangle { anchors.centerIn: parent; width: 10; height: 1; rotation: -45; color: "#355E56" } }
                        TapHandler { onTapped: sourceController.clearGroupFilter() }
                    }
                    ActionButton { visible: sourceController.activeFilterCount > 1; width: 76; height: 29; quiet: true; text: "Clear all"; onClicked: sourceController.clearProfileFilters() }
                }
            }

            Rectangle {
                id: profileTableFrame
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: recordsHeader.bottom
                anchors.bottom: profileFooter.top
                anchors.bottomMargin: 8
                color: "#FFFFFF"
                border.width: 1
                border.color: root.rule
                radius: 3
                clip: true

                HorizontalHeaderView {
                    id: profileHeaderView
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 47
                    syncView: profileTableView
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    delegate: Rectangle {
                        implicitWidth: 150
                        implicitHeight: 47
                        color: "#F8FAFC"
                        border.width: 1
                        border.color: root.softRule
                        Text { anchors.fill: parent; anchors.margins: 7; text: model.display; color: root.ink; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; wrapMode: Text.Wrap; font.family: "Arial"; font.pixelSize: 10; lineHeight: 1.1 }
                    }
                }

                TableView {
                    id: profileTableView
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: profileHeaderView.bottom
                    anchors.bottom: parent.bottom
                    model: sourceTableModel
                    clip: true
                    reuseItems: true
                    boundsBehavior: Flickable.StopAtBounds
                    columnSpacing: -1
                    rowSpacing: -1
                    columnWidthProvider: function(column) { return column === 0 ? 102 : 150 }
                    rowHeightProvider: function() { return 35 }
                    delegate: Rectangle {
                        required property int row
                        required property int column
                        implicitWidth: column === 0 ? 102 : 150
                        implicitHeight: 35
                        color: row % 2 === 0 ? "#FFFFFF" : "#FBFCFE"
                        border.width: 1
                        border.color: root.softRule
                        Text { anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9; text: model.display; color: model.display === "—" ? "#8B94A3" : root.ink; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; font.family: "Arial"; font.pixelSize: 11 }
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
                id: profileFooter
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.bottom: parent.bottom
                height: 31
                Text { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; text: "Descriptive profile only · no prediction or performance metric has been calculated"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                Text { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; text: "Source Row identity preserved"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
            }
        }

        Item {
            id: resultsDesk
            visible: sourceController.activeSurface === "results"
            anchors.fill: parent

            Text {
                id: resultsTitle
                x: 34
                y: 23
                text: "Prediction Results"
                color: root.ink
                font.family: "Arial"
                font.pixelSize: 27
                font.weight: Font.Medium
            }

            Rectangle {
                anchors.left: resultsTitle.right
                anchors.leftMargin: 17
                anchors.verticalCenter: resultsTitle.verticalCenter
                width: verifiedText.implicitWidth + 28
                height: 24
                color: "#EDF7F2"
                radius: 12
                Text { id: verifiedText; anchors.centerIn: parent; text: "VERIFIED RUN"; color: "#147A4A"; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 0.5 }
            }

            Text {
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.baseline: resultsTitle.baseline
                width: Math.min(430, parent.width * 0.35)
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideMiddle
                text: resultsController.runId
                color: root.secondary
                font.family: "Arial"
                font.pixelSize: 11
            }

            Rectangle {
                id: resultsSummary
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: resultsTitle.bottom
                anchors.topMargin: 17
                height: 72
                color: "#FAFBFD"
                border.width: 1
                border.color: root.rule
                radius: 3

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    Repeater {
                        model: [
                            { value: resultsController.sourceName, label: "Source Dataset", share: 0.25 },
                            { value: resultsController.recordCount.toLocaleString(), label: "Records", share: 0.12 },
                            { value: resultsController.pathogenicCount.toLocaleString(), label: "Pathogenic", share: 0.12 },
                            { value: resultsController.benignCount.toLocaleString(), label: "Benign", share: 0.12 },
                            { value: resultsController.releaseThreshold.toFixed(6), label: "Release threshold", share: 0.15 },
                            { value: resultsController.packageName + " " + resultsController.packageVersion, label: "Model Package", share: 0.24 }
                        ]
                        Item {
                            required property var modelData
                            required property int index
                            width: parent.width * modelData.share
                            height: parent.height
                            Text { x: 12; y: 15; width: parent.width - 25; text: modelData.value; elide: Text.ElideMiddle; color: root.ink; font.family: "Arial"; font.pixelSize: 13; font.weight: Font.DemiBold }
                            Text { x: 12; y: 42; text: modelData.label; color: root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                            Rectangle { visible: index > 0; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; width: 1; height: 31; color: root.rule }
                        }
                    }
                }
            }

            Row {
                id: resultsTabs
                x: 34
                anchors.top: resultsSummary.bottom
                anchors.topMargin: 16
                spacing: 22
                Repeater {
                    model: [{ key: "overview", label: "Overview" }, { key: "records", label: "Records" }]
                    Item {
                        required property var modelData
                        width: labelText.implicitWidth
                        height: 34
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.label
                        Accessible.selected: resultsController.activeTab === modelData.key
                        Text { id: labelText; anchors.top: parent.top; text: modelData.label; color: resultsController.activeTab === modelData.key ? root.ink : root.secondary; font.family: "Arial"; font.pixelSize: 13; font.weight: resultsController.activeTab === modelData.key ? Font.DemiBold : Font.Normal }
                        Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 2; color: resultsController.activeTab === modelData.key ? root.blue : "transparent" }
                        TapHandler { onTapped: modelData.key === "overview" ? resultsController.showOverview() : resultsController.showRecords() }
                        Keys.onReturnPressed: modelData.key === "overview" ? resultsController.showOverview() : resultsController.showRecords()
                        Keys.onSpacePressed: modelData.key === "overview" ? resultsController.showOverview() : resultsController.showRecords()
                    }
                }
            }

            // Research Export. Every original Source Dataset column beside the
            // immutable predictions, in Source Row order regardless of how the
            // table is currently sorted or filtered. Competition Export stays
            // separate and awaits the organizer format.
            FileDialog {
                id: researchExportDialog
                title: "Export predictions with every source column"
                fileMode: FileDialog.SaveFile
                defaultSuffix: "csv"
                nameFilters: ["CSV files (*.csv)"]
                currentFile: "file:" + exportController.suggestedFileName
                onAccepted: exportController.exportResearchCsv(selectedFile)
            }

            ActionButton {
                id: exportButton
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.verticalCenter: resultsTabs.verticalCenter
                height: 34
                quiet: true
                text: exportController.busy ? "Exporting…" : "Export CSV"
                enabled: exportController.canExport
                Accessible.description: "Write every source column and its prediction in Source Row order"
                onClicked: researchExportDialog.open()
            }

            Rectangle { anchors.left: parent.left; anchors.leftMargin: 34; anchors.right: parent.right; anchors.rightMargin: 34; anchors.top: resultsTabs.bottom; height: 1; color: root.rule }

            Item {
                id: overviewPane
                visible: resultsController.activeTab === "overview"
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: resultsTabs.bottom
                anchors.topMargin: 22
                anchors.bottom: resultsFooter.top
                anchors.bottomMargin: 15

                Item {
                    id: distributionPane
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * 0.67

                    SectionTitle { id: distributionTitle; text: "Ensemble Score Distribution" }
                    Text { anchors.left: distributionTitle.right; anchors.leftMargin: 12; anchors.baseline: distributionTitle.baseline; text: "Select a score band to inspect its records"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }

                    Item {
                        id: chart
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: distributionTitle.bottom
                        anchors.topMargin: 25
                        height: Math.max(230, parent.height - 145)

                        Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: root.rule }
                        Repeater {
                            model: 5
                            Rectangle { required property int index; x: 0; y: chart.height * index / 4; width: chart.width; height: 1; color: index === 4 ? root.rule : root.softRule }
                        }
                        Row {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: parent.height
                            spacing: 2
                            Repeater {
                                model: scoreHistogramModel
                                Item {
                                    required property real lower
                                    required property real upper
                                    required property int count
                                    required property real heightRatio
                                    width: (chart.width - 62) / 32
                                    height: chart.height
                                    activeFocusOnTab: count > 0
                                    Accessible.role: Accessible.Button
                                    Accessible.name: count + " records with scores from " + lower.toFixed(3) + " to " + upper.toFixed(3)
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.bottom: parent.bottom
                                        height: Math.max(count > 0 ? 3 : 0, (parent.height - 18) * heightRatio)
                                        color: lower >= resultsController.selectedLower && upper <= resultsController.selectedUpper ? root.blue : "#8EA2C9"
                                        opacity: hover.hovered ? 1 : 0.88
                                    }
                                    HoverHandler { id: hover }
                                    TapHandler { onTapped: resultsController.selectScoreRange(lower, upper) }
                                    Keys.onReturnPressed: resultsController.selectScoreRange(lower, upper)
                                    Keys.onSpacePressed: resultsController.selectScoreRange(lower, upper)
                                }
                            }
                        }
                        Rectangle { x: chart.width * resultsController.releaseThreshold; y: 0; width: 2; height: chart.height; color: root.amber }
                        Text { x: Math.min(chart.width - width, chart.width * resultsController.releaseThreshold + 6); y: 4; text: "Threshold " + resultsController.releaseThreshold.toFixed(3); color: root.amber; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold }
                    }

                    Row {
                        anchors.left: chart.left
                        anchors.right: chart.right
                        anchors.top: chart.bottom
                        anchors.topMargin: 9
                        Text { text: "0.0"; color: root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                        Item { width: parent.width - 48; height: 1 }
                        Text { text: "1.0"; color: root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                    }
                }

                Rectangle { anchors.left: distributionPane.right; anchors.leftMargin: 24; anchors.top: parent.top; anchors.bottom: parent.bottom; width: 1; color: root.rule }

                Item {
                    anchors.left: distributionPane.right
                    anchors.leftMargin: 49
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    SectionTitle { id: investigationTitle; text: "Investigation Sets" }
                    Text { anchors.left: parent.left; anchors.right: parent.right; anchors.top: investigationTitle.bottom; anchors.topMargin: 10; text: "Purposeful groups derived from the immutable prediction records."; color: root.secondary; wrapMode: Text.Wrap; font.family: "Arial"; font.pixelSize: 11 }
                    ListView {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: investigationTitle.bottom
                        anchors.topMargin: 42
                        height: Math.min(contentHeight, 252)
                        model: investigationSetModel
                        interactive: false
                        spacing: 0
                        delegate: Item {
                            required property string key
                            required property string title
                            required property string detail
                            required property int count
                            width: ListView.view.width
                            height: 60
                            activeFocusOnTab: true
                            Accessible.role: Accessible.Button
                            Accessible.name: title + ", " + count + " records"
                            Rectangle { anchors.fill: parent; color: resultsController.selectionKey === key ? "#F0F4FF" : "transparent"; border.width: resultsController.selectionKey === key ? 1 : 0; border.color: "#C5D2FA"; radius: 3 }
                            Text { x: 11; y: 10; width: parent.width - 62; text: title; color: root.ink; font.family: "Arial"; font.pixelSize: 12; font.weight: Font.DemiBold }
                            Text { x: 11; y: 32; width: parent.width - 62; text: detail; elide: Text.ElideRight; color: root.secondary; font.family: "Arial"; font.pixelSize: 10 }
                            Text { anchors.right: parent.right; anchors.rightMargin: 12; y: 18; text: count.toLocaleString(); color: resultsController.selectionKey === key ? root.blue : root.ink; font.family: "Arial"; font.pixelSize: 14; font.weight: Font.Bold }
                            TapHandler { onTapped: resultsController.selectInvestigationSet(key) }
                            Keys.onReturnPressed: resultsController.selectInvestigationSet(key)
                            Keys.onSpacePressed: resultsController.selectInvestigationSet(key)
                        }
                    }

                    Text {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: selectionBox.top
                        anchors.bottomMargin: 10
                        text: "Run warnings  " + resultsController.warningCount + "  ·  run-level evidence, not a row filter"
                        color: resultsController.warningCount > 0 ? root.amber : root.secondary
                        font.family: "Arial"
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        id: selectionBox
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 82
                        color: "#FAFBFD"
                        border.width: 1
                        border.color: root.rule
                        radius: 3
                        Text { x: 14; y: 13; width: parent.width - 28; text: resultsController.selectionTitle; elide: Text.ElideRight; color: root.ink; font.family: "Arial"; font.pixelSize: 12; font.weight: Font.DemiBold }
                        Text { x: 14; y: 36; text: resultsController.selectedCount.toLocaleString() + " records selected"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
                        ActionButton { anchors.right: parent.right; anchors.rightMargin: 10; anchors.bottom: parent.bottom; anchors.bottomMargin: 9; width: 150; height: 31; primary: true; text: "Inspect " + resultsController.selectedCount.toLocaleString() + " records"; enabled: resultsController.selectedCount > 0; onClicked: resultsController.inspectSelection() }
                    }
                }
            }

            Item {
                id: recordsPane
                visible: resultsController.activeTab === "records"
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.top: resultsTabs.bottom
                anchors.topMargin: 17
                anchors.bottom: resultsFooter.top
                anchors.bottomMargin: 12

                ActionButton { id: backOverview; anchors.left: parent.left; anchors.top: parent.top; width: 142; height: 34; quiet: true; text: "Back to Overview"; onClicked: resultsController.showOverview() }
                Rectangle {
                    anchors.left: backOverview.right
                    anchors.leftMargin: 14
                    anchors.verticalCenter: backOverview.verticalCenter
                    width: selectionRecordText.implicitWidth + 26
                    height: 30
                    color: "#F0F4FF"
                    border.width: 1
                    border.color: "#C5D2FA"
                    radius: 15
                    Text { id: selectionRecordText; x: 12; anchors.verticalCenter: parent.verticalCenter; text: resultsController.selectionTitle + " · " + resultsController.visibleRecordCount.toLocaleString() + (resultsController.selectionKey === "all" ? "" : "  ×"); color: root.blue; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.DemiBold }
                    TapHandler { enabled: resultsController.selectionKey !== "all"; onTapped: resultsController.clearSelection() }
                }
                TextField {
                    anchors.right: parent.right
                    anchors.verticalCenter: backOverview.verticalCenter
                    width: 238
                    height: 34
                    placeholderText: "Search Source Row or class"
                    selectByMouse: true
                    font.family: "Arial"
                    font.pixelSize: 11
                    onTextChanged: resultsController.searchRecords(text)
                }

                SplitView {
                    id: recordsWorkspace
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: backOverview.bottom
                    anchors.topMargin: 14
                    anchors.bottom: parent.bottom
                    orientation: Qt.Horizontal
                    handle: Rectangle {
                        id: splitHandle
                        implicitWidth: 9
                        implicitHeight: 9
                        color: SplitHandle.hovered || SplitHandle.pressed ? "#EEF3FF" : "#F8FAFC"
                        activeFocusOnTab: resultsController.hasSelectedRecord
                        Accessible.role: Accessible.Separator
                        Accessible.name: "Resize Records table and Variant Inspector"
                        Accessible.description: "Use Left and Right Arrow keys to resize the Variant Inspector"
                        Rectangle { anchors.horizontalCenter: parent.horizontalCenter; width: splitHandle.activeFocus ? 2 : 1; height: parent.height; color: splitHandle.activeFocus || SplitHandle.hovered || SplitHandle.pressed ? root.blue : root.rule }
                        Keys.onPressed: function(event) {
                            if (event.key !== Qt.Key_Left && event.key !== Qt.Key_Right)
                                return
                            var change = event.key === Qt.Key_Left ? 24 : -24
                            variantInspector.SplitView.preferredWidth = Math.max(
                                variantInspector.SplitView.minimumWidth,
                                Math.min(variantInspector.SplitView.maximumWidth, variantInspector.width + change)
                            )
                            event.accepted = true
                        }
                    }

                    Item {
                        id: recordsTablePane
                        SplitView.fillWidth: true
                        SplitView.minimumWidth: resultsController.hasSelectedRecord ? 500 : 680

                        HorizontalHeaderView {
                            id: predictionHeader
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            height: 35
                            syncView: predictionTable
                            clip: true
                            delegate: Rectangle { implicitWidth: model.column === 0 ? 120 : 190; implicitHeight: 35; color: "#F3F5F8"; border.width: 1; border.color: root.rule; Text { anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10; text: model.display; color: root.secondary; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold } }
                        }
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: predictionHeader.bottom
                            anchors.bottom: parent.bottom
                            color: "transparent"
                            border.width: predictionTable.activeFocus ? 1 : 0
                            border.color: root.blue

                            TableView {
                                id: predictionTable
                                anchors.fill: parent
                                anchors.margins: parent.border.width
                                model: predictionTableModel
                                clip: true
                                reuseItems: true
                                activeFocusOnTab: true
                                Accessible.role: Accessible.Table
                                Accessible.name: "Prediction Records. Use arrow keys to select a Source Row."
                                columnSpacing: -1
                                rowSpacing: -1
                                columnWidthProvider: function(column) { return column === 0 ? 120 : 190 }
                                rowHeightProvider: function() { return 36 }
                                delegate: Rectangle {
                                    required property int row
                                    required property int column
                                    required property int sourceRow
                                    required property string columnLabel
                                    implicitWidth: column === 0 ? 120 : 190
                                    implicitHeight: 36
                                    color: row === resultsController.selectedVisibleRow ? "#EEF3FF" : (row % 2 === 0 ? "#FFFFFF" : "#FBFCFE")
                                    border.width: 1
                                    border.color: row === resultsController.selectedVisibleRow ? "#C5D2FA" : root.softRule
                                    Accessible.role: Accessible.Cell
                                    Accessible.name: columnLabel + ", Source Row " + sourceRow + ": " + model.display
                                    Accessible.selected: row === resultsController.selectedVisibleRow
                                    Accessible.onPressAction: resultsController.selectRecordAt(row)
                                    Text { anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10; text: model.display; color: column === 1 && model.display === "Pathogenic" ? root.pathogenic : root.ink; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; font.family: "Arial"; font.pixelSize: 11; font.weight: column === 1 || column === 0 ? Font.DemiBold : Font.Normal }
                                    TapHandler { onTapped: { predictionTable.forceActiveFocus(); resultsController.selectRecordAt(row) } }
                                }
                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Escape && resultsController.hasSelectedRecord) {
                                        resultsController.closeInspector()
                                        event.accepted = true
                                        return
                                    }
                                    if (resultsController.visibleRecordCount < 1)
                                        return
                                    var current = resultsController.selectedVisibleRow
                                    var next = current
                                    if (event.key === Qt.Key_Down)
                                        next = Math.min(resultsController.visibleRecordCount - 1, current < 0 ? 0 : current + 1)
                                    else if (event.key === Qt.Key_Up)
                                        next = Math.max(0, current < 0 ? 0 : current - 1)
                                    else if (event.key === Qt.Key_Home)
                                        next = 0
                                    else if (event.key === Qt.Key_End)
                                        next = resultsController.visibleRecordCount - 1
                                    else if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) && current < 0)
                                        next = 0
                                    else
                                        return
                                    resultsController.selectRecordAt(next)
                                    positionViewAtRow(next, TableView.Contain)
                                    event.accepted = true
                                }
                                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }
                            }
                        }
                    }

                    VariantInspector {
                        id: variantInspector
                        visible: resultsController.hasSelectedRecord
                        SplitView.preferredWidth: Math.max(390, recordsWorkspace.width * 0.39)
                        SplitView.minimumWidth: 360
                        SplitView.maximumWidth: 650
                    }
                }
            }

            Item {
                id: resultsFooter
                anchors.left: parent.left
                anchors.leftMargin: 34
                anchors.right: parent.right
                anchors.rightMargin: 34
                anchors.bottom: parent.bottom
                height: 34
                Text { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; text: "Immutable predictions · Source state: " + resultsController.sourceState + " · " + resultsController.warningCount + " warnings"; color: resultsController.sourceState === "available" ? root.secondary : root.amber; font.family: "Arial"; font.pixelSize: 11 }
                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    width: Math.min(implicitWidth, parent.width * 0.62)
                    elide: Text.ElideMiddle
                    visible: exportController.message !== ""
                    text: exportController.message
                    color: exportController.messageKind === "error" ? "#A32217"
                         : exportController.messageKind === "success" ? "#1F6B4B"
                         : root.secondary
                    font.family: "Arial"
                    font.pixelSize: 11
                }
                Text { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; visible: exportController.message === ""; text: "Source Row identity preserved"; color: root.secondary; font.family: "Arial"; font.pixelSize: 11 }
            }
        }

        EvaluationWorkspace {
            id: evaluationWorkspace
            visible: sourceController.activeSurface === "evaluation"
            anchors.fill: parent
        }

        ModelPackageSettings {
            id: modelPackageSettings
            visible: sourceController.activeSurface === "settings"
            anchors.fill: parent
        }

        Rectangle {
            id: evidencePane
            visible: sourceController.activeSurface === "review"
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
