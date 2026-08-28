import QtQuick

Rectangle {
    id: control

    property string text: ""
    property bool primary: false
    property bool quiet: false
    signal clicked()

    implicitHeight: 42
    implicitWidth: label.implicitWidth + 30
    activeFocusOnTab: enabled
    radius: 5
    color: !enabled ? "#E9EDF3" : primary ? (hover.hovered ? "#0B35C5" : "#0B42E7") : (hover.hovered ? "#F1F4F8" : "#FFFFFF")
    border.width: primary || quiet ? 0 : 1
    border.color: activeFocus ? "#0B42E7" : "#CCD3DE"
    opacity: enabled ? 1 : 0.72

    Text {
        id: label
        anchors.centerIn: parent
        text: control.text
        color: !control.enabled ? "#7E8798" : control.primary ? "#FFFFFF" : "#101522"
        font.family: "Arial"
        font.pixelSize: 14
        font.weight: Font.Medium
    }

    HoverHandler { id: hover; enabled: control.enabled }
    TapHandler {
        enabled: control.enabled
        onTapped: {
            control.forceActiveFocus()
            control.clicked()
        }
    }
    Keys.onPressed: function(event) {
        if (control.enabled && (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space)) {
            control.clicked()
            event.accepted = true
        }
    }
    Accessible.role: Accessible.Button
    Accessible.name: control.text
    Accessible.onPressAction: control.clicked()
}
