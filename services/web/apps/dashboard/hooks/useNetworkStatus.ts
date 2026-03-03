import { useEffect, useState } from 'react';

interface NetworkStatus {
    isOnline: boolean;
    isSlowConnection: boolean;
    effectiveType: '4g' | '3g' | '2g' | 'slow-2g' | 'unknown';
}

export const useNetworkStatus = (): NetworkStatus => {
    const [status, setStatus] = useState<NetworkStatus>({
        isOnline: true,
        isSlowConnection: false,
        effectiveType: '4g',
    });

    useEffect(() => {
        const updateStatus = () => {
            const connection =
                (navigator as any).connection ||
                (navigator as any).mozConnection ||
                (navigator as any).webkitConnection;

            setStatus({
                isOnline: navigator.onLine,
                isSlowConnection:
                    connection?.effectiveType !== '4g' &&
                    connection?.effectiveType !== undefined,
                effectiveType: connection?.effectiveType || 'unknown',
            });
        };

        // Initial status
        updateStatus();

        // Listen for changes
        window.addEventListener('online', updateStatus);
        window.addEventListener('offline', updateStatus);

        const connection =
            (navigator as any).connection ||
            (navigator as any).mozConnection ||
            (navigator as any).webkitConnection;

        if (connection) {
            connection.addEventListener('change', updateStatus);
        }

        return () => {
            window.removeEventListener('online', updateStatus);
            window.removeEventListener('offline', updateStatus);

            if (connection) {
                connection.removeEventListener('change', updateStatus);
            }
        };
    }, []);

    return status;
};
