import objc
import logging
import platform

logger = logging.getLogger(__name__)

def perform_ocr_on_image(image_path: str) -> str:
    """
    Extracts text from an image using the macOS native Vision framework.
    Completely offline, high-accuracy, and fast.
    """
    if platform.system() != "Darwin":
        logger.warning("Native macOS Vision OCR is only supported on Darwin (macOS).")
        return "[OCR Not Supported on this OS]"

    try:
        from Cocoa import NSURL
        from Vision import VNImageRequestHandler, VNRecognizeTextRequest

        url = NSURL.fileURLWithPath_(image_path)
        request = VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(0) # 0 = Accurate, 1 = Fast
        
        handler = VNImageRequestHandler.alloc().initWithURL_options_(url, None)
        success, error = handler.performRequests_error_([request], None)
        if not success:
            logger.error(f"Vision OCR request failed: {error}")
            return ""
            
        results = request.results()
        text_lines = []
        for result in results:
            candidates = result.topCandidates_(1)
            if candidates:
                text_lines.append(candidates[0].string())
                
        return "\n".join(text_lines)
    except Exception as e:
        logger.error(f"Native macOS OCR failed: {e}")
        return ""
