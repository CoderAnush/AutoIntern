import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

export default function Offline() {
    const handleRetry = () => {
        window.location.reload();
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
            <div className="text-center max-w-md">
                <div className="mb-6 flex justify-center">
                    <div className="relative">
                        <WifiOff className="w-16 h-16 text-red-400 animate-pulse" />
                    </div>
                </div>

                <h1 className="text-3xl font-bold text-white mb-2">
                    No Internet Connection
                </h1>

                <p className="text-slate-300 mb-6">
                    AutoIntern requires an internet connection to sync data. Please check your connection and try again.
                </p>

                <div className="space-y-3">
                    <button
                        onClick={handleRetry}
                        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Retry Connection
                    </button>

                    <div className="pt-4 border-t border-slate-700">
                        <p className="text-sm text-slate-400">
                            ℹ️ You can still browse your cached data while offline, but some features won't be available.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
