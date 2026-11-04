import QtQuick
import Quickshell
import "ui" as UI
ShellRoot {
    id: root
    property int phase: 0
    property int requestsBefore: 0
    function check(value, message) {
        if (!value) { console.error("FAIL", message); Qt.quit(); throw new Error(message) }
    }
    function checkBottom() {
        const item = messages.itemAtIndex(messages.count - 1)
        check(item && item.y + item.height > messages.contentY
            && item.y < messages.contentY + messages.height, "newest message intersects viewport")
        const bottom = messages.originY + Math.max(0, messages.contentHeight - messages.height + messages.bottomMargin)
        if (messages.contentHeight - messages.height + messages.bottomMargin > 0)
            check(Math.abs(messages.contentY - bottom) < 1, "bottom uses current origin")
        else
            check(messages.contentY >= messages.originY - messages.topMargin - 1
                && messages.contentY <= messages.originY + 1, "short list stays within native margin bounds")
    }
    FloatingWindow {
        id: window
        implicitWidth: 600
        implicitHeight: 400
        UI.MessageList { id: messages; anchors.fill: parent }
    }
    Timer {
        interval: 350
        running: true
        repeat: true
        onTriggered: {
            if (root.phase === 0) {
                for (let i = 0; i < 48; i++) UI.Backend.messages.append({ts: String(i), rowHeight: 42 + (i % 5) * 19})
            } else if (root.phase === 1) {
                root.checkBottom()
                messages.stick = false; messages.pinBottom = false
                messages.currentIndex = 24; messages.positionViewAtIndex(24, ListView.Beginning)
                UI.Backend.aboutToPrepend()
                for (let i = 0; i < 1200; i++) UI.Backend.messages.insert(0, {ts: "older" + i, rowHeight: 35 + (i % 7) * 13})
                UI.Backend.prepended(1200)
            } else if (root.phase === 2) {
                messages.forceLayout()
                root.check(messages.originY < -80000, "history produces a real negative origin")
                console.log("SHIFT", messages.originY, "rows", messages.count)
                messages.toBottom()
            } else if (root.phase === 3) {
                messages.pinBottomView(); root.checkBottom()
                messages.stick = false
                messages.currentIndex = 100; messages.positionViewAtIndex(100, ListView.Beginning)
                root.requestsBefore = UI.Backend.requests
                messages.scroll(-1)
                root.check(UI.Backend.requests === root.requestsBefore, "mid-history scroll does not request older rows")
                messages.scroll(-100000)
                root.check(Math.abs(messages.contentY - messages.originY) < 1, "up-scroll clamps at shifted origin")
                root.check(UI.Backend.requests > root.requestsBefore, "near-top scroll requests older history")
                messages.toBottom(); messages.toBottom()
                window.implicitHeight = 250
            } else if (root.phase === 4) {
                root.checkBottom()
                window.implicitWidth = 420
            } else if (root.phase === 5) {
                root.checkBottom()
                messages.currentIndex = 800
                UI.Backend.messages.setProperty(UI.Backend.messages.count - 1, "rowHeight", 950)
                UI.Backend.reactionChanged()
            } else if (root.phase === 6) {
                root.checkBottom()
                root.check(messages.currentIndex === 800, "resizing does not move the message cursor")
                UI.Backend.messages.append({ts: "new-arrival", rowHeight: 60})
            } else if (root.phase === 7) {
                root.checkBottom()
                root.check(messages.currentIndex === 800, "new arrivals preserve an older cursor")
                messages.stick = false; messages.pinBottom = false
                UI.Backend.messages.clear()
                for (let i = 0; i < 48; i++) UI.Backend.messages.append({ts: String(i), rowHeight: 70})
                messages.currentIndex = 30; messages.positionViewAtIndex(30, ListView.Beginning)
            } else if (root.phase === 8) {
                UI.Backend.messages.remove(0, 20)
            } else if (root.phase === 9) {
                messages.forceLayout()
                root.check(messages.originY > 0, "removals produce a real positive origin")
                messages.toBottom()
            } else if (root.phase === 10) {
                root.checkBottom()
                messages.scroll(-100000)
                root.check(Math.abs(messages.contentY - messages.originY) < 1, "positive-origin scroll clamps at top")
                messages.stick = false; messages.pinBottom = false
                UI.Backend.messages.clear()
                UI.Backend.messages.append({ts: "short", rowHeight: 40})
            } else if (root.phase === 11) {
                messages.toBottom()
            } else if (root.phase === 12) {
                root.checkBottom()
                console.log("PASS origin-aware history, scrolling, resizing, cursor preservation, and short lists")
                Qt.quit(); return
            }
            root.phase++
        }
    }
}
