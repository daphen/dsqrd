import QtQuick
import QsLib

// Cockpit's round composer action: solid fg when ready, a soft tint otherwise.
Item {
    id: btn
    property string iconName: ""
    property bool ready: false
    signal clicked()
    readonly property color contentColor: ready ? Theme.bg : Theme.mode === "dark" ? Qt.alpha(Theme.fg, 0.8) : Theme.fg_muted
    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: btn.ready ? Theme.fg : hover.hovered ? Theme.itemHover : Qt.alpha(Theme.fg, Theme.mode === "dark" ? 0.16 : 0.08)
        Behavior on color { ColorAnimation { duration: 160 } }
    }
    Icon {
        visible: btn.iconName.length > 0
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: -1; anchors.verticalCenterOffset: 1
        width: Math.round(btn.width * 0.47); height: width
        name: btn.iconName
        color: btn.contentColor
        Behavior on color { ColorAnimation { duration: 200 } }
    }
    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: btn.clicked() }
}
