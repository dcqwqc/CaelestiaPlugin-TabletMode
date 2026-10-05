import QtQuick
import qs.components.controls
import qs.services
import dcqwqc.tabletmode.services as TabletPlugin

IconButton {
    visible: TabletPlugin.RotationLock.available
    icon: "keyboard"
    checked: TabletPlugin.RotationLock.keyboardOverride
    enabled: !TabletPlugin.RotationLock.keyboardOverrideChanging
    onClicked: TabletPlugin.RotationLock.toggleKeyboardOverride()

    inactiveColour: Colours.layer(Colours.palette.m3surfaceContainerHighest, 2)
    fillWidth: true
    isToggle: true
    isRound: true
    shapeMorph: true

    onVisibleChanged: if (visible)
        TabletPlugin.RotationLock.refresh()
}
