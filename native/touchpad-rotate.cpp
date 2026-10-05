#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>

#include <algorithm>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static HANDLE PHANDLE = nullptr;
static CFunctionHook* g_motionHook = nullptr;
static int g_transform = 0;
static std::vector<std::string> g_devices;

using OrigOnMouseMoved = void (*)(CInputManager*, IPointer::SMotionEvent);

static Vector2D rotateDelta(const Vector2D& v, int transform) {
    switch (transform & 3) {
        case 1: return {-v.y, v.x};
        case 2: return {-v.x, -v.y};
        case 3: return {v.y, -v.x};
        default: return v;
    }
}

static bool isManaged(const SP<IPointer>& device) {
    if (!device || !device->m_isTouchpad)
        return false;
    return std::find(g_devices.begin(), g_devices.end(), device->m_hlName) != g_devices.end();
}

static void hkOnMouseMoved(CInputManager* self, IPointer::SMotionEvent event) {
    if (isManaged(event.device) && g_transform != 0) {
        event.delta = rotateDelta(event.delta, g_transform);
        event.unaccel = rotateDelta(event.unaccel, g_transform);
    }

    reinterpret_cast<OrigOnMouseMoved>(g_motionHook->m_original)(self, event);
}

static SDispatchResult setTransform(std::string args) {
    std::istringstream input(args);
    int transform = 0;
    if (!(input >> transform))
        return {.success = false, .error = "expected transform followed by managed touchpad names"};

    std::vector<std::string> devices;
    std::string device;
    while (input >> device)
        devices.push_back(device);

    g_transform = ((transform % 4) + 4) % 4;
    g_devices = std::move(devices);
    return {};
}

APICALL EXPORT std::string PLUGIN_API_VERSION() {
    return HYPRLAND_API_VERSION;
}

APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle) {
    PHANDLE = handle;

    const auto matches = HyprlandAPI::findFunctionsByName(PHANDLE, "onMouseMoved");
    void* target = nullptr;
    for (const auto& match : matches) {
        if (match.demangled.find("CInputManager::onMouseMoved(IPointer::SMotionEvent)") != std::string::npos) {
            target = match.address;
            break;
        }
    }

    if (!target)
        throw std::runtime_error("TabletMode: CInputManager::onMouseMoved hook target not found");

    g_motionHook = HyprlandAPI::createFunctionHook(PHANDLE, target, reinterpret_cast<void*>(&hkOnMouseMoved));
    if (!g_motionHook || !g_motionHook->hook())
        throw std::runtime_error("TabletMode: failed to hook touchpad motion");

    if (!HyprlandAPI::addDispatcherV2(PHANDLE, "tabletmode-touchpad-transform", setTransform))
        throw std::runtime_error("TabletMode: failed to register touchpad transform dispatcher");

    return {
        "tabletmode-touchpad-rotate",
        "Rotates only TabletMode-managed internal touchpad motion after libinput",
        "dcqwqc",
        "1.0.0",
    };
}

APICALL EXPORT void PLUGIN_EXIT() {
    if (PHANDLE)
        HyprlandAPI::removeDispatcher(PHANDLE, "tabletmode-touchpad-transform");
}
