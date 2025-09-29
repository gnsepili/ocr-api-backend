import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight, X } from 'lucide-react';

// Configure PDF.js worker - using unpkg CDN for reliability
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

function PDFViewer({ pdfUrl, highlightCoords, onClearSelection }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  // Scale coordinates from OCR image pixels to rendered PDF size
  const scaleCoordinates = (coords) => {
    if (!coords || coords.length !== 4) return null;
    
    const ocrWidth = 2000;
    const ocrHeight = 2339;
    const pdfWidth = 720 * scale;
    const pdfHeight = 842 * scale;
    
    const scaleX = pdfWidth / ocrWidth;
    const scaleY = pdfHeight / ocrHeight;
    
    return {
      left: coords[0] * scaleX,
      top: coords[1] * scaleY,
      width: (coords[2] - coords[0]) * scaleX,
      height: (coords[3] - coords[1]) * scaleY,
    };
  };

  const scaledCoords = highlightCoords ? scaleCoordinates(highlightCoords) : null;

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Enhanced Controls */}
      <div className="px-4 py-3 bg-white border-b shadow-sm flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPageNumber(prev => Math.max(1, prev - 1))}
            disabled={pageNumber <= 1}
            className="flex items-center gap-1 px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            <ChevronLeft size={16} />
            <span className="text-sm font-medium">Previous</span>
          </button>
          <div className="px-4 py-2 bg-gray-100 rounded-lg">
            <span className="text-sm font-semibold text-gray-700">
              Page {pageNumber} of {numPages || '?'}
            </span>
          </div>
          <button
            onClick={() => setPageNumber(prev => Math.min(numPages || 1, prev + 1))}
            disabled={pageNumber >= (numPages || 1)}
            className="flex items-center gap-1 px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            <span className="text-sm font-medium">Next</span>
            <ChevronRight size={16} />
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setScale(prev => Math.max(0.5, prev - 0.1))}
            className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut size={18} className="text-gray-700" />
          </button>
          <span className="px-3 py-1 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={() => setScale(prev => Math.min(2, prev + 0.1))}
            className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            title="Zoom In"
          >
            <ZoomIn size={18} className="text-gray-700" />
          </button>
        </div>

        {highlightCoords && (
          <button
            onClick={onClearSelection}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 transition-all shadow-sm"
          >
            <X size={16} />
            <span className="text-sm font-medium">Clear Highlight</span>
          </button>
        )}
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="relative inline-block shadow-2xl rounded-lg overflow-hidden">
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={(error) => console.error('PDF Load Error:', error)}
            options={{
              cMapUrl: `https://unpkg.com/pdfjs-dist@${pdfjs.version}/cmaps/`,
              cMapPacked: true,
              standardFontDataUrl: `https://unpkg.com/pdfjs-dist@${pdfjs.version}/standard_fonts/`,
            }}
          >
            <Page 
              pageNumber={pageNumber} 
              scale={scale}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
          
          {/* Highlight Overlay */}
          {scaledCoords && (
            <div
              className="absolute border-4 border-blue-500 bg-blue-400 bg-opacity-20 pointer-events-none animate-pulse rounded"
              style={{
                left: `${scaledCoords.left}px`,
                top: `${scaledCoords.top}px`,
                width: `${scaledCoords.width}px`,
                height: `${scaledCoords.height}px`,
                boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)',
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default PDFViewer;
