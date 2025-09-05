# 🚀 Развертывание на GitHub Pages

## Что нужно сделать:

### 1. Создать ветку `gh-pages`
```bash
# В Git Bash или другом терминале:
git checkout -b gh-pages
```

### 2. Скопировать файлы в корень репозитория
```bash
# Скопировать основные HTML файлы:
cp VIEW_ALL.html index.html
cp ui/demo/preview.html demo.html
cp ui/brand/preview.html brand.html
cp ui/brand/convert-svg-to-png.html converter.html

# Скопировать папки:
cp -r ui/brand/stickers/ stickers/
cp -r ui/brand/ logos/
```

### 3. Настроить GitHub Pages
1. Зайти в репозиторий на GitHub
2. Settings → Pages
3. Source: "Deploy from a branch"
4. Branch: "gh-pages" → "/ (root)"
5. Save

### 4. Push на GitHub
```bash
git add .
git commit -m "feat: add demo website for partners"
git push origin gh-pages
```

---

## 🎯 Результат:

Через 2-3 минуты сайт будет доступен по адресу:
**`https://markgerber1.github.io/skin-advisor/`**

---

## 📁 Что будет на сайте:

- **Главная страница**: `https://markgerber1.github.io/skin-advisor/`
- **Дизайн-система**: `https://markgerber1.github.io/skin-advisor/demo.html`
- **Бренд активы**: `https://markgerber1.github.io/skin-advisor/brand.html`
- **Конвертер**: `https://markgerber1.github.io/skin-advisor/converter.html`

---

## 🎨 Что увидит партнер:

1. **Красивый сайт** с демонстрацией всех материалов
2. **Интерактивные демо** компонентов
3. **Брендовые активы** (логотипы и стикеры)
4. **Отчет** о проделанной работе
5. **Документацию** по использованию

---

## 💡 Альтернативы (если GitHub не подходит):

### Netlify (бесплатно):
1. Зарегистрироваться на netlify.com
2. Drag & drop папку `ui/` в браузер
3. Получить бесплатный домен типа `beauty-demo.netlify.app`

### Vercel (бесплатно):
1. Зарегистрироваться на vercel.com
2. Импортировать из GitHub
3. Автоматическое развертывание

---

## 🔥 Готовый план действий:

1. **Сейчас**: Создать ветку gh-pages
2. **Скопировать**: Основные HTML файлы в корень
3. **Push**: На GitHub
4. **Настроить**: GitHub Pages в настройках
5. **Результат**: Сайт готов через 2-3 минуты!

Хотите, чтобы я создал готовый скрипт для автоматизации этого процесса?



