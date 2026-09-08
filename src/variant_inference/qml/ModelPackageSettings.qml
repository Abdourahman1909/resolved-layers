import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

// Install a Model Package without a terminal.
//
// This surface displays evidence and collects one deliberate decision. It never
// parses a manifest, hashes an artifact, or judges trust; the controller does
// that off the QML thread and reports the outcome.
Item {
    id: settings

    readonly property color ink: "#101522"
    readonly property color secondary: "#566176"
    readonly property color blue: "#0B42E7"
    readonly property color amber: "#8A590E"
    readonly property color danger: "#A32217"
    readonly property color rule: "#D8DEE8"
    readonly property color softRule: "#E8ECF2"

    function messageColor(kind) {
        if (kind === "error") return settings.danger
        if (kind === "warning") return settings.amber
        if (kind === "success") return "#1F6B4B"
        return settings.secondary
    }

    FolderDialog {
        id: packageFolderDialog
        title: "Select the Model Package folder"
        onAccepted: modelPackageController.selectPackage(selectedFolder)
    }

    Flickable {
        anchors.fill: parent
        anchors.leftMargin: 36
        anchors.rightMargin: 36
        anchors.topMargin: 28
        contentWidth: width
        contentHeight: body.implicitHeight + 48
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: AppScrollBar { }

        Column {
            id: body
            width: Math.min(parent.width, 880)
            spacing: 0

            Text {
                text: "Settings"
                color: settings.ink
                font.family: "Arial"
                font.pixelSize: 30
                font.weight: Font.Normal
            }

            Item { width: 1; height: 6 }

            Row {
                spacing: 10
                Rectangle {
                    width: 9
                    height: 9
                    radius: 5
                    anchors.verticalCenter: parent.verticalCenter
                    color: settings.messageColor(modelPackageController.messageKind)
                }
                Text {
                    text: modelPackageController.message
                    color: settings.secondary
                    font.family: "Arial"
                    font.pixelSize: 14
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Item { width: 1; height: 26 }

            // Installed ------------------------------------------------------

            Text {
                text: "INSTALLED MODEL PACKAGE"
                color: settings.blue
                font.family: "Arial"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                font.letterSpacing: 0.6
            }

            Item { width: 1; height: 12 }

            Rectangle {
                width: body.width
                implicitHeight: installedColumn.implicitHeight + 34
                radius: 6
                color: "#FBFCFD"
                border.width: 1
                border.color: settings.softRule

                Column {
                    id: installedColumn
                    x: 20
                    y: 17
                    width: parent.width - 40
                    spacing: 2

                    EvidenceRow {
                        width: parent.width
                        label: "Model Package"
                        value: modelPackageController.installedName
                        wrapValue: true
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Location"
                        value: modelPackageController.installedPath
                        wrapValue: true
                    }

                    Item { width: 1; height: 10 }

                    ActionButton {
                        text: "Remove installed package"
                        quiet: true
                        enabled: modelPackageController.hasInstalled
                        visible: modelPackageController.hasInstalled
                        onClicked: modelPackageController.removeInstalled()
                    }
                }
            }

            Item { width: 1; height: 30 }

            // Choose ---------------------------------------------------------

            Text {
                text: "CHOOSE A MODEL PACKAGE"
                color: settings.blue
                font.family: "Arial"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                font.letterSpacing: 0.6
            }

            Item { width: 1; height: 8 }

            Text {
                width: body.width
                text: "A Model Package is a folder containing a manifest and its integrity-checked "
                    + "artifacts. Loose model files and unpackaged folders are never accepted."
                color: settings.secondary
                font.family: "Arial"
                font.pixelSize: 13
                wrapMode: Text.WordWrap
                lineHeight: 1.25
            }

            Item { width: 1; height: 14 }

            ActionButton {
                text: modelPackageController.busy ? "Validating…" : "Select package folder…"
                enabled: !modelPackageController.busy
                onClicked: packageFolderDialog.open()
            }

            Item { width: 1; height: 22 }

            // Selected evidence ----------------------------------------------

            Rectangle {
                width: body.width
                visible: modelPackageController.hasSelection
                implicitHeight: selectedColumn.implicitHeight + 36
                radius: 6
                color: "#FFFFFF"
                border.width: 1
                border.color: settings.rule

                Column {
                    id: selectedColumn
                    x: 20
                    y: 18
                    width: parent.width - 40
                    spacing: 2

                    Text {
                        text: "SELECTED PACKAGE"
                        color: settings.ink
                        font.family: "Arial"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.6
                    }

                    Item { width: 1; height: 10 }

                    EvidenceRow {
                        width: parent.width
                        label: "Name"
                        value: modelPackageController.selectedName
                        wrapValue: true
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Version"
                        value: modelPackageController.selectedVersion
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Model Features"
                        value: modelPackageController.selectedFeatureCount
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Release Threshold"
                        value: modelPackageController.selectedThreshold
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Verified artifacts"
                        value: modelPackageController.selectedArtifactCount
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Manifest SHA-256"
                        value: modelPackageController.selectedChecksum
                        wrapValue: true
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Location"
                        value: modelPackageController.selectedPath
                        wrapValue: true
                    }

                    Item { width: 1; height: 14 }

                    // Trust decision. An unconfirmed package is structurally
                    // valid but nobody has vouched for it, and loading a model
                    // deserializes code, so the operator must decide.
                    Rectangle {
                        width: parent.width
                        visible: modelPackageController.needsConfirmation
                        implicitHeight: confirmColumn.implicitHeight + 28
                        radius: 5
                        color: "#FDF8EF"
                        border.width: 1
                        border.color: "#E4D2AC"

                        Column {
                            id: confirmColumn
                            x: 16
                            y: 14
                            width: parent.width - 32
                            spacing: 10

                            Text {
                                width: parent.width
                                text: "This Model Package is not recognised. Confirm that you trust "
                                    + "this exact manifest checksum before it is used. Loading a model "
                                    + "runs code from the package, so only confirm packages you received "
                                    + "from a source you trust."
                                color: settings.amber
                                font.family: "Arial"
                                font.pixelSize: 13
                                wrapMode: Text.WordWrap
                                lineHeight: 1.25
                            }

                            ActionButton {
                                text: "Confirm this checksum"
                                onClicked: modelPackageController.confirmSelected()
                            }
                        }
                    }

                    Item {
                        width: 1
                        height: modelPackageController.needsConfirmation ? 14 : 0
                    }

                    ActionButton {
                        text: "Install this Model Package"
                        primary: true
                        enabled: modelPackageController.canInstall
                        onClicked: modelPackageController.installSelected()
                    }
                }
            }

            Item { width: 1; height: 26 }

            Text {
                text: "ABOUT"
                color: settings.blue
                font.family: "Arial"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                font.letterSpacing: 0.6
            }

            Item { width: 1; height: 12 }

            Rectangle {
                width: body.width
                implicitHeight: aboutColumn.implicitHeight + 34
                radius: 6
                color: "#FBFCFD"
                border.width: 1
                border.color: settings.softRule

                Column {
                    id: aboutColumn
                    x: 20
                    y: 17
                    width: parent.width - 40
                    spacing: 2

                    EvidenceRow {
                        width: parent.width
                        label: "Application"
                        value: "Resolved Layers " + modelPackageController.applicationVersion
                    }
                    EvidenceRow {
                        width: parent.width
                        label: "Owner"
                        value: "Computational Health Lab"
                    }
                }
            }

            Item { width: 1; height: 26 }

            Text {
                width: body.width
                text: "Model Packages are supplied separately and are never bundled with the "
                    + "application. Installing one records its location and checksum only; no model "
                    + "artifact is copied."
                color: settings.secondary
                font.family: "Arial"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                lineHeight: 1.25
            }
        }
    }
}
