#
# Emotion Bridge Extension Addon
# Registers the emotion bridge extension with TEN Framework
#
from ten_runtime import Addon, register_addon_as_extension, TenEnv


@register_addon_as_extension("emotion_bridge_python")
class EmotionBridgeExtensionAddon(Addon):

    def on_create_instance(self, ten_env: TenEnv, name: str, context) -> None:
        from .extension import EmotionBridgeExtension
        ten_env.log_info("Creating EmotionBridgeExtension instance")
        ten_env.on_create_instance_done(EmotionBridgeExtension(name), context)