'use client';

import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import { useInstallPrompt } from '@/hooks/useInstallPrompt';

export const PWAInstallButton = () => {
    const { isInstallable, promptInstall } = useInstallPrompt();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted || !isInstallable) {
        return null;
    }

    return (
        <button
            onClick={promptInstall}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium transition-colors"
            title="Install AutoIntern as an app on your device"
        >
            <Download className="w-4 h-4" />
            Install App
        </button>
    );
};
