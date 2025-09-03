/**
 * PWA Install Prompt Component
 * Универсальный компонент для установки PWA приложения
 */

class PWAInstallPrompt {
    constructor(options = {}) {
        this.options = {
            installText: '📱 Установить приложение',
            dismissText: 'Позже',
            title: 'Установить Beauty Care',
            description: 'Добавьте приложение на домашний экран для быстрого доступа и офлайн режима',
            icon: 'ui/brand/logo.svg',
            themeColor: '#C26A8D',
            ...options
        };

        this.deferredPrompt = null;
        this.installPrompt = null;
        this.isInstalled = false;

        this.init();
    }

    init() {
        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            console.log('✅ PWA: App is already installed');
            return;
        }

        // Listen for install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });

        // Listen for successful installation
        window.addEventListener('appinstalled', (e) => {
            console.log('✅ PWA: App was successfully installed');
            this.isInstalled = true;
            this.hideInstallPrompt();
            this.showSuccessMessage();
        });

        // Register service worker
        this.registerServiceWorker();
    }

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/BeautyCare-Site/service-worker.js')
                .then(registration => {
                    console.log('✅ PWA: Service Worker registered:', registration.scope);

                    // Handle updates
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                this.showUpdateNotification();
                            }
                        });
                    });
                })
                .catch(error => {
                    console.error('❌ PWA: Service Worker registration failed:', error);
                });
        }
    }

    showInstallPrompt() {
        if (this.isInstalled) return;

        // Create prompt element
        this.installPrompt = document.createElement('div');
        this.installPrompt.className = 'pwa-install-prompt';
        this.installPrompt.innerHTML = `
            <div class="pwa-install-content">
                <div class="pwa-install-icon">
                    <img src="${this.options.icon}" alt="Beauty Care" onerror="this.style.display='none'">
                </div>
                <div class="pwa-install-text">
                    <h3>${this.options.title}</h3>
                    <p>${this.options.description}</p>
                </div>
                <div class="pwa-install-actions">
                    <button class="pwa-install-btn">${this.options.installText}</button>
                    <button class="pwa-dismiss-btn">${this.options.dismissText}</button>
                </div>
                <button class="pwa-close-btn" aria-label="Закрыть">×</button>
            </div>
        `;

        // Add event listeners
        const installBtn = this.installPrompt.querySelector('.pwa-install-btn');
        const dismissBtn = this.installPrompt.querySelector('.pwa-dismiss-btn');
        const closeBtn = this.installPrompt.querySelector('.pwa-close-btn');

        installBtn.addEventListener('click', () => this.installPWA());
        dismissBtn.addEventListener('click', () => this.hideInstallPrompt());
        closeBtn.addEventListener('click', () => this.hideInstallPrompt());

        // Add to page
        document.body.appendChild(this.installPrompt);

        // Animate in
        setTimeout(() => {
            this.installPrompt.classList.add('visible');
        }, 100);
    }

    hideInstallPrompt() {
        if (this.installPrompt) {
            this.installPrompt.classList.remove('visible');
            setTimeout(() => {
                if (this.installPrompt && this.installPrompt.parentNode) {
                    this.installPrompt.parentNode.removeChild(this.installPrompt);
                    this.installPrompt = null;
                }
            }, 300);
        }
    }

    async installPWA() {
        if (!this.deferredPrompt) return;

        try {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;

            console.log('PWA install outcome:', outcome);

            if (outcome === 'accepted') {
                this.showSuccessMessage();
            }

            this.deferredPrompt = null;
            this.hideInstallPrompt();
        } catch (error) {
            console.error('PWA install error:', error);
        }
    }

    showSuccessMessage() {
        const successMsg = document.createElement('div');
        successMsg.className = 'pwa-success-message';
        successMsg.innerHTML = `
            <div class="pwa-success-content">
                <div class="pwa-success-icon">✅</div>
                <div class="pwa-success-text">
                    <h4>Приложение установлено!</h4>
                    <p>Теперь Beauty Care доступно на вашем домашнем экране</p>
                </div>
                <button class="pwa-success-close" onclick="this.parentNode.parentNode.remove()">×</button>
            </div>
        `;

        document.body.appendChild(successMsg);

        setTimeout(() => {
            if (successMsg && successMsg.parentNode) {
                successMsg.parentNode.removeChild(successMsg);
            }
        }, 5000);
    }

    showUpdateNotification() {
        const updateMsg = document.createElement('div');
        updateMsg.className = 'pwa-update-notification';
        updateMsg.innerHTML = `
            <div class="pwa-update-content">
                <div class="pwa-update-icon">🔄</div>
                <div class="pwa-update-text">
                    <h4>Доступно обновление</h4>
                    <p>Новая версия Beauty Care готова</p>
                </div>
                <div class="pwa-update-actions">
                    <button onclick="window.location.reload()">Обновить</button>
                    <button onclick="this.parentNode.parentNode.remove()">Позже</button>
                </div>
            </div>
        `;

        document.body.appendChild(updateMsg);
    }

    // Utility method to cache current page
    cacheCurrentPage(userId = 'anonymous', pageData = {}) {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'CACHE_REPORT',
                userId: userId,
                reportData: {
                    title: document.title || 'Beauty Care Page',
                    url: window.location.href,
                    type: 'page',
                    created: Date.now(),
                    ...pageData
                }
            });
        }
    }

    // Get cached reports
    getCachedReports(userId = 'anonymous') {
        return new Promise((resolve) => {
            if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                const messageHandler = (event) => {
                    if (event.data && event.data.type === 'CACHED_REPORTS_LIST') {
                        navigator.serviceWorker.removeEventListener('message', messageHandler);
                        resolve(event.data.reports || []);
                    }
                };

                navigator.serviceWorker.addEventListener('message', messageHandler);

                navigator.serviceWorker.controller.postMessage({
                    type: 'GET_CACHED_REPORTS',
                    userId: userId
                });

                // Timeout fallback
                setTimeout(() => {
                    navigator.serviceWorker.removeEventListener('message', messageHandler);
                    resolve([]);
                }, 5000);
            } else {
                resolve([]);
            }
        });
    }
}

