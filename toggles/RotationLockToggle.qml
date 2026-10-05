import QtQuick
import Caelestia.Config
import qs.components
import qs.services
import dcqwqc.tabletmode.services as RotationPlugin

// Permanently split rotation control:
// left = toggle sensor auto-rotation on/off
// right = force the next 90° orientation and hold it
StyledRect {
    id: root

    property bool fillWidth: true
    property bool shapeMorph: true
    property real shapeMorphExpansion: 0

    implicitWidth: implicitHeight * 2 + segmentGap
    implicitHeight: autoIcon.implicitHeight + Tokens.padding.small * 2
    visible: RotationPlugin.RotationLock.available
    opacity: RotationPlugin.RotationLock.rotationChanging ? 0.72 : 1

    readonly property bool automatic: !RotationPlugin.RotationLock.locked
    readonly property int degrees: RotationPlugin.RotationLock.degrees
    readonly property string angleLabel: degrees === 270 ? "-90°" : degrees + "°"
    readonly property real outerRadius: Math.min(height / 2, Tokens.rounding.large)
    readonly property real innerRadius: Math.min(outerRadius, Tokens.rounding.small)
    readonly property real segmentGap: Math.max(2, Math.round(Tokens.spacing.extraSmall / 2))
    readonly property real segmentWidth: Math.floor((width - segmentGap) / 2)

    readonly property color selectedColour: Colours.palette.m3primary
    readonly property color selectedOnColour: Colours.palette.m3onPrimary
    readonly property color inactiveColour: Colours.layer(Colours.palette.m3surfaceContainerHighest, 2)
    readonly property color inactiveOnColour: Colours.palette.m3onSurfaceVariant

    radius: outerRadius
    color: "transparent"

    Behavior on opacity { CAnim {} }

    component SegmentSurface: StyledRect {
        required property bool first
        property bool selected: false

        radius: 0
        topLeftRadius: first ? root.outerRadius : root.innerRadius
        bottomLeftRadius: first ? root.outerRadius : root.innerRadius
        topRightRadius: first ? root.innerRadius : root.outerRadius
        bottomRightRadius: first ? root.innerRadius : root.outerRadius
        color: selected ? root.selectedColour : root.inactiveColour

        Behavior on color { CAnim {} }
    }

    SegmentSurface {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.segmentWidth
        first: true
        selected: root.automatic
    }

    SegmentSurface {
        anchors.left: parent.left
        anchors.leftMargin: root.segmentWidth + root.segmentGap
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        first: false
        selected: !root.automatic
    }

    Item {
        id: autoAction
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.segmentWidth

        StateLayer {
            color: root.automatic ? root.selectedOnColour : root.inactiveOnColour
            rect.topLeftRadius: root.outerRadius
            rect.bottomLeftRadius: root.outerRadius
            rect.topRightRadius: root.innerRadius
            rect.bottomRightRadius: root.innerRadius
            onClicked: {
                if (!RotationPlugin.RotationLock.rotationChanging)
                    RotationPlugin.RotationLock.toggleAutomatic();
            }
        }

        MaterialIcon {
            id: autoIcon
            anchors.centerIn: parent
            anchors.verticalCenterOffset: 1
            text: "screen_rotation"
            color: root.automatic ? root.selectedOnColour : root.inactiveOnColour
            fill: root.automatic ? 1 : 0
            fontStyle: Tokens.font.icon.small
        }
    }

    Item {
        id: forceAction
        anchors.left: autoAction.right
        anchors.leftMargin: root.segmentGap
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        StateLayer {
            color: !root.automatic ? root.selectedOnColour : root.inactiveOnColour
            rect.topLeftRadius: root.innerRadius
            rect.bottomLeftRadius: root.innerRadius
            rect.topRightRadius: root.outerRadius
            rect.bottomRightRadius: root.outerRadius
            onClicked: {
                if (!RotationPlugin.RotationLock.rotationChanging)
                    RotationPlugin.RotationLock.forceNext();
            }
        }

        StyledText {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: 1
            text: root.angleLabel
            animate: true
            color: !root.automatic ? root.selectedOnColour : root.inactiveOnColour
            horizontalAlignment: Text.AlignHCenter
            font.weight: Font.DemiBold
        }
    }

    Timer {
        interval: 700
        repeat: true
        running: root.visible
        onTriggered: RotationPlugin.RotationLock.refresh()
    }

    onVisibleChanged: if (visible)
        RotationPlugin.RotationLock.refresh()
}
