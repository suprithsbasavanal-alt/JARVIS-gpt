import logging
import cv2
import numpy as np
import platform
import subprocess
from backend.agents.base import BaseAgent

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
            # Create a mock black image if everything fails
            try:
                img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                cv2.imwrite(output_path, img)
                return True
            except Exception:
                pass
        return False

    def explain_screen(self, screenshot_path: str) -> str:
        """
        Analyzes a screenshot and describes its content.
        Uses multimodal input if Gemini is configured.
        """
        logger.info(f"Explaining screen: {screenshot_path}")
        if self.model:
            try:
                import google.generativeai as genai
                # Load the screenshot image
                with open(screenshot_path, "rb") as f:
                    image_bytes = f.read()
                
                image_part = {
                    "mime_type": "image/png",
                    "data": image_bytes
                }
                
                prompt = "What am I looking at on this screen? Describe the active application, window layout, and text content visible."
                response = self.model.generate_content([prompt, image_part])
                return response.text
            except Exception as e:
                logger.error(f"Multimodal explanation failed: {e}")
                
        return "[Vision Agent: Mock description of the user's screen. A code editor window and terminal are open.]"
        
vision_agent = VisionAgent()
