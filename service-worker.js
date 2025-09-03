/**
 * Service Worker для Beauty Care PWA
 * Кеширует статические ассеты и персональные отчеты для офлайн-доступа
 */

const CACHE_NAME = 'beauty-care-v1.0.0';
const OFFLINE_URL = '/BeautyCare-Site/offline.html';

// Ресурсы для кеширования при установке
const STATIC_CACHE_URLS = [
  '/BeautyCare-Site/',
  '/BeautyCare-Site/index.html',
  '/BeautyCare-Site/demo.html',
  '/BeautyCare-Site/brand.html',
  '/BeautyCare-Site/offline.html',
  '/BeautyCare-Site/manifest.json',
  '/BeautyCare-Site/ui/theme/tokens.css',
  '/BeautyCare-Site/ui/theme/skins.css',
  '/BeautyCare-Site/ui/components/index.css',
  '/BeautyCare-Site/ui/icons/icons.svg',
  '/BeautyCare-Site/ui/brand/logo.svg',
  '/BeautyCare-Site/ui/brand/logo-dark.svg',
  '/BeautyCare-Site/ui/brand/stickers/palette.svg',
  '/BeautyCare-Site/ui/brand/stickers/drop.svg',
  '/BeautyCare-Site/ui/brand/stickers/heart-lipstick.svg',
  '/BeautyCare-Site/ui/icons/svg/palette.svg',
  '/BeautyCare-Site/ui/icons/svg/drop.svg',
  '/BeautyCare-Site/ui/icons/svg/cart.svg',
  '/BeautyCare-Site/ui/icons/svg/info.svg',
  '/BeautyCare-Site/ui/icons/svg/list.svg',
  '/BeautyCare-Site/ui/icons/svg/settings.svg'
];

// Ресурсы для динамического кеширования (отчеты)
const DYNAMIC_CACHE_PATTERNS = [
  /\/data\/reports\/.*\.pdf$/,
  /\/data\/reports\/.*\.html$/,
  /\/output\/cards\/.*\.svg$/,
  /\/output\/cards\/.*\.png$/,
  /\/assets\/.*\.(json|yaml)$/,
  /\/data\/.*\.json$/
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing...');

  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);

      try {
        // Кешируем статические ресурсы
        await cache.addAll(STATIC_CACHE_URLS);
        console.log('✅ Service Worker: Static assets cached');
      } catch (error) {
        console.error('❌ Service Worker: Failed to cache static assets:', error);
        // Продолжаем установку даже при ошибке кеширования
      }

      // Принудительно активируем новый service worker
      await self.skipWaiting();
      console.log('✅ Service Worker: Installation completed');
    })()
  );
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker: Activating...');

  event.waitUntil(
    (async () => {
      // Очищаем старые кеши
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );

      // Принимаем контроль над всеми клиентами
      await self.clients.claim();
      console.log('✅ Service Worker: Activation completed');
    })()
  );
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
  // Пропускаем не-GET запросы
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);

  // Обрабатываем запросы к нашему домену
  if (url.origin === self.location.origin) {
    // Проверяем, является ли ресурс динамическим (отчеты, данные)
    const isDynamicResource = DYNAMIC_CACHE_PATTERNS.some(pattern =>
      pattern.test(url.pathname)
    );

    if (isDynamicResource) {
      // Стратегия: Network First с fallback на cache для динамических ресурсов
      event.respondWith(
        (async () => {
          try {
            // Сначала пытаемся получить из сети
            const networkResponse = await fetch(event.request);
            if (networkResponse.ok) {
              // Обновляем кеш
              const cache = await caches.open(CACHE_NAME);
              cache.put(event.request, networkResponse.clone());
              console.log('📥 Service Worker: Updated cache for:', url.pathname);
            }
            return networkResponse;
          } catch (error) {
            // Если сеть недоступна, ищем в кеше
            const cachedResponse = await caches.match(event.request);
            if (cachedResponse) {
              console.log('📤 Service Worker: Served from cache:', url.pathname);
              return cachedResponse;
            }

            // Если ничего нет в кеше, возвращаем офлайн страницу для отчетов
            if (url.pathname.includes('/reports/') || url.pathname.includes('/data/')) {
              const offlineResponse = await caches.match(OFFLINE_URL);
              if (offlineResponse) {
                return offlineResponse;
              }
            }

            throw error;
          }
        })()
      );
    } else {
      // Стратегия: Cache First для статических ресурсов
      event.respondWith(
        (async () => {
          const cachedResponse = await caches.match(event.request);
          if (cachedResponse) {
            return cachedResponse;
          }

          try {
            const networkResponse = await fetch(event.request);
            if (networkResponse.ok) {
              const cache = await caches.open(CACHE_NAME);
              cache.put(event.request, networkResponse.clone());
            }
            return networkResponse;
          } catch (error) {
            // Для HTML страниц возвращаем офлайн страницу
            if (event.request.headers.get('accept').includes('text/html')) {
              const offlineResponse = await caches.match(OFFLINE_URL);
              if (offlineResponse) {
                return offlineResponse;
              }
            }
            throw error;
          }
        })()
      );
    }
  }
});

