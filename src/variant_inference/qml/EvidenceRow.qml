import QtQuick

Item {
    id: row

    property string label: ""
    property string value: "—"
    property bool wrapValue: false
    property color valueColor: "#111827"

    implicitHeight: Math.max(labelText.implicitHeight, valueText.implicitHeight) + 7

    Text {
        id: labelText
        width: parent.width * 0.46
        anchors.left: parent.left
        anchors.top: parent.top
        text: row.label
        color: "#303847"
        font.family: "Arial"
        font.pixelSize: 13
        lineHeight: 1.15
    }

    Text {
        id: valueText
        width: parent.width * 0.52
        anchors.right: parent.right
        anchors.top: parent.top
        text: row.value
        color: row.valueColor
        horizontalAlignment: Text.AlignRight
        wrapMode: row.wrapValue ? Text.WrapAnywhere : Text.NoWrap
        elide: row.wrapValue ? Text.ElideNone : Text.ElideMiddle
        font.family: "Arial"
        font.pixelSize: 13
        font.weight: Font.Medium
        lineHeight: 1.15
    }
}

