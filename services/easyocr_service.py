"""
EasyOCR Service Module - Extract text with coordinates from PDFs
"""

import logging
import asyncio
import os
import tempfile
from typing import List, Dict, Any, Tuple
import numpy as np
from pdf2image import convert_from_bytes
import easyocr
import aiofiles

logger = logging.getLogger(__name__)


class EasyOCRService:
    """Service for extracting text and coordinates from PDFs using EasyOCR."""
    
    def __init__(self, languages: List[str] = ['en']):
        """Initialize EasyOCR reader with specified languages."""
        self.languages = languages
        self._reader = None
        
    def _get_reader(self):
        """Lazy initialization of EasyOCR reader."""
        if self._reader is None:
            logger.info(f"Initializing EasyOCR reader with languages: {self.languages}")
            self._reader = easyocr.Reader(self.languages, gpu=False)  # Set gpu=True if available
        return self._reader
    
    async def extract_from_pdf(self, pdf_content: bytes, dpi: int = 200) -> List[Dict[str, Any]]:
        """
        Extract text with coordinates from PDF content.
        
        Args:
            pdf_content: PDF file content as bytes
            dpi: DPI for PDF to image conversion (higher = better quality but slower)
            
        Returns:
            List of dictionaries containing OCR results for each page
        """
        try:
            # Convert PDF to images
            logger.info("Converting PDF to images...")
            images = await asyncio.to_thread(
                convert_from_bytes, 
                pdf_content, 
                dpi=dpi,
                fmt='RGB'
            )
            
            logger.info(f"Converted PDF to {len(images)} page(s)")
            
            # Process each page
            all_pages_data = []
            reader = self._get_reader()
            
            for page_num, image in enumerate(images):
                logger.info(f"Processing page {page_num + 1}/{len(images)}")
                
                # Convert PIL image to numpy array for EasyOCR
                image_np = np.array(image)
                
                # Extract text with coordinates
                ocr_results = await asyncio.to_thread(
                    reader.readtext, 
                    image_np, 
                    detail=1,  # Return detailed results with coordinates
                    paragraph=False  # Don't group into paragraphs
                )
                
                # Format results
                page_data = {
                    "page_number": page_num + 1,
                    "page_width": image.width,
                    "page_height": image.height,
                    "text_elements": []
                }
                
                for bbox, text, confidence in ocr_results:
                    # EasyOCR returns bbox as [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    # Convert to [x0, y0, x1, y1] format (top-left, bottom-right)
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    x0, y0 = min(x_coords), min(y_coords)
                    x1, y1 = max(x_coords), max(y_coords)
                    
                    text_element = {
                        "text": text.strip(),
                        "bbox": [x0, y0, x1, y1],  # [x0, y0, x1, y1]
                        "confidence": float(confidence),
                        "page": page_num + 1
                    }
                    
                    # Only include text elements with reasonable confidence
                    if confidence > 0.3 and text.strip():
                        page_data["text_elements"].append(text_element)
                
                all_pages_data.append(page_data)
                logger.info(f"Extracted {len(page_data['text_elements'])} text elements from page {page_num + 1}")
            
            return all_pages_data
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def format_for_llm(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format OCR data for LLM consumption.
        
        Args:
            ocr_data: OCR results from extract_from_pdf
            
        Returns:
            Formatted data suitable for LLM processing
        """
        formatted_data = {
            "document_info": {
                "total_pages": len(ocr_data),
                "total_text_elements": sum(len(page["text_elements"]) for page in ocr_data)
            },
            "pages": [],
            "all_text": "",  # Combined text for LLM context
            "text_with_coordinates": []  # Text elements with spatial info
        }
        
        all_text_parts = []
        
        for page_data in ocr_data:
            page_info = {
                "page_number": page_data["page_number"],
                "dimensions": {
                    "width": page_data["page_width"],
                    "height": page_data["page_height"]
                },
                "text_elements": page_data["text_elements"]
            }
            formatted_data["pages"].append(page_info)
            
            # Sort text elements by position (top to bottom, left to right)
            sorted_elements = sorted(
                page_data["text_elements"],
                key=lambda x: (x["bbox"][1], x["bbox"][0])  # Sort by y, then x
            )
            
            # Add to combined text
            page_text = " ".join([elem["text"] for elem in sorted_elements])
            all_text_parts.append(f"[Page {page_data['page_number']}] {page_text}")
            
            # Add to coordinate-aware text
            for elem in sorted_elements:
                formatted_data["text_with_coordinates"].append({
                    "text": elem["text"],
                    "page": elem["page"],
                    "bbox": elem["bbox"],
                    "confidence": elem["confidence"]
                })
        
        formatted_data["all_text"] = "\n\n".join(all_text_parts)
        
        return formatted_data
    
    async def process_pdf_for_llm(self, pdf_content: bytes, dpi: int = 200) -> Dict[str, Any]:
        """
        Complete pipeline: Extract OCR data and format for LLM.
        
        Args:
            pdf_content: PDF file content as bytes
            dpi: DPI for PDF to image conversion
            
        Returns:
            Formatted OCR data ready for LLM processing
        """
        logger.info("Starting PDF OCR processing for LLM")
        
        # Extract OCR data
        ocr_data = await self.extract_from_pdf(pdf_content, dpi=dpi)
        
        # Format for LLM
        formatted_data = self.format_for_llm(ocr_data)
        
        logger.info(f"OCR processing complete. Extracted {formatted_data['document_info']['total_text_elements']} text elements from {formatted_data['document_info']['total_pages']} pages")
        
        return formatted_data