// Auto-initialize if script is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pwaInstallPrompt = new PWAInstallPrompt();
    });
} else {
    window.pwaInstallPrompt = new PWAInstallPrompt();
}

// CSS Styles for PWA components
const pwaStyles = `
<style>
.pwa-install-prompt {
    position: fixed;
    bottom: 20px;
    left: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    opacity: 0;
    transform: translateY(100px);
    transition: all 0.3s ease;
    max-width: 400px;
    margin: 0 auto;
}

.pwa-install-prompt.visible {
    opacity: 1;
    transform: translateY(0);
}

.pwa-install-content {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    position: relative;
}

.pwa-install-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: linear-gradient(135deg, #C26A8D, #C9B7FF);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.pwa-install-icon img {
    width: 32px;
    height: 32px;
    border-radius: 8px;
}

.pwa-install-text {
    flex: 1;
}

.pwa-install-text h3 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.pwa-install-text p {
    margin: 0;
    font-size: 14px;
    color: #666;
    line-height: 1.4;
}

.pwa-install-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.pwa-install-btn {
    background: #C26A8D;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s ease;
}

.pwa-install-btn:hover {
    background: #B0557A;
}

.pwa-dismiss-btn {
    background: none;
    color: #666;
    border: none;
    padding: 4px 16px;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s ease;
}

.pwa-dismiss-btn:hover {
    background: rgba(0, 0, 0, 0.05);
}

.pwa-close-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: none;
    border: none;
    font-size: 20px;
    color: #999;
    cursor: pointer;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.2s ease;
}

.pwa-close-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: #666;
}

.pwa-success-message {
    position: fixed;
    top: 20px;
    left: 20px;
    right: 20px;
    background: #4CAF50;
    color: white;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(76, 175, 80, 0.3);
    z-index: 1001;
    max-width: 400px;
    margin: 0 auto;
}

.pwa-success-content {
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
}

.pwa-success-icon {
    font-size: 24px;
}

.pwa-success-text h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
}

.pwa-success-text p {
    margin: 0;
    font-size: 14px;
    opacity: 0.9;
}

.pwa-success-close {
    position: absolute;
    top: -4px;
    right: -4px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}

.pwa-update-notification {
    position: fixed;
    top: 20px;
    left: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    z-index: 1001;
    max-width: 400px;
    margin: 0 auto;
}

.pwa-update-content {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
}

.pwa-update-icon {
    font-size: 24px;
}

.pwa-update-text h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.pwa-update-text p {
    margin: 0;
    font-size: 14px;
    color: #666;
}

.pwa-update-actions {
    display: flex;
    gap: 8px;
    margin-left: auto;
}

.pwa-update-actions button {
    padding: 6px 12px;
    border: none;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
}

.pwa-update-actions button:first-child {
    background: #C26A8D;
    color: white;
}

.pwa-update-actions button:last-child {
    background: #f5f5f5;
    color: #333;
}

@media (max-width: 480px) {
    .pwa-install-content {
        flex-direction: column;
        text-align: center;
        gap: 16px;
    }

    .pwa-install-actions {
        flex-direction: row;
        width: 100%;
    }

    .pwa-install-btn,
    .pwa-dismiss-btn {
        flex: 1;
    }
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', pwaStyles);

console.log('🎯 PWA Install Prompt component loaded');