// Обработка сообщений от основного потока
self.addEventListener('message', (event) => {
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'CACHE_REPORT':
        // Кеширование персонального отчета
        cacheUserReport(event.data.userId, event.data.reportData);
        break;

      case 'GET_CACHED_REPORTS':
        // Получение списка кешированных отчетов
        getCachedReports(event.data.userId);
        break;

      case 'CLEAR_CACHE':
        // Очистка кеша
        clearUserCache(event.data.userId);
        break;
    }
  }
});

// Функция кеширования персонального отчета
async function cacheUserReport(userId, reportData) {
  try {
    const cache = await caches.open(CACHE_NAME);

    // Кешируем PDF отчет
    if (reportData.pdfUrl) {
      await cache.add(reportData.pdfUrl);
      console.log('📄 Service Worker: Cached PDF report for user:', userId);
    }

    // Кешируем JSON данные
    if (reportData.jsonData) {
      const jsonResponse = new Response(JSON.stringify(reportData.jsonData), {
        headers: { 'Content-Type': 'application/json' }
      });
      await cache.put(`/data/reports/user_${userId}_latest.json`, jsonResponse);
      console.log('📋 Service Worker: Cached JSON data for user:', userId);
    }

    // Кешируем визуальные карточки
    if (reportData.cardUrls && Array.isArray(reportData.cardUrls)) {
      for (const cardUrl of reportData.cardUrls) {
        try {
          await cache.add(cardUrl);
          console.log('🎨 Service Worker: Cached card:', cardUrl);
        } catch (error) {
          console.warn('⚠️ Service Worker: Failed to cache card:', cardUrl, error);
        }
      }
    }

    // Отправляем подтверждение клиенту
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'REPORT_CACHED',
        userId: userId,
        timestamp: Date.now()
      });
    });

  } catch (error) {
    console.error('❌ Service Worker: Failed to cache user report:', error);
  }
}

// Функция получения списка кешированных отчетов
async function getCachedReports(userId) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();

    const reports = [];
    const reportPattern = new RegExp(`user_${userId}.*\.(pdf|json)$`);

    for (const request of keys) {
      if (reportPattern.test(request.url)) {
        const response = await cache.match(request);
        if (response) {
          const contentType = response.headers.get('content-type');
          reports.push({
            url: request.url,
            type: contentType?.includes('pdf') ? 'pdf' : 'json',
            cachedAt: Date.now()
          });
        }
      }
    }

    // Отправляем список отчетов клиенту
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'CACHED_REPORTS_LIST',
        userId: userId,
        reports: reports
      });
    });

  } catch (error) {
    console.error('❌ Service Worker: Failed to get cached reports:', error);
  }
}

// Функция очистки кеша пользователя
async function clearUserCache(userId) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();

    const userPattern = new RegExp(`user_${userId}`);
    const deletedUrls = [];

    for (const request of keys) {
      if (userPattern.test(request.url)) {
        await cache.delete(request);
        deletedUrls.push(request.url);
      }
    }

    console.log('🗑️ Service Worker: Cleared cache for user:', userId, deletedUrls);

    // Отправляем подтверждение клиенту
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'CACHE_CLEARED',
        userId: userId,
        deletedUrls: deletedUrls
      });
    });

  } catch (error) {
    console.error('❌ Service Worker: Failed to clear user cache:', error);
  }
}

// Обработка push-уведомлений (для будущего использования)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();

    const options = {
      body: data.body,
      icon: '/BeautyCare-Site/ui/brand/logo.svg',
      badge: '/BeautyCare-Site/ui/brand/stickers/drop.svg',
      vibrate: [100, 50, 100],
      data: {
        url: data.url || '/BeautyCare-Site/'
      }
    };

    event.waitUntil(
      self.registration.showNotification(data.title || 'Beauty Care', options)
    );
  }
});

// Обработка клика по уведомлению
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    self.clients.openWindow(event.notification.data.url || '/BeautyCare-Site/')
  );
});

console.log('🎯 Service Worker: Loaded and ready');

