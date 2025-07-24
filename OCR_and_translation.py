import cv2
import pytesseract
from deep_translator import GoogleTranslator
import re

def clean_text(text: str) -> str:
    """Cleans text by removing stray characters and normalizing spaces."""
    text = text.replace("|", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fix_common_ocr_errors(text: str) -> str:
    """Fix common OCR mistakes such as missing 'I' at the start."""
    # If text starts with "am ", add missing "I"
    corrections = [
        (r"^am ", "I am ")
    ]
    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def translate_to_chinese(text: str) -> str:
    """Translate English to Simplified Chinese using deep-translator."""
    try:
        translated = GoogleTranslator(source='en', target='zh-CN').translate(text)
    except Exception as e:
        print(f"⚠️ Translation failed for '{text}': {e}")
        translated = None
    return translated if translated else text

def merge_into_paragraphs(lines):
    """
    Merge lines into paragraphs based on punctuation and spacing.
    """
    paragraphs = []
    current_paragraph = ""

    for line in lines:
        line = clean_text(fix_common_ocr_errors(line))
        if not line:
            continue

        if current_paragraph:
            current_paragraph += " " + line
        else:
            current_paragraph = line

        # Paragraph ends if line ends with '.', '?', '!' OR is very short (likely a title)
        if any(line.endswith(p) for p in [".", "?", "!", ":"]) or len(line.split()) < 5:
            paragraphs.append(current_paragraph.strip())
            current_paragraph = ""

    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    return paragraphs

def extract_and_translate_text(image_path: str, output_txt: str):
    """Extracts text, merges into paragraphs, and saves English + Chinese pairs."""
    img = cv2.imread(image_path)
    data = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)

    # Group texts by line
    lines = {}
    for i, text in enumerate(data['text']):
        if text.strip():
            line_id = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            lines.setdefault(line_id, []).append(text.strip())

    # Keep reading order
    sorted_lines = [" ".join(words) for _, words in sorted(lines.items(), key=lambda x: x[0])]

    # Merge lines into paragraphs
    paragraphs = merge_into_paragraphs(sorted_lines)

    # Save results
    with open(output_txt, "w", encoding="utf-8") as f:
        for eng in paragraphs:
            chi = translate_to_chinese(eng)
            f.write(f"{eng}\n{chi}\n\n")

    print(f"✅ Translated and formatted text saved as: {output_txt}")

if __name__ == "__main__":
    extract_and_translate_text("input_text.png", "translated_output.txt")