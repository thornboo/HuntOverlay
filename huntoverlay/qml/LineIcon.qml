import QtQuick 2.15

Item {
    id: icon

    property string kind: "map"
    property color color: "#CFCFCF"
    property real lineWidth: 1.8

    implicitWidth: 20
    implicitHeight: 20

    readonly property string glyph: {
        if (kind === "map") return "▦"
        if (kind === "poi") return "⌖"
        if (kind === "boss") return "◇"
        if (kind === "settings") return "⚙"
        if (kind === "measure") return "⌁"
        if (kind === "flag") return "⚑"
        if (kind === "keyboard") return "⌨"
        if (kind === "storage") return "▣"
        if (kind === "overlay") return "◫"
        return "○"
    }

    Text {
        anchors.fill: parent
        text: icon.glyph
        color: icon.color
        font.family: Qt.application.font.family
        font.pixelSize: Math.min(icon.width, icon.height)
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
