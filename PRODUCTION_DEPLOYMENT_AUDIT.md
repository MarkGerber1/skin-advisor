# 🚀 ПРОД-ЦИКЛ АУДИТ: GitHub → Actions → Railway

## 📊 АУДИТ ТЕКУЩЕГО СОСТОЯНИЯ

### 🔍 Git Branches & Remote Info

**Локальные ветки:**
- `master` (текущая)
- `demo-site`

**Удаленные ветки:**
- `origin/HEAD -> origin/main` (GitHub default branch = **main**)
- `origin/main` (tracked)
- `origin/master` (tracked)
- `origin/demo-site` (tracked)

**Remote configuration:**
- HEAD branch: **main** (нужно изменить на master)
- Local master merges with remote master
- Push destinations настроены корректно

### ⚙️ GitHub Actions Workflows

**Существующие workflows:**

#### 1. `ci.yml` - CI Pipeline
```yaml
on:
  push: [master, main]      # ✅ Обе ветки
  pull_request: [master, main]
```
- ✅ Python 3.11, dependencies install
- ✅ Black formatting + Ruff linting
- ✅ Auto-commit formatting changes
- ✅ Python compilation check
- ✅ Smoke tests (render, flow, cart, affiliate)

#### 2. `railway-deploy.yml` - Deploy Pipeline
```yaml
on:
  push: ["master"]          # ✅ Только master
  workflow_run: ["CI"] completed
```
- ✅ Depends on CI success
- ✅ Railway CLI via curl
- ✅ Login with RAILWAY_TOKEN
- ✅ Deploy via `railway up`

### 🎯 ПРОБЛЕМЫ ВЫЯВЛЕНЫ

#### 🚨 Critical Issues:
1. **Default branch = `main`** (должен быть `master`)
2. **Две прод-ветки** создают путаницу
3. **Branch protection** отсутствует
4. **Preview deployments** не настроены

#### ⚠️ Configuration Issues:
1. CI workflow запускается на обеих ветках
2. Нет status checks requirement
3. Нет branch protection rules
4. Railway может деплоить из main вместо master

### 📋 ПЛАН НОРМАЛИЗАЦИИ

#### Phase 1: Branch Normalization
- [ ] Изменить default branch на `master` в GitHub
- [ ] Настроить branch protection для `master`
- [ ] Удалить/заморозить ветку `main`

#### Phase 2: CI/CD Optimization
- [ ] Обновить CI workflow (только master)
- [ ] Настроить status checks
- [ ] Добавить deploy-production workflow

#### Phase 3: Railway Configuration
- [ ] Подтвердить deploy из master
- [ ] Включить Preview Environments
- [ ] Настроить переменные окружения

#### Phase 4: Testing & Validation
- [ ] Тестовый commit в master
- [ ] Создание PR с preview deploy
- [ ] Проверка автоматического удаления preview

---

## ✅ ВЫПОЛНЕННЫЕ ШАГИ

### Phase 1: ✅ Branch Normalization
- ✅ Синхронизирован main с master
- ✅ Запушен обновленный main в GitHub
- ✅ Готово к смене default branch

### Phase 2: ✅ CI/CD Optimization
- ✅ Обновлен CI workflow (только master)
- ✅ Создан production deployment workflow
- ✅ Создан preview deployment workflow
- ✅ Настроена автоматическая очистка preview

### Phase 3: 🚧 Railway Configuration (Требует ручной настройки)
- ✅ Обновлена railway.json (Dockerfile.simple)
- ✅ Удален конфликтующий railway.toml
- ⚠️ **Требуется:** Изменить default branch в GitHub на master
- ⚠️ **Требуется:** Настроить branch protection rules

### Phase 4: 🔄 Testing & Validation (Ожидает)

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ (РУЧНЫЕ ДЕЙСТВИЯ)

### 1. Изменить Default Branch в GitHub
```
GitHub → Settings → Branches
- Default branch: master (вместо main)
- Save changes
```

### 2. Настроить Branch Protection Rules
```
GitHub → Settings → Branches → Add rule
- Branch name pattern: master
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
  - Status checks: CI, build-test
- ✅ Require linear history
- ✅ Include administrators
- Create
```

### 3. Проверить Railway Settings
```
Railway Dashboard → Project Settings
- ✅ Repository: MarkGerber1/skin-advisor
- ✅ Branch: master
- ✅ Auto deploy: ON
- ✅ Preview Environments: ON
- ✅ Destroy Previews on merge/close: ON
```

### 4. Настроить Secrets в GitHub
```
GitHub → Settings → Secrets and variables → Actions
- ✅ RAILWAY_TOKEN: [ваш токен]
```

### 5. Тестирование
```bash
# Создать тестовый коммит в master
git commit -m "test: production deployment test"
git push

# Проверить:
# - ✅ CI workflow запустился
# - ✅ Production deploy запустился после CI
# - ✅ Railway получил обновление
```

---

## 📋 ТЕКУЩЕЕ СОСТОЯНИЕ

| Компонент | Статус | Действие |
|-----------|--------|----------|
| Git Branches | ✅ Синхронизированы | Готово |
| GitHub Actions | ✅ Настроены | Готово |
| Railway Config | ⚠️ Частично | Требует ручной настройки |
| Branch Protection | ❌ Отсутствует | Требует настройки в GitHub |
| Preview Deploy | ✅ Настроен | Готово |

**Текущее состояние:** 🟡 Готово к финальной настройке
**Целевое состояние:** 🟢 Полный прод-цикл работает

---

## 🚀 ФИНАЛЬНЫЕ ШАГИ ДЛЯ ЗАПУСКА

### Шаг 1: GitHub Settings
1. **Изменить default branch** на `master`
2. **Настроить branch protection** для `master`
3. **Добавить RAILWAY_TOKEN** в secrets

### Шаг 2: Railway Settings
1. **Подтвердить branch** = `master`
2. **Включить Preview Environments**
3. **Проверить Auto Deploy**

### Шаг 3: Тестирование
1. **Push в master** → должен запуститься CI
2. **После CI success** → должен запуститься production deploy
3. **Создать PR** → должен появиться preview deploy

### Шаг 4: Очистка (опционально)
```bash
# После успешного тестирования можно удалить main:
git push origin --delete main
git branch -d main
```

---

## 📊 ПРОВЕРКА ГОТОВНОСТИ

**Когда все настроено правильно:**
- ✅ Push в `master` → `CI` → `Deploy Production`
- ✅ PR в `master` → `Preview Deploy` + комментарий с URL
- ✅ Merge PR → автоматическая очистка preview
- ✅ Branch protection блокирует прямые push в master
- ✅ Railway деплоит только из master

**Система готова к production!** 🎉

---
*Отчет обновлен: после настройки workflows*
*Следующий шаг: Ручная настройка GitHub + Railway*
