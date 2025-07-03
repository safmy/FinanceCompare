"""
Convert PDF pages to images for Vision API processing
"""

import io
import base64
from pdf2image import convert_from_bytes
from PIL import Image

def pdf_to_images(pdf_content):
    """Convert PDF bytes to a list of image bytes"""
    try:
        # Convert PDF to PIL images
        images = convert_from_bytes(pdf_content, dpi=300)
        
        image_bytes_list = []
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            image_bytes_list.append(img_byte_arr)
            print(f"Converted page {i+1} to image ({len(img_byte_arr)} bytes)")
        
        return image_bytes_list
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []

def extract_text_from_pdf_pages(vision_client, pdf_content):
    """Extract text from all pages of a PDF"""
    all_text = []
    
    # Convert PDF to images
    image_bytes_list = pdf_to_images(pdf_content)
    
    if not image_bytes_list:
        print("No images extracted from PDF")
        return None
    
    # Process each page
    for i, image_bytes in enumerate(image_bytes_list):
        try:
            from google.cloud import vision
            image = vision.Image(content=image_bytes)
            
            # Use document_text_detection for better results on documents
            response = vision_client.document_text_detection(image=image)
            
            if response.error.message:
                print(f"Error processing page {i+1}: {response.error.message}")
                continue
            
            page_text = response.full_text_annotation.text
            all_text.append(page_text)
            print(f"Page {i+1}: Extracted {len(page_text)} characters")
            
        except Exception as e:
            print(f"Error processing page {i+1}: {e}")
            continue
    
    # Combine all pages
    return '\n'.join(all_text) if all_text else None