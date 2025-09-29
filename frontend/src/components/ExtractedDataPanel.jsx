import { Check, AlertCircle, ChevronDown, ChevronUp, Info, TrendingUp } from 'lucide-react';
import { useState } from 'react';

function ExtractedDataPanel({ data, selectedField, onFieldClick }) {
  const [expandedSections, setExpandedSections] = useState({
    basicInfo: true,
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getConfidenceBadge = (confidence) => {
    if (!confidence) return null;
    
    const percentage = Math.round(confidence * 100);
    let bgColor, textColor, icon;
    
    if (percentage >= 80) {
      bgColor = 'bg-green-100';
      textColor = 'text-green-700';
      icon = <Check size={12} />;
    } else if (percentage >= 60) {
      bgColor = 'bg-amber-100';
      textColor = 'text-amber-700';
      icon = <AlertCircle size={12} />;
    } else {
      bgColor = 'bg-red-100';
      textColor = 'text-red-700';
      icon = <AlertCircle size={12} />;
    }

    return (
      <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${bgColor} ${textColor}`}>
        {icon}
        <span>{percentage}%</span>
      </div>
    );
  };

  const renderFieldValue = (fieldName, fieldData) => {
    if (!fieldData || !fieldData.value) {
      return (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
            {fieldName.replace(/_/g, ' ')}
          </div>
          <span className="text-gray-400 italic text-sm">Not found</span>
        </div>
      );
    }

    const isSelected = selectedField === fieldName;

    return (
      <div
        className={`p-4 rounded-xl border-2 transition-all cursor-pointer transform hover:scale-[1.02] ${
          isSelected 
            ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-lg ring-2 ring-blue-300' 
            : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md'
        }`}
        onClick={() => onFieldClick(fieldName, fieldData.position)}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            {fieldName.replace(/_/g, ' ')}
          </div>
          {getConfidenceBadge(fieldData.confidence)}
        </div>
        <div className="font-semibold text-gray-900 text-base">
          {String(fieldData.value)}
        </div>
      </div>
    );
  };

  return (
    <div className="p-5">
      {/* Header */}
      <div className="mb-5">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Info className="text-blue-600" size={24} />
          Extracted Data
        </h2>
        <p className="text-sm text-gray-500 mt-1">Click any field to highlight in PDF</p>
      </div>
      
      {/* Basic Information Section */}
      {data && data.basic_information && (
        <div className="mb-6">
          <button
            onClick={() => toggleSection('basicInfo')}
            className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl hover:from-blue-100 hover:to-indigo-100 transition-all shadow-sm border border-blue-200"
          >
            <h3 className="font-bold text-gray-800 flex items-center gap-2">
              <span className="text-blue-600">📋</span>
              Basic Information
            </h3>
            {expandedSections.basicInfo ? 
              <ChevronUp size={20} className="text-blue-600" /> : 
              <ChevronDown size={20} className="text-blue-600" />
            }
          </button>
          
          {expandedSections.basicInfo && (
            <div className="mt-3 space-y-3">
              {Object.entries(data.basic_information).map(([key, value]) => (
                <div key={key}>
                  {renderFieldValue(key, value)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Summary Stats Card */}
      {data && data.transactions && (
        <div className="p-5 bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 rounded-2xl border-2 border-emerald-200 shadow-lg">
          <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <TrendingUp className="text-emerald-600" size={20} />
            Summary
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-white bg-opacity-70 rounded-lg">
              <span className="text-sm font-medium text-gray-600">Total Transactions</span>
              <span className="text-lg font-bold text-emerald-700">{data.transactions.length}</span>
            </div>
            {data.basic_information?.opening_balance?.value && (
              <div className="flex justify-between items-center p-3 bg-white bg-opacity-70 rounded-lg">
                <span className="text-sm font-medium text-gray-600">Opening Balance</span>
                <span className="text-lg font-bold text-blue-700">₹{data.basic_information.opening_balance.value.toLocaleString()}</span>
              </div>
            )}
            {data.basic_information?.closing_balance?.value && (
              <div className="flex justify-between items-center p-3 bg-white bg-opacity-70 rounded-lg">
                <span className="text-sm font-medium text-gray-600">Closing Balance</span>
                <span className="text-lg font-bold text-purple-700">₹{data.basic_information.closing_balance.value.toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Instructions Card */}
      <div className="mt-5 p-4 bg-gradient-to-r from-amber-50 to-yellow-50 rounded-xl border border-amber-200">
        <div className="flex items-start gap-3">
          <span className="text-2xl">💡</span>
          <div>
            <p className="text-sm font-medium text-amber-900">Quick Tip</p>
            <p className="text-xs text-amber-700 mt-1">Click on any field above to highlight its location in the PDF document</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExtractedDataPanel;
