import { Receipt } from 'lucide-react';

function TransactionsTable({ transactions, onTransactionClick }) {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <Receipt size={48} className="mx-auto mb-3 text-gray-400" />
          <p className="text-lg font-medium">No transactions found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Table Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-slate-100 border-b-2 border-slate-200">
        <div className="flex items-center gap-2">
          <Receipt className="text-blue-600" size={22} />
          <h3 className="font-bold text-gray-800 text-lg">
            Transactions <span className="text-blue-600">({transactions.length})</span>
          </h3>
        </div>
      </div>

      {/* Table Content */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="bg-gradient-to-r from-slate-100 to-slate-200 sticky top-0 shadow-sm">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b-2 border-slate-300">#</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b-2 border-slate-300">Date</th>
              <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b-2 border-slate-300">Description</th>
              <th className="px-4 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wider border-b-2 border-slate-300">Debit (Dr)</th>
              <th className="px-4 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wider border-b-2 border-slate-300">Credit (Cr)</th>
              <th className="px-4 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wider border-b-2 border-slate-300">Balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.map((transaction, index) => (
              <tr
                key={index}
                onClick={() => onTransactionClick(transaction)}
                className="hover:bg-blue-50 cursor-pointer transition-colors group"
              >
                <td className="px-4 py-4 text-sm font-medium text-gray-500 group-hover:text-blue-600">
                  {index + 1}
                </td>
                <td className="px-4 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">
                  {transaction.date?.value || '-'}
                </td>
                <td className="px-4 py-4 text-sm text-gray-700 max-w-md">
                  <div className="truncate group-hover:text-blue-900">
                    {transaction.description?.value || '-'}
                  </div>
                </td>
                <td className="px-4 py-4 text-sm text-right font-semibold whitespace-nowrap">
                  {transaction.debit?.value ? (
                    <span className="text-red-600 bg-red-50 px-2 py-1 rounded-lg">
                      ₹{transaction.debit.value.toLocaleString()}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-4 text-sm text-right font-semibold whitespace-nowrap">
                  {transaction.credit?.value ? (
                    <span className="text-green-600 bg-green-50 px-2 py-1 rounded-lg">
                      ₹{transaction.credit.value.toLocaleString()}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-4 text-sm text-right font-bold text-gray-900 whitespace-nowrap">
                  {transaction.balance?.value ? (
                    <span className="bg-blue-50 px-2 py-1 rounded-lg">
                      ₹{transaction.balance.value.toLocaleString()}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TransactionsTable;
