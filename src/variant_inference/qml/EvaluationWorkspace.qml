import QtQuick
import QtQuick.Controls

/*
THESIS: Evaluation is an authorized evidence ledger, never a KPI dashboard or automatic label guess.
OWN-WORLD: The incumbent Evidence Desk uses white paper surfaces, cool rules, compact Arial type, and one blue interaction voice.
STORY: Verify the source, authorize exact raw mappings, read the disclosed denominator and observed metrics, then inspect exact error rows.
FIRST VIEWPORT: Run identity and authorization lead; a ruled metric ledger, confusion matrix, cohorts, and traceability evidence follow without decorative charts.
FORM: Operate-mode extension of the established Evidence Desk; no new visual-world seed.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
*/

Item {
    id: evaluationRoot

    readonly property color ink: "#101522"
    readonly property color secondary: "#566176"
    readonly property color blue: "#0B42E7"
    readonly property color pathogenic: "#263B72"
    readonly property color benign: "#6D9B91"
    readonly property color amber: "#8A590E"
    readonly property color error: "#B52921"
    readonly property color rule: "#D8DEE8"
    readonly property color softRule: "#E8ECF2"

    function reviewCoverageDraft() {
        evaluationController.reviewCoverage(
            evaluationPathogenic.currentIndex > 0 ? evaluationPathogenic.currentText : "",
            evaluationBenign.currentIndex > 0 ? evaluationBenign.currentText : ""
        )
    }

    Flickable {
        id: evaluationScroll
        anchors.fill: parent
        contentWidth: width
        contentHeight: contentColumn.implicitHeight + 56
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        activeFocusOnTab: true
        Accessible.role: Accessible.Pane
        Accessible.name: "Observed Evaluation workspace"
        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_PageDown) {
                contentY = Math.min(contentHeight - height, contentY + height * 0.82)
                event.accepted = true
            } else if (event.key === Qt.Key_PageUp) {
                contentY = Math.max(0, contentY - height * 0.82)
                event.accepted = true
            } else if (event.key === Qt.Key_Home) {
                contentY = 0
                event.accepted = true
            } else if (event.key === Qt.Key_End) {
                contentY = Math.max(0, contentHeight - height)
                event.accepted = true
            }
        }

        ScrollBar.vertical: AppScrollBar { }

        Column {
            id: contentColumn
            x: 34
            y: 23
            width: evaluationScroll.width - 68
            spacing: 17

            Item {
                width: parent.width
                height: 44

                Text {
                    id: evaluationTitle
                    anchors.left: parent.left
                    anchors.top: parent.top
                    text: "Observed Evaluation"
                    color: evaluationRoot.ink
                    font.family: "Arial"
                    font.pixelSize: 27
                    font.weight: Font.Medium
                }

                Rectangle {
                    anchors.left: evaluationTitle.right
                    anchors.leftMargin: 17
                    anchors.verticalCenter: evaluationTitle.verticalCenter
                    width: evaluationStateText.implicitWidth + 28
                    height: 24
                    color: evaluationController.hasReport ? "#EDF7F2" : evaluationController.sourceAvailable ? "#F1F4F8" : "#FFF5E7"
                    radius: 12
                    Text {
                        id: evaluationStateText
                        anchors.centerIn: parent
                        text: evaluationController.busy ? "VERIFYING EVIDENCE" : evaluationController.hasReport ? "AUTHORIZED LABELS" : evaluationController.sourceAvailable ? "AUTHORIZATION REQUIRED" : evaluationController.sourceState.toUpperCase()
                        color: evaluationController.hasReport ? "#147A4A" : evaluationController.sourceAvailable ? evaluationRoot.secondary : evaluationRoot.amber
                        font.family: "Arial"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 0.45
                    }
                }

                Text {
                    anchors.right: parent.right
                    anchors.baseline: evaluationTitle.baseline
                    width: Math.min(430, parent.width * 0.38)
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideMiddle
                    text: resultsController.runId
                    color: evaluationRoot.secondary
                    font.family: "Arial"
                    font.pixelSize: 11
                }
            }

            Text {
                width: parent.width
                text: "Observed performance on this explicitly authorized labeled dataset. These values are not competition-final performance, biological causation, clinical validation, or threshold optimization."
                color: evaluationRoot.secondary
                wrapMode: Text.Wrap
                font.family: "Arial"
                font.pixelSize: 12
                lineHeight: 1.2
            }

            Rectangle {
                width: parent.width
                height: 72
                color: "#FAFBFD"
                border.width: 1
                border.color: evaluationRoot.rule
                radius: 3

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    Repeater {
                        model: [
                            { label: "Source Dataset", value: resultsController.sourceName, share: 0.20 },
                            { label: "Model Package", value: resultsController.packageName + " " + resultsController.packageVersion, share: 0.21 },
                            { label: "Inference Contract", value: resultsController.contractId + " · " + resultsController.contractVersion, share: 0.21 },
                            { label: "Release Threshold", value: resultsController.releaseThreshold.toFixed(6), share: 0.14 },
                            { label: "Evaluated Denominator", value: evaluationController.hasReport ? evaluationController.evaluatedCount.toLocaleString() + " of " + evaluationController.totalCount.toLocaleString() : "Not calculated", share: 0.24 }
                        ]
                        Item {
                            required property var modelData
                            required property int index
                            width: parent.width * modelData.share
                            height: parent.height
                            Text { x: 10; y: 15; width: parent.width - 22; text: modelData.value; elide: Text.ElideMiddle; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 12; font.weight: Font.DemiBold }
                            Text { x: 10; y: 42; width: parent.width - 22; text: modelData.label; elide: Text.ElideRight; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10 }
                            Rectangle { visible: index > 0; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; width: 1; height: 40; color: evaluationRoot.rule }
                        }
                    }
                }
            }

            Rectangle {
                width: parent.width
                height: authorizationContent.implicitHeight + 30
                color: "#FFFFFF"
                border.width: 1
                border.color: evaluationController.sourceAvailable ? evaluationRoot.rule : "#E5C997"
                radius: 3

                Column {
                    id: authorizationContent
                    x: 17
                    y: 15
                    width: parent.width - 34
                    spacing: 10

                    Row {
                        width: parent.width
                        height: 24
                        spacing: 12
                        SectionTitle { id: authorizationTitle; width: 210; text: "Ground-Truth Authorization" }
                        Text {
                            width: parent.width - authorizationTitle.width - 158
                            text: evaluationController.busy ? evaluationController.busyMessage : evaluationController.message
                            color: evaluationController.errorMessage ? evaluationRoot.error : evaluationRoot.secondary
                            elide: Text.ElideRight
                            font.family: "Arial"
                            font.pixelSize: 11
                        }
                        ActionButton {
                            width: 122
                            height: 28
                            quiet: true
                            text: "Refresh source"
                            enabled: !evaluationController.busy
                            onClicked: evaluationController.refreshSource()
                        }
                    }

                    Text {
                        visible: !evaluationController.sourceAvailable
                        width: parent.width
                        text: evaluationController.sourceDetail
                        color: evaluationRoot.amber
                        wrapMode: Text.Wrap
                        font.family: "Arial"
                        font.pixelSize: 12
                    }

                    Row {
                        visible: evaluationController.sourceAvailable
                        width: parent.width
                        height: 52
                        spacing: 12

                        Column {
                            width: Math.max(210, (parent.width - 166) * 0.34)
                            spacing: 5
                            Text { text: "LABEL COLUMN"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 0.35 }
                            SelectField {
                                id: evaluationLabelColumn
                                width: parent.width
                                height: 34
                                model: ["Select label column"].concat(evaluationController.labelColumns)
                                currentIndex: Math.max(0, model.indexOf(evaluationController.selectedLabelColumn))
                                Accessible.name: "Evaluation label column"
                                onActivated: evaluationController.selectLabelColumn(currentIndex === 0 ? "" : currentText)
                            }
                        }

                        Column {
                            width: Math.max(180, (parent.width - 166) * 0.28)
                            spacing: 5
                            Text { text: "PATHOGENIC RAW VALUE"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 0.35 }
                            SelectField {
                                id: evaluationPathogenic
                                width: parent.width
                                height: 34
                                enabled: evaluationController.selectedLabelColumn !== "" && !evaluationController.busy
                                model: ["Select exact raw value"].concat(evaluationController.labelValues)
                                currentIndex: Math.max(0, model.indexOf(evaluationController.pathogenicMapping))
                                Accessible.name: "Raw value mapped to Pathogenic"
                                onActivated: evaluationRoot.reviewCoverageDraft()
                            }
                        }

                        Column {
                            width: Math.max(180, (parent.width - 166) * 0.28)
                            spacing: 5
                            Text { text: "BENIGN RAW VALUE"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 0.35 }
                            SelectField {
                                id: evaluationBenign
                                width: parent.width
                                height: 34
                                enabled: evaluationController.selectedLabelColumn !== "" && !evaluationController.busy
                                model: ["Select exact raw value"].concat(evaluationController.labelValues)
                                currentIndex: Math.max(0, model.indexOf(evaluationController.benignMapping))
                                Accessible.name: "Raw value mapped to Benign"
                                onActivated: evaluationRoot.reviewCoverageDraft()
                            }
                        }

                        ActionButton {
                            anchors.bottom: parent.bottom
                            width: 130
                            height: 34
                            primary: true
                            text: evaluationController.hasReport ? "Re-authorize" : "Authorize"
                            enabled: evaluationController.hasCoveragePreview && !evaluationController.busy && evaluationPathogenic.currentIndex > 0 && evaluationBenign.currentIndex > 0 && evaluationPathogenic.currentText !== evaluationBenign.currentText
                            onClicked: evaluationController.authorizeEvaluation(evaluationPathogenic.currentText, evaluationBenign.currentText)
                        }
                    }

                    Rectangle {
                        visible: evaluationController.hasCoveragePreview && !evaluationController.hasReport
                        width: parent.width
                        height: 42
                        color: "#F1F4F8"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3
                        Accessible.role: Accessible.StaticText
                        Accessible.name: "Proposed label coverage: " + evaluationController.previewEvaluatedCount + " valid of " + evaluationController.previewTotalCount + ", " + evaluationController.previewMissingCount + " missing, " + evaluationController.previewUnrecognizedCount + " unrecognized. Review this coverage before authorizing Evaluation."
                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - 24
                            text: "Review proposed coverage before authorization: " + evaluationController.previewEvaluatedCount.toLocaleString() + " valid of " + evaluationController.previewTotalCount.toLocaleString() + " · " + evaluationController.previewMissingCount.toLocaleString() + " missing · " + evaluationController.previewUnrecognizedCount.toLocaleString() + " unrecognized"
                            color: evaluationRoot.ink
                            elide: Text.ElideRight
                            font.family: "Arial"
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }
                    }

                    Row {
                        visible: evaluationController.hasReport
                        width: parent.width
                        height: 28
                        spacing: 14
                        Text { anchors.verticalCenter: parent.verticalCenter; text: "Authorized: " + evaluationController.selectedLabelColumn + " · “" + evaluationController.pathogenicMapping + "” → Pathogenic · “" + evaluationController.benignMapping + "” → Benign"; color: "#147A4A"; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.DemiBold }
                        ActionButton { width: 142; height: 28; quiet: true; text: "Clear authorization"; onClicked: evaluationController.clearAuthorization() }
                    }
                }
            }

            Item {
                visible: evaluationController.hasReport
                width: parent.width
                height: Math.max(reportLeft.implicitHeight, reportRight.implicitHeight)

                Column {
                    id: reportLeft
                    anchors.left: parent.left
                    anchors.top: parent.top
                    width: parent.width * 0.64
                    spacing: 17

                    Rectangle {
                        width: parent.width
                        height: 104
                        color: "#FFFFFF"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3

                        Row {
                            anchors.fill: parent
                            Repeater {
                                model: evaluationMetricModel
                                delegate: Item {
                                    required property string key
                                    required property string label
                                    required property string display
                                    required property string definition
                                    required property bool defined
                                    required property int index
                                    width: parent.width / 5
                                    height: parent.height
                                    Accessible.role: Accessible.StaticText
                                    Accessible.name: label + ": " + display + ". " + definition
                                    Text { x: 13; y: 16; width: parent.width - 26; text: label; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.DemiBold }
                                    Text { x: 13; y: 39; width: parent.width - 26; text: display; color: defined ? (key === "f1" ? evaluationRoot.blue : evaluationRoot.ink) : evaluationRoot.amber; font.family: "Arial"; font.pixelSize: key === "f1" ? 24 : 20; font.weight: Font.Medium }
                                    Text { x: 13; y: 72; width: parent.width - 26; text: definition; color: evaluationRoot.secondary; elide: Text.ElideRight; font.family: "Arial"; font.pixelSize: 9 }
                                    Rectangle { visible: index > 0; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; width: 1; height: 70; color: evaluationRoot.softRule }
                                }
                            }
                        }
                    }

                    // Group breakdown. The competition combines panels by
                    // weighting each equally, so a healthy pooled figure can
                    // conceal a weak group. Grouping is opt-in; no column is
                    // chosen automatically, exactly as with the label column.
                    Rectangle {
                        id: groupPanel
                        width: parent.width
                        implicitHeight: groupColumn.implicitHeight + 34
                        color: "#FFFFFF"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3

                        Column {
                            id: groupColumn
                            x: 17
                            y: 16
                            width: parent.width - 34
                            spacing: 0

                            SectionTitle { text: "Group Breakdown" }

                            Item { width: 1; height: 5 }

                            Text {
                                width: parent.width
                                text: "Observed metrics computed inside each group separately. "
                                    + "The mean weights every group equally regardless of size."
                                color: evaluationRoot.secondary
                                font.family: "Arial"
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }

                            Item { width: 1; height: 12 }

                            SelectField {
                                id: groupColumnSelect
                                width: Math.min(parent.width, 320)
                                height: 34
                                model: ["No grouping"].concat(evaluationController.groupColumns)
                                currentIndex: Math.max(0, model.indexOf(evaluationController.groupColumn))
                                enabled: evaluationController.hasReport && !evaluationController.busy
                                Accessible.name: "Group observed metrics by a source column"
                                onActivated: evaluationController.selectGroupColumn(currentIndex === 0 ? "" : currentText)
                            }

                            Item { width: 1; height: 14 }

                            // Equal-weighted means, shown only once grouping exists.
                            Row {
                                visible: evaluationController.hasGrouping
                                spacing: 26
                                Repeater {
                                    model: [
                                        { label: "Mean F1", value: evaluationController.meanGroupF1 },
                                        { label: "Mean MCC", value: evaluationController.meanGroupMcc },
                                        { label: "Groups", value: evaluationController.groupCount.toString() }
                                    ]
                                    Column {
                                        required property var modelData
                                        spacing: 2
                                        Text { text: modelData.label; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold }
                                        Text { text: modelData.value; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 18; font.weight: Font.Medium }
                                    }
                                }
                            }

                            Item { width: 1; height: evaluationController.hasGrouping ? 14 : 0 }

                            // Header row
                            Row {
                                visible: evaluationController.hasGrouping
                                width: parent.width
                                Repeater {
                                    model: [
                                        { text: "Group", share: 0.24, align: Text.AlignLeft },
                                        { text: "Evaluated", share: 0.13, align: Text.AlignRight },
                                        { text: "TP", share: 0.08, align: Text.AlignRight },
                                        { text: "FP", share: 0.08, align: Text.AlignRight },
                                        { text: "FN", share: 0.08, align: Text.AlignRight },
                                        { text: "TN", share: 0.08, align: Text.AlignRight },
                                        { text: "F1", share: 0.155, align: Text.AlignRight },
                                        { text: "MCC", share: 0.155, align: Text.AlignRight }
                                    ]
                                    Text {
                                        required property var modelData
                                        width: groupColumn.width * modelData.share
                                        text: modelData.text
                                        horizontalAlignment: modelData.align
                                        color: evaluationRoot.secondary
                                        font.family: "Arial"
                                        font.pixelSize: 10
                                        font.weight: Font.DemiBold
                                    }
                                }
                            }

                            Rectangle {
                                visible: evaluationController.hasGrouping
                                width: parent.width
                                height: 1
                                color: evaluationRoot.rule
                            }

                            Repeater {
                                model: evaluationController.hasGrouping ? evaluationGroupModel : null
                                delegate: Row {
                                    required property string groupValue
                                    required property int evaluated
                                    required property int truePositive
                                    required property int falsePositive
                                    required property int falseNegative
                                    required property int trueNegative
                                    required property string f1
                                    required property string mcc
                                    width: groupColumn.width
                                    height: 27
                                    Accessible.role: Accessible.Row
                                    Accessible.name: groupValue + ": F1 " + f1 + ", MCC " + mcc
                                        + ", " + evaluated + " evaluated records"

                                    Text { width: groupColumn.width * 0.24; anchors.verticalCenter: parent.verticalCenter; text: groupValue; elide: Text.ElideRight; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.DemiBold }
                                    Text { width: groupColumn.width * 0.13; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: evaluated.toLocaleString(); color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 11 }
                                    Text { width: groupColumn.width * 0.08; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: truePositive; color: evaluationRoot.pathogenic; font.family: "Arial"; font.pixelSize: 11 }
                                    Text { width: groupColumn.width * 0.08; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: falsePositive; color: evaluationRoot.error; font.family: "Arial"; font.pixelSize: 11 }
                                    Text { width: groupColumn.width * 0.08; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: falseNegative; color: evaluationRoot.error; font.family: "Arial"; font.pixelSize: 11 }
                                    Text { width: groupColumn.width * 0.08; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: trueNegative; color: evaluationRoot.benign; font.family: "Arial"; font.pixelSize: 11 }
                                    Text { width: groupColumn.width * 0.155; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: f1; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.Medium }
                                    Text { width: groupColumn.width * 0.155; anchors.verticalCenter: parent.verticalCenter; horizontalAlignment: Text.AlignRight; text: mcc; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.Medium }
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: 238
                        color: "#FFFFFF"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3

                        SectionTitle { id: confusionTitle; x: 17; y: 16; text: "Traceable Confusion Matrix" }
                        Text { x: 17; y: 42; text: "Rows are predictions · columns are authorized Ground Truth"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10 }

                        Item {
                            x: 17
                            y: 68
                            width: parent.width - 34
                            height: 150

                            Text { x: 0; y: 28; width: 106; text: "Predicted\nPathogenic"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; horizontalAlignment: Text.AlignRight }
                            Text { x: 0; y: 98; width: 106; text: "Predicted\nBenign"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; horizontalAlignment: Text.AlignRight }
                            Text { x: 124; y: 0; width: (parent.width - 124) / 2; text: "Ground Truth Pathogenic"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; font.weight: Font.DemiBold }
                            Text { x: 124 + (parent.width - 124) / 2; y: 0; width: (parent.width - 124) / 2; text: "Ground Truth Benign"; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; font.weight: Font.DemiBold }

                            Repeater {
                                model: [
                                    { xShare: 0, yPos: 22, label: "TP", value: evaluationController.truePositive, color: evaluationRoot.pathogenic },
                                    { xShare: 0.5, yPos: 22, label: "FP", value: evaluationController.falsePositive, color: evaluationRoot.error },
                                    { xShare: 0, yPos: 88, label: "FN", value: evaluationController.falseNegative, color: evaluationRoot.error },
                                    { xShare: 0.5, yPos: 88, label: "TN", value: evaluationController.trueNegative, color: evaluationRoot.benign }
                                ]
                                Rectangle {
                                    required property var modelData
                                    x: 124 + (parent.width - 124) * modelData.xShare
                                    y: modelData.yPos
                                    width: (parent.width - 124) / 2
                                    height: 58
                                    color: "#FAFBFD"
                                    border.width: 1
                                    border.color: evaluationRoot.rule
                                    Text { x: 12; anchors.verticalCenter: parent.verticalCenter; text: modelData.label; color: modelData.color; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.Bold }
                                    Text { anchors.right: parent.right; anchors.rightMargin: 14; anchors.verticalCenter: parent.verticalCenter; text: modelData.value.toLocaleString(); color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 20; font.weight: Font.Medium }
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: 78
                        color: "#FAFBFD"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3
                        Text { x: 16; y: 14; text: evaluationController.evaluatedCount.toLocaleString() + " of " + evaluationController.totalCount.toLocaleString() + " Source Rows evaluated"; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 13; font.weight: Font.DemiBold }
                        Text { x: 16; y: 39; text: evaluationController.excludedCount.toLocaleString() + " excluded · " + evaluationController.missingCount.toLocaleString() + " missing labels · " + evaluationController.unrecognizedCount.toLocaleString() + " unrecognized raw values"; color: evaluationController.excludedCount > 0 ? evaluationRoot.amber : evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 11 }
                    }
                }

                Column {
                    id: reportRight
                    anchors.right: parent.right
                    anchors.top: parent.top
                    width: parent.width * 0.34
                    spacing: 17

                    Rectangle {
                        width: parent.width
                        height: 288
                        color: "#FFFFFF"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3
                        SectionTitle { id: cohortsTitle; x: 17; y: 16; text: "Evaluation Cohorts" }
                        Text { x: 17; y: 42; width: parent.width - 34; text: "Open exact Source Rows in Records, then select any row for the existing Variant Inspector."; color: evaluationRoot.secondary; wrapMode: Text.Wrap; font.family: "Arial"; font.pixelSize: 10 }
                        ListView {
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            ScrollBar.vertical: AppScrollBar { }
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            anchors.top: parent.top
                            anchors.topMargin: 78
                            height: 196
                            model: evaluationCohortModel
                            interactive: false
                            delegate: Item {
                                required property string key
                                required property string title
                                required property string detail
                                required property int count
                                width: ListView.view.width
                                height: 49
                                Text { x: 6; y: 7; width: parent.width - 126; text: title; elide: Text.ElideRight; color: evaluationRoot.ink; font.family: "Arial"; font.pixelSize: 11; font.weight: Font.DemiBold }
                                Text { x: 6; y: 27; width: parent.width - 126; text: detail; elide: Text.ElideRight; color: evaluationRoot.secondary; font.family: "Arial"; font.pixelSize: 9 }
                                ActionButton { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; width: 108; height: 29; quiet: true; text: "Inspect " + count; enabled: count > 0; onClicked: sourceController.inspectEvaluationCohort(key) }
                                Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: evaluationRoot.softRule }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: evidenceColumn.implicitHeight + 30
                        color: "#FAFBFD"
                        border.width: 1
                        border.color: evaluationRoot.rule
                        radius: 3

                        Column {
                            id: evidenceColumn
                            x: 17
                            y: 15
                            width: parent.width - 34
                            spacing: 8
                            SectionTitle { text: "Calculation Evidence" }
                            EvidenceRow { width: parent.width; label: "Run"; value: resultsController.runId; wrapValue: true }
                            EvidenceRow { width: parent.width; label: "Source state"; value: evaluationController.sourceState; valueColor: evaluationController.sourceAvailable ? "#147A4A" : evaluationRoot.amber }
                            EvidenceRow { width: parent.width; label: "Source SHA-256"; value: evaluationController.expectedSha256; wrapValue: true }
                            EvidenceRow { width: parent.width; label: "Label column"; value: evaluationController.selectedLabelColumn; wrapValue: true }
                            EvidenceRow { width: parent.width; label: "Raw mappings"; value: evaluationController.pathogenicMapping + " → P · " + evaluationController.benignMapping + " → B"; wrapValue: true }
                            EvidenceRow { width: parent.width; label: "Threshold"; value: resultsController.releaseThreshold.toFixed(6) + " · fixed" }
                            EvidenceRow { width: parent.width; label: "Contract checksum"; value: resultsController.contractChecksum; wrapValue: true }
                            Text { width: parent.width; text: "Undefined is shown whenever a metric formula has a zero denominator. No ambiguous Source Row is silently included, and no threshold is changed here."; color: evaluationRoot.secondary; wrapMode: Text.Wrap; font.family: "Arial"; font.pixelSize: 10; lineHeight: 1.2 }
                        }
                    }
                }
            }

            Rectangle {
                visible: !evaluationController.hasReport
                width: parent.width
                height: 130
                color: "#FAFBFD"
                border.width: 1
                border.color: evaluationRoot.rule
                radius: 3
                SectionTitle { x: 18; y: 17; text: "Metrics Withheld" }
                Text {
                    x: 18
                    y: 48
                    width: parent.width - 36
                    text: evaluationController.sourceAvailable
                        ? "No observed metric has been calculated. Complete Ground-Truth Authorization above. Missing or unrecognized labels will remain excluded and disclosed rather than silently dropped."
                        : "Evaluation is disabled until the archived Source Dataset is present and its SHA-256 checksum matches the immutable Verified Run. Predictions remain available in Results, but labels and metrics are not read from an unavailable source."
                    color: evaluationRoot.secondary
                    wrapMode: Text.Wrap
                    font.family: "Arial"
                    font.pixelSize: 12
                    lineHeight: 1.25
                }
            }

            Text {
                width: parent.width
                text: "Observed Evaluation only · fixed Release Threshold · Source Row identity preserved · no clinical validation claim"
                color: evaluationRoot.secondary
                font.family: "Arial"
                font.pixelSize: 11
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
