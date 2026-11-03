import QtQuick
import QsLib

// Cockpit's feed dot grid.
Canvas {
    id: grid
    readonly property color dotColor: Theme.mode === "light" ? Qt.rgba(0.14, 0.14, 0.13, 0.07) : Qt.rgba(1, 1, 1, 0.08)
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onDotColorChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        ctx.fillStyle = grid.dotColor
        for (let y = 16; y < height; y += 32)
            for (let x = 16; x < width; x += 32) {
                ctx.beginPath()
                ctx.arc(x, y, 1.2, 0, Math.PI * 2)
                ctx.fill()
            }
    }
}
