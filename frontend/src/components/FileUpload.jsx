import { Upload, Loader2 } from 'lucide-react';

function FileUpload({ onFileUpload, loading }) {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      onFileUpload(file);
    } else {
      alert('Please select a valid PDF file');
    }
  };

  return (
    <div className="flex items-center gap-4">
      <label className={`flex items-center gap-3 px-6 py-3 rounded-xl font-medium transition-all shadow-lg ${
        loading 
          ? 'bg-gray-400 cursor-not-allowed' 
          : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 cursor-pointer transform hover:scale-105'
      } text-white`}>
        {loading ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            <span>Processing...</span>
          </>
        ) : (
          <>
            <Upload size={20} />
            <span>Upload PDF</span>
          </>
        )}
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
          disabled={loading}
        />
      </label>
      <div className="flex-1">
        <p className="text-sm text-gray-600 font-medium">
          📄 Upload a bank statement PDF (max 50MB)
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Supports all standard bank statement formats
        </p>
      </div>
    </div>
  );
}

export default FileUpload;
