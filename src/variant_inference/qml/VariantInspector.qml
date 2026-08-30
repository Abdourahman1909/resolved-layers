/*
THESIS: Preserve exact Source Row identity while prediction and original-row evidence remain inspectable beside the active Records table; refuse modal detail views.
OWN-WORLD: Extend the Evidence Desk with white paper surfaces, cool rules, compact Arial working type, and laboratory blue only for interaction and identity emphasis.
STORY: The operator selects one prediction, verifies model-output evidence and immutable run identity, then reads the complete checksum-valid original row or truthful unavailable evidence.
FIRST VIEWPORT: A resizable right pane leads with Source Row and prediction, followed by score/threshold evidence, separate component scores, run identity, and source state.
FORM: Precisely specified local split-workspace extension; seed key variant-inspector-local-extension.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
*/

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: inspector

    color: "#FFFFFF"
    border.width: 1
    border.color: "#D8DEE8"
    radius: 3
    clip: true
    Accessible.role: Accessible.Pane
    Accessible.name: "Variant Inspector for Source Row " + resultsController.selectedSourceRow

    Rectangle {
        id: inspectorHeader
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 68
        color: "#F8FAFC"
        border.width: 1
        border.color: "#E8ECF2"

        Text {
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.top: parent.top
            anchors.topMargin: 12
            text: "Variant Inspector"
            color: "#101522"
            font.family: "Arial"
            font.pixelSize: 17
            font.weight: Font.DemiBold
        }
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 11
            text: "Source Row " + resultsController.selectedSourceRow.toLocaleString() + " · original source " + resultsController.sourceEvidenceState
            color: "#0B42E7"
            font.family: "Arial"
            font.pixelSize: 11
            font.weight: Font.DemiBold
        }
        ActionButton {
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            width: 66
            height: 32
            quiet: true
            text: "Close"
            onClicked: resultsController.closeInspector()
        }
    }

    Flickable {
        id: inspectorScroll
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: inspectorHeader.bottom
        anchors.bottom: parent.bottom
        contentWidth: width
        contentHeight: inspectorColumn.implicitHeight + 28
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        activeFocusOnTab: true
        Accessible.role: Accessible.Pane
        Accessible.name: "Scrollable Variant Inspector evidence"
        Keys.onPressed: function(event) {
            var step = 42
            var page = Math.max(120, height * 0.82)
            if (event.key === Qt.Key_Down)
                contentY = Math.min(contentHeight - height, contentY + step)
            else if (event.key === Qt.Key_Up)
                contentY = Math.max(0, contentY - step)
            else if (event.key === Qt.Key_PageDown)
                contentY = Math.min(contentHeight - height, contentY + page)
            else if (event.key === Qt.Key_PageUp)
                contentY = Math.max(0, contentY - page)
            else if (event.key === Qt.Key_Home)
                contentY = 0
            else if (event.key === Qt.Key_End)
                contentY = Math.max(0, contentHeight - height)
            else
                return
            event.accepted = true
        }

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            contentItem: Rectangle { implicitWidth: 6; radius: 3; color: "#AEB8C8" }
            background: Rectangle { color: "transparent" }
        }

        Column {
            id: inspectorColumn
            x: 18
            y: 18
            width: inspectorScroll.width - 36
            spacing: 0

            Rectangle {
                width: parent.width
                height: 66
                color: "#EEF3FF"
                border.width: 1
                border.color: "#C5D2FA"
                radius: 3

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 14
                    anchors.top: parent.top
                    anchors.topMargin: 10
                    text: "SOURCE ROW " + resultsController.selectedSourceRow.toLocaleString()
                    color: "#0B42E7"
                    font.family: "Arial"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.35
                }
                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 14
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 10
                    text: resultsController.selectedPrediction
                    color: resultsController.selectedPrediction === "Pathogenic" ? "#263B72" : "#50796F"
                    font.family: "Arial"
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                Text {
                    anchors.right: parent.right
                    anchors.rightMargin: 14
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 12
                    text: resultsController.selectedEnsembleScore.toFixed(6)
                    color: "#101522"
                    font.family: "Arial"
                    font.pixelSize: 17
                    font.weight: Font.Medium
                }
            }

            Item { width: 1; height: 20 }
            SectionTitle { text: "Prediction evidence" }
            Item { width: 1; height: 13 }
            EvidenceRow { width: parent.width; label: "Ensemble Score"; value: resultsController.selectedEnsembleScore.toFixed(6) }
            EvidenceRow { width: parent.width; label: "Release Threshold"; value: resultsController.releaseThreshold.toFixed(6); valueColor: "#8A590E" }
            EvidenceRow { width: parent.width; label: "Threshold relationship"; value: resultsController.thresholdRelationship; wrapValue: true }
            EvidenceRow { width: parent.width; label: "Model disagreement"; value: resultsController.selectedDisagreement.toFixed(6) }

            Rectangle { width: parent.width; height: 1; color: "#E8ECF2" }
            Item { width: 1; height: 18 }
            SectionTitle { text: "Component-model evidence" }
            Item { width: 1; height: 12 }
            Row {
                width: parent.width
                height: 58

                Item {
                    width: (parent.width - 1) / 2
                    height: parent.height
                    Text { anchors.left: parent.left; anchors.top: parent.top; text: "CatBoost"; color: "#303847"; font.family: "Arial"; font.pixelSize: 12; font.weight: Font.DemiBold }
                    Text { anchors.left: parent.left; anchors.bottom: parent.bottom; text: resultsController.selectedCatBoostScore.toFixed(6); color: "#101522"; font.family: "Arial"; font.pixelSize: 18; font.weight: Font.Medium }
                }
                Rectangle { width: 1; height: parent.height; color: "#D8DEE8" }
                Item {
                    width: (parent.width - 1) / 2
                    height: parent.height
                    Text { anchors.left: parent.left; anchors.leftMargin: 18; anchors.top: parent.top; text: "LightGBM"; color: "#303847"; font.family: "Arial"; font.pixelSize: 12; font.weight: Font.DemiBold }
                    Text { anchors.left: parent.left; anchors.leftMargin: 18; anchors.bottom: parent.bottom; text: resultsController.selectedLightgbmScore.toFixed(6); color: "#101522"; font.family: "Arial"; font.pixelSize: 18; font.weight: Font.Medium }
                }
            }
            Text {
                width: parent.width
                bottomPadding: 18
                text: "Component scores are separate model-output evidence. They are not biological causation, clinical evidence, or model explainability."
                color: "#566176"
                wrapMode: Text.Wrap
                font.family: "Arial"
                font.pixelSize: 11
                lineHeight: 1.22
            }

            Rectangle { width: parent.width; height: 1; color: "#D8DEE8" }
            Item { width: 1; height: 18 }
            SectionTitle { text: "Run and release identity" }
            Item { width: 1; height: 12 }
            EvidenceRow { width: parent.width; label: "Verified Run"; value: resultsController.runId; wrapValue: true }
            EvidenceRow { width: parent.width; label: "Model Package"; value: resultsController.packageName + " · " + resultsController.packageVersion; wrapValue: true }
            EvidenceRow { width: parent.width; label: "Package checksum"; value: resultsController.packageManifestChecksum; wrapValue: true }
            EvidenceRow { width: parent.width; label: "Inference Contract"; value: resultsController.contractId + " · " + resultsController.contractVersion; wrapValue: true }
            EvidenceRow { width: parent.width; label: "Contract checksum"; value: resultsController.contractChecksum; wrapValue: true }

            Rectangle { width: parent.width; height: 1; color: "#D8DEE8" }
            Item { width: 1; height: 18 }
            SectionTitle { text: "Original source row" }
            Item { width: 1; height: 12 }
            Rectangle {
                width: parent.width
                height: sourceStateColumn.implicitHeight + 20
                color: resultsController.sourceEvidenceState === "available" ? "#F0F7F4" : resultsController.sourceEvidenceState === "checking" ? "#EEF3FF" : resultsController.sourceEvidenceState === "modified" ? "#FFF5EB" : "#F8F3F1"
                border.width: 1
                border.color: resultsController.sourceEvidenceState === "available" ? "#B9D4C8" : resultsController.sourceEvidenceState === "checking" ? "#C5D2FA" : resultsController.sourceEvidenceState === "modified" ? "#E5C18F" : "#DFC5BE"
                radius: 3

                Column {
                    id: sourceStateColumn
                    x: 12
                    y: 10
                    width: parent.width - 24
                    spacing: 5
                    Text {
                        width: parent.width
                        text: resultsController.sourceEvidenceState === "available" ? "CHECKSUM-VALID SOURCE" : resultsController.sourceEvidenceState === "checking" ? "VERIFYING SOURCE" : resultsController.sourceEvidenceState.toUpperCase() + " SOURCE"
                        color: resultsController.sourceEvidenceState === "available" ? "#14804A" : resultsController.sourceEvidenceState === "checking" ? "#0B42E7" : resultsController.sourceEvidenceState === "modified" ? "#8A590E" : "#B52921"
                        font.family: "Arial"
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.35
                    }
                    Text {
                        width: parent.width
                        text: resultsController.sourceEvidenceDetail
                        color: "#303847"
                        wrapMode: Text.Wrap
                        font.family: "Arial"
                        font.pixelSize: 11
                        lineHeight: 1.2
                    }
                }
            }
            Item { width: 1; height: 12 }
            EvidenceRow { width: parent.width; label: "Expected SHA-256"; value: resultsController.sourceExpectedSha256; wrapValue: true }
            EvidenceRow { visible: resultsController.sourceEvidenceState === "modified"; width: parent.width; label: "Current SHA-256"; value: resultsController.sourceCurrentSha256; wrapValue: true; valueColor: "#8A590E" }

            Text {
                visible: resultsController.sourceEvidenceState === "available"
                width: parent.width
                topPadding: 8
                bottomPadding: 9
                text: "Complete original row · " + resultsController.sourceFieldCount.toLocaleString() + " columns"
                color: "#101522"
                font.family: "Arial"
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }

            TextField {
                id: sourceFieldSearch
                visible: resultsController.sourceEvidenceState === "available"
                width: parent.width
                height: 34
                placeholderText: "Find source field or value"
                selectByMouse: true
                font.family: "Arial"
                font.pixelSize: 11
                onTextChanged: resultsController.searchSourceFields(text)
                onActiveFocusChanged: if (activeFocus) inspectorScroll.contentY = Math.min(
                    Math.max(0, inspectorScroll.contentHeight - inspectorScroll.height),
                    Math.max(0, sourceFieldSearch.y + sourceFieldSearch.parent.y - 24)
                )
                Accessible.name: "Find a field or value in the complete original Source Row"
            }
            Item { visible: resultsController.sourceEvidenceState === "available"; width: 1; height: 9 }
            Text {
                visible: resultsController.sourceEvidenceState === "available" && resultsController.visibleSourceFieldCount !== resultsController.sourceFieldCount
                width: parent.width
                bottomPadding: 8
                text: "Showing " + resultsController.visibleSourceFieldCount.toLocaleString() + " of " + resultsController.sourceFieldCount.toLocaleString() + " source columns"
                color: "#566176"
                font.family: "Arial"
                font.pixelSize: 10
            }

            Repeater {
                model: sourceFieldModel
                delegate: Item {
                    required property string fieldName
                    required property string fieldValue
                    required property string fieldType
                    required property int index

                    width: inspectorColumn.width
                    height: Math.max(42, fieldValueText.implicitHeight + 18)
                    visible: resultsController.sourceEvidenceState === "available"

                    Rectangle { anchors.fill: parent; color: index % 2 === 0 ? "#FFFFFF" : "#FBFCFE" }
                    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: "#E8ECF2" }
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        anchors.top: parent.top
                        anchors.topMargin: 8
                        width: parent.width * 0.40 - 14
                        text: fieldName
                        color: "#303847"
                        elide: Text.ElideMiddle
                        font.family: "Arial"
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                    }
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: parent.width * 0.40
                        anchors.top: parent.top
                        anchors.topMargin: 8
                        text: fieldType
                        color: "#626C7F"
                        font.family: "Arial"
                        font.pixelSize: 9
                    }
                    Text {
                        id: fieldValueText
                        anchors.left: parent.left
                        anchors.leftMargin: parent.width * 0.54
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        anchors.top: parent.top
                        anchors.topMargin: 8
                        text: fieldValue === "" ? "<missing>" : fieldValue
                        color: fieldValue === "" ? "#626C7F" : "#101522"
                        horizontalAlignment: Text.AlignRight
                        wrapMode: Text.WrapAnywhere
                        font.family: "Arial"
                        font.pixelSize: 11
                    }
                }
            }
            Item { width: 1; height: 16 }
        }
    }
}
