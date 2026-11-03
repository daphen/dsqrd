import QtQuick
import QsLib

// Cockpit's composer-corner pill: an icon that widens to show its label on hover.
Rectangle {
    id: pill
    property string iconName: ""
    property string label: ""
    property int iconSize: 16
    property bool active: false
    property color tint: Theme.fg_muted
    default property alias glyph: glyphSlot.data
    signal clicked()
    readonly property bool expanded: hover.hovered || active
    readonly property color hoverFill: Theme.mode === "light" ? Theme.itemHover : Qt.rgba(1, 1, 1, 0.07)
    implicitWidth: expanded ? row.implicitWidth + 12 : 30
    implicitHeight: 22
    radius: 11
    color: expanded ? hoverFill : Qt.alpha(hoverFill, 0)
    clip: true
    Behavior on implicitWidth { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    Behavior on color { ColorAnimation { duration: 140 } }
    Row {
        id: row
        anchors { left: parent.left; leftMargin: 6; verticalCenter: parent.verticalCenter }
        spacing: 5
        Item {
            id: glyphSlot
            width: pill.iconSize; height: pill.iconSize
            anchors.verticalCenter: parent.verticalCenter
            Icon { visible: pill.iconName.length > 0; anchors.fill: parent; name: pill.iconName; color: pill.tint }
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            visible: pill.expanded
            text: pill.label
            color: pill.tint
            font { family: Theme.fontFamily; pixelSize: Theme.fontSize; weight: 650 }
        }
    }
    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: pill.clicked() }
}
