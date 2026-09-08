import QtQuick
import QtQuick.Controls

// A scrollbar with a handle wide enough to grab.
//
// Qt's default for a ComboBox popup is a ScrollIndicator, which only reports
// position and cannot be dragged. With hundreds of source columns in a list,
// a wheel is the only way to move and long lists become tedious. This is an
// interactive ScrollBar sized for the pointer, in the Evidence Desk palette.
ScrollBar {
    id: control

    policy: ScrollBar.AsNeeded
    // A wider track than the handle, so the pointer has room to land.
    implicitWidth: 12
    implicitHeight: 12
    padding: 3
    minimumSize: 0.08

    contentItem: Rectangle {
        implicitWidth: 6
        implicitHeight: 6
        radius: 3
        color: control.pressed ? "#7E8798"
             : control.hovered ? "#98A2B3"
             : "#C4CCD9"
        // Visible whenever there is anything to scroll, not only while the
        // pointer is over it: a handle you cannot see is one you cannot grab.
        opacity: control.size < 1 ? (control.active || control.hovered ? 1 : 0.8) : 0

        Behavior on opacity { NumberAnimation { duration: 140 } }
        Behavior on color { ColorAnimation { duration: 100 } }
    }

    background: Rectangle {
        color: control.hovered ? "#F1F4F8" : "transparent"
        radius: 6
        Behavior on color { ColorAnimation { duration: 100 } }
    }
}
