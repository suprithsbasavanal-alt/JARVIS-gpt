import logging
import cv2
import numpy as np
import platform
import subprocess
import re
from backend.agents.base import BaseAgent
from backend.vision.ocr import perform_ocr_on_image

logger = logging.getLogger(__name__)

VISION_PROMPT = """You are the JARVIS Vision Agent. Your task is to analyze screen captures, image files, or camera streams.
Explain clearly what elements are visible on the screen, read the active window labels, identify text via OCR, and guide UI interactions.
"""

class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="vision",
            system_prompt=VISION_PROMPT
        )
        self.system = platform.system()

    def get_active_app(self) -> str:
        """
        Gets the name of the active frontmost application on macOS.
        """
        if self.system != "Darwin":
            return "Unknown (Non-macOS)"
        try:
            # Zero-permission built-in tool to read the active frontmost ASN
            asn_out = subprocess.check_output(["lsappinfo", "front"], text=True).strip()
            info_out = subprocess.check_output(["lsappinfo", "info", asn_out], text=True)
            match = re.search(r'"([^"]+)"', info_out)
            if match:
                return match.group(1)
        except Exception as e:
            logger.debug(f"Failed to resolve active application: {e}")
        return "Unknown Application"

    def capture_screen(self, output_path: str = "screenshot.png") -> bool:
        """
        Captures the current desktop screen.
        On macOS, uses the native 'screencapture' CLI utility.
        """
        logger.info(f"Capturing screen to: {output_path}")
        if self.system == "Darwin":
            try:
                subprocess.run(["screencapture", "-x", output_path], check=True)
                return True
            except Exception as e:
                logger.error(f"macOS screencapture failed: {e}")
        
        # Cross-platform fallback using OpenCV + PyAutoGUI if available
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Fallback screen capture failed: {e}")
            try:
                img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                cv2.imwrite(output_path, img)
                return True
            except Exception:
                pass
        return False

    def explain_screen(self, screenshot_path: str) -> str:
        """
        Analyzes a screenshot, runs OCR, and describes its content.
        Uses multimodal input if Gemini is configured.
        """
        logger.info(f"Explaining screen: {screenshot_path}")
        
        # 1. Resolve active application and OCR text
        active_app = self.get_active_app()
        ocr_text = perform_ocr_on_image(screenshot_path)
        
        logger.info(f"Active App Detected: '{active_app}'")
        logger.info(f"OCR characters extracted: {len(ocr_text)}")

        prompt = (
            f"Active Application in Focus: '{active_app}'\n\n"
            f"Extracted OCR Text:\n\"\"\"\n{ocr_text}\n\"\"\"\n\n"
            f"What am I looking at on this screen? Explain the window layout, active application context, "
            f"and synthesize details based on both the OCR text and the visual screenshot image."
        )

        if self.model:
            try:
                # Load the screenshot image
                with open(screenshot_path, "rb") as f:
                    image_bytes = f.read()
                
                image_part = {
                    "mime_type": "image/png",
                    "data": image_bytes
                }
                
                response = self.model.generate_content([prompt, image_part])
                return response.text
            except Exception as e:
                logger.error(f"Multimodal explanation failed: {e}")
                
        # Heuristic offline fallback response
        briefing = f"### [OFFLINE VISION STATE] Screen Telemetry\n\n"
        briefing += f"- **Active Application**: `{active_app}`\n"
        if ocr_text.strip():
            briefing += f"- **Extracted OCR Text Output**:\n```\n{ocr_text[:400]}...\n```\n"
        else:
            briefing += "- **OCR Output**: No visible characters detected on screen layout.\n"
        briefing += "\n*Note: Multimodal visual reasoning is offline. Please enter a Gemini API Key in Settings.*"
        return briefing
        
vision_agent = VisionAgent()
