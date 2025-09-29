import { useState } from 'react';
import { FileText, Sparkles } from 'lucide-react';
import FileUpload from './components/FileUpload';
import PDFViewer from './components/PDFViewer';
import ExtractedDataPanel from './components/ExtractedDataPanel';
import TransactionsTable from './components/TransactionsTable';
import ConnectionLine from './components/ConnectionLine';
import { uploadPDF } from './utils/api';

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedField, setSelectedField] = useState(null);
  const [highlightCoords, setHighlightCoords] = useState(null);

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError(null);
    setPdfFile(file);
    setPdfUrl(URL.createObjectURL(file));

    try {
      const result = await uploadPDF(file);
      if (result.status === 'success') {
        setExtractedData(result);
      } else {
        setError(result.error || 'Failed to process PDF');
      }
    } catch (err) {
      setError(err.message || 'Failed to upload PDF');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldClick = (fieldName, coordinates) => {
    setSelectedField(fieldName);
    setHighlightCoords(coordinates);
  };

  const handleClearSelection = () => {
    setSelectedField(null);
    setHighlightCoords(null);
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Modern Gradient Header */}
      <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white shadow-xl">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white bg-opacity-20 rounded-lg backdrop-blur-sm">
              <FileText size={28} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">OCR Document Extractor</h1>
              <p className="text-sm text-blue-100 flex items-center gap-1">
                <Sparkles size={14} />
                Powered by AI • Extract structured data from bank statements
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* File Upload Section */}
      <div className="px-6 py-4 bg-white border-b shadow-sm">
        <FileUpload onFileUpload={handleFileUpload} loading={loading} />
        {error && (
          <div className="mt-3 p-4 bg-red-50 border-l-4 border-red-500 text-red-800 rounded-r-lg">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      {pdfUrl && extractedData && (
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Extracted Data */}
          <div className="w-1/3 border-r bg-white shadow-lg overflow-y-auto">
            <ExtractedDataPanel
              data={extractedData.data}
              selectedField={selectedField}
              onFieldClick={handleFieldClick}
            />
          </div>

          {/* Right Panel - PDF Viewer */}
          <div className="flex-1 relative">
            <PDFViewer
              pdfUrl={pdfUrl}
              highlightCoords={highlightCoords}
              onClearSelection={handleClearSelection}
            />
            {selectedField && highlightCoords && (
              <ConnectionLine
                fieldName={selectedField}
                targetCoords={highlightCoords}
              />
            )}
          </div>
        </div>
      )}

      {/* Bottom Panel - Transactions Table */}
      {extractedData && extractedData.data && extractedData.data.transactions && (
        <div className="h-1/3 border-t bg-white shadow-xl overflow-hidden">
          <TransactionsTable
            transactions={extractedData.data.transactions}
            onTransactionClick={(transaction) => {
              console.log('Transaction clicked:', transaction);
            }}
          />
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-2xl shadow-2xl">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200"></div>
                <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-600 absolute top-0 left-0"></div>
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-gray-800">Processing PDF...</p>
                <p className="text-sm text-gray-500 mt-1">Extracting data with AI</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
