import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

// Competition Submission.
//
// Separate from Evaluation by design: Evaluation needs authorized labels and
// reports observed performance, while this surface prepares an unlabelled run
// for external scoring and never shows a metric. The organisers score the
// uploaded file automatically, so everything here exists to make sure the file
// they receive is one their system accepts.
Item {
    id: submission

    readonly property color ink: "#101522"
    readonly property color secondary: "#566176"
    readonly property color blue: "#0B42E7"
    readonly property color amber: "#8A590E"
    readonly property color success: "#14804A"
    readonly property color error: "#B52921"
    readonly property color rule: "#D8DEE8"
    readonly property color softRule: "#E8ECF2"

    function messageColor(kind) {
        if (kind === "error") return submission.error
        if (kind === "warning") return submission.amber
        if (kind === "success") return submission.success
        return submission.secondary
    }

    FileDialog {
        id: submissionDialog
        title: "Write the competition submission"
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        nameFilters: ["JSON files (*.json)"]
        currentFile: "file:" + submissionController.suggestedFileName
        onAccepted: submissionController.writeSubmission(selectedFile)
    }

    Flickable {
        anchors.fill: parent
        anchors.leftMargin: 34
        anchors.rightMargin: 34
        anchors.topMargin: 26
        contentWidth: width
        contentHeight: body.implicitHeight + 44
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: AppScrollBar { }

        Column {
            id: body
            width: Math.min(parent.width, 940)
            spacing: 0

            Row {
                spacing: 14
                Text {
                    text: "Competition Submission"
                    color: submission.ink
                    font.family: "Arial"
                    font.pixelSize: 30
                    anchors.verticalCenter: parent.verticalCenter
                }
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: levelText.implicitWidth + 20
                    height: 24
                    radius: 12
                    color: "#EEF3FF"
                    Text {
                        id: levelText
                        anchors.centerIn: parent
                        text: submissionController.competitionLevel
                        color: submission.blue
                        font.family: "Arial"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 0.5
                    }
                }
            }

            Item { width: 1; height: 8 }

            Text {
                width: body.width
                text: "Prepares one completed Verified Run for external Organizer Scoring. "
                    + "No observed metric is shown here: the organisers hold the labels and "
                    + "calculate the score themselves."
                color: submission.secondary
                font.family: "Arial"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                lineHeight: 1.25
            }

            Item { width: 1; height: 22 }

            // Team identity ---------------------------------------------------

            Text {
                text: "SUBMISSION HEADER"
                color: submission.blue
                font.family: "Arial"; font.pixelSize: 12
                font.weight: Font.DemiBold; font.letterSpacing: 0.6
            }

            Item { width: 1; height: 10 }

            Rectangle {
                width: body.width
                implicitHeight: headerColumn.implicitHeight + 32
                radius: 4
                color: "#FBFCFE"
                border.width: 1
                border.color: submission.softRule

                Column {
                    id: headerColumn
                    x: 18; y: 16
                    width: parent.width - 36
                    spacing: 1

                    EvidenceRow { width: parent.width; label: "Team name"; value: submissionController.teamName }
                    EvidenceRow { width: parent.width; label: "Team ID"; value: submissionController.teamId }
                    EvidenceRow { width: parent.width; label: "Application ID"; value: submissionController.applicationId }
                    EvidenceRow { width: parent.width; label: "Competition level"; value: submissionController.competitionLevel }
                    EvidenceRow { width: parent.width; label: "Format profile"; value: submissionController.profileId }
                }
            }

            Item { width: 1; height: 24 }

            // Column mapping --------------------------------------------------

            Text {
                text: "RECORD MAPPING"
                color: submission.blue
                font.family: "Arial"; font.pixelSize: 12
                font.weight: Font.DemiBold; font.letterSpacing: 0.6
            }

            Item { width: 1; height: 8 }

            Text {
                width: body.width
                text: "Each submitted record carries the organisers' own identifier and panel, "
                    + "copied from the Source Dataset unchanged. Identifiers are never generated."
                color: submission.secondary
                font.family: "Arial"; font.pixelSize: 12
                wrapMode: Text.WordWrap; lineHeight: 1.25
            }

            Item { width: 1; height: 12 }

            Row {
                spacing: 18

                Column {
                    spacing: 6
                    Text { text: "IDENTIFIER COLUMN"; color: submission.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 0.4 }
                    SelectField {
                        width: 260; height: 34
                        enabled: submissionController.hasRun && !submissionController.busy
                        // A sentinel first entry, so an unchosen column never
                        // renders as though the first column were selected.
                        model: ["Choose identifier column"].concat(submissionController.sourceColumns)
                        currentIndex: Math.max(0, model.indexOf(submissionController.identifierColumn))
                        Accessible.name: "Record identifier column"
                        onActivated: submissionController.selectIdentifierColumn(currentIndex === 0 ? "" : currentText)
                    }
                }

                Column {
                    spacing: 6
                    Text { text: "PANEL COLUMN"; color: submission.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 0.4 }
                    SelectField {
                        width: 260; height: 34
                        enabled: submissionController.hasRun && !submissionController.busy
                        model: ["Choose panel column"].concat(submissionController.sourceColumns)
                        currentIndex: Math.max(0, model.indexOf(submissionController.panelColumn))
                        Accessible.name: "Panel column"
                        onActivated: submissionController.selectPanelColumn(currentIndex === 0 ? "" : currentText)
                    }
                }

                Column {
                    spacing: 6
                    Text { text: "RECORDS"; color: submission.secondary; font.family: "Arial"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 0.4 }
                    Text {
                        height: 34
                        verticalAlignment: Text.AlignVCenter
                        text: submissionController.recordCount.toLocaleString()
                        color: submission.ink
                        font.family: "Arial"; font.pixelSize: 20; font.weight: Font.Medium
                    }
                }
            }

            Item { width: 1; height: 24 }

            // Write -----------------------------------------------------------

            Text {
                text: "WRITE SUBMISSION"
                color: submission.blue
                font.family: "Arial"; font.pixelSize: 12
                font.weight: Font.DemiBold; font.letterSpacing: 0.6
            }

            Item { width: 1; height: 8 }

            Text {
                width: body.width
                text: "The file is checked against every published rule before it is written. "
                    + "A submission that would be rejected is refused here instead, while "
                    + "there is still time to correct it."
                color: submission.secondary
                font.family: "Arial"; font.pixelSize: 12
                wrapMode: Text.WordWrap; lineHeight: 1.25
            }

            Item { width: 1; height: 14 }

            Row {
                spacing: 16
                ActionButton {
                    primary: true
                    text: submissionController.busy ? "Checking…" : "Write submission file…"
                    enabled: submissionController.canWrite
                    Accessible.description: "Validate and write the competition submission JSON"
                    onClicked: submissionDialog.open()
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: submissionController.suggestedFileName
                    color: submission.secondary
                    font.family: "Arial"; font.pixelSize: 12
                }
            }

            Item { width: 1; height: 16 }

            Row {
                spacing: 10
                Rectangle {
                    width: 9; height: 9; radius: 5
                    anchors.verticalCenter: parent.verticalCenter
                    color: submission.messageColor(submissionController.messageKind)
                }
                Text {
                    width: body.width - 24
                    anchors.verticalCenter: parent.verticalCenter
                    text: submissionController.message
                    color: submissionController.messageKind === "neutral"
                         ? submission.secondary
                         : submission.messageColor(submissionController.messageKind)
                    font.family: "Arial"; font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }

            Item { width: 1; height: submissionController.checks.length > 0 ? 18 : 0 }

            // Checks performed ------------------------------------------------

            Rectangle {
                visible: submissionController.checks.length > 0
                width: body.width
                implicitHeight: checksColumn.implicitHeight + 30
                radius: 4
                color: "#F5FBF7"
                border.width: 1
                border.color: "#CFE6D9"

                Column {
                    id: checksColumn
                    x: 18; y: 15
                    width: parent.width - 36
                    spacing: 6

                    Text {
                        text: "CHECKED BEFORE WRITING"
                        color: submission.success
                        font.family: "Arial"; font.pixelSize: 10
                        font.weight: Font.DemiBold; font.letterSpacing: 0.5
                    }

                    Repeater {
                        model: submissionController.checks
                        Row {
                            required property string modelData
                            spacing: 8
                            Text { text: "✓"; color: submission.success; font.family: "Arial"; font.pixelSize: 12; font.weight: Font.Bold }
                            Text { text: modelData; color: submission.ink; font.family: "Arial"; font.pixelSize: 12 }
                        }
                    }

                    Item { width: 1; height: 2 }

                    Text {
                        visible: submissionController.writtenPath !== ""
                        width: parent.width
                        text: submissionController.writtenPath
                        color: submission.secondary
                        font.family: "Arial"; font.pixelSize: 11
                        elide: Text.ElideMiddle
                    }
                }
            }

            Item { width: 1; height: 26 }

            Text {
                width: body.width
                text: "Upload this file to the organisers' web system. Uploading more than once "
                    + "is permitted; the last file their system validates is the official "
                    + "submission, and a rejected upload does not invalidate an earlier valid one."
                color: submission.secondary
                font.family: "Arial"; font.pixelSize: 11
                wrapMode: Text.WordWrap; lineHeight: 1.25
            }
        }
    }
}
