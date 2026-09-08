import QtQuick
import QtQuick.Controls

ComboBox {
    id: control

    property string placeholder: "Select"

    implicitHeight: 38
    implicitWidth: 190
    leftPadding: 12
    rightPadding: 34
    hoverEnabled: true

    contentItem: Text {
        text: control.displayText || control.placeholder
        color: control.enabled ? "#101522" : "#626C7F"
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        font.family: "Arial"
        font.pixelSize: 12
    }

    indicator: Item {
        x: control.width - 24
        y: (control.height - height) / 2
        width: 12
        height: 8

        Rectangle {
            x: 1
            y: 2
            width: 7
            height: 1.5
            rotation: 42
            color: "#566176"
            transformOrigin: Item.Left
        }
        Rectangle {
            x: 6
            y: 7
            width: 7
            height: 1.5
            rotation: -42
            color: "#566176"
            transformOrigin: Item.Left
        }
    }

    background: Rectangle {
        color: control.enabled ? "#FFFFFF" : "#F1F4F8"
        border.width: 1
        border.color: control.activeFocus || control.popup.visible ? "#0B42E7" : "#CCD3DE"
        radius: 4
    }

    delegate: ItemDelegate {
        required property var model
        required property int index
        width: control.width
        height: 36
        highlighted: control.highlightedIndex === index

        contentItem: Text {
            text: model[control.textRole] || modelData
            color: "#101522"
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font.family: "Arial"
            font.pixelSize: 12
        }
        background: Rectangle {
            color: parent.highlighted ? "#EEF3FF" : "#FFFFFF"
        }
    }

    popup: Popup {
        y: control.height + 3
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 2, 260)
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            // Interactive, so a long column list can be dragged rather than
            // only wheeled through.
            ScrollBar.vertical: AppScrollBar { policy: ScrollBar.AsNeeded }
        }
        background: Rectangle {
            color: "#FFFFFF"
            border.width: 1
            border.color: "#BFC7D4"
            radius: 4
        }
    }
}
