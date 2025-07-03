# Qdrant Vector Store and UI Setup Guide

Это руководство описывает как использовать новые функции Morphik:
1. **Поддержка Qdrant** как векторное хранилище
2. **Полноценный WebUI** на localhost:3000 через Docker

## 🔥 Новые функции

### 1. Поддержка Qdrant Vector Database

Qdrant - это высокопроизводительная векторная база данных, которая может использоваться вместо pgvector.

**Преимущества Qdrant:**
- Высокая производительность для векторного поиска
- Масштабируемость
- Поддержка кластеризации
- Веб-интерфейс для мониторинга
- Гибкая фильтрация метаданных

### 2. WebUI на localhost:3000

Полноценный Next.js интерфейс для работы с Morphik через веб-браузер.

**Возможности UI:**
- Интерактивный чат с документами
- Загрузка и управление документами  
- Просмотр результатов поиска
- Визуализация графов знаний
- Настройка параметров

## 🚀 Быстрый запуск

### Вариант 1: Использование Qdrant + UI

```bash
# 1. Клонировать репозиторий (если еще не сделано)
git clone <repository>
cd morphik-core

# 2. Скопировать конфигурацию Qdrant
cp morphik.qdrant.toml morphik.toml

# 3. Запустить все сервисы с UI
docker-compose up -d

# 4. Проверить что все сервисы запущены
docker-compose ps
```

**Доступные сервисы:**
- **Morphik API**: http://localhost:8000
- **WebUI**: http://localhost:3000
- **Qdrant**: http://localhost:6333
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Вариант 2: Только добавить UI к существующей установке

```bash
# Если у вас уже настроен Morphik с pgvector, просто добавьте UI:
docker-compose up ui -d
```

UI будет доступен на http://localhost:3000

## ⚙️ Детальная настройка

### Настройка Qdrant

1. **Обновите morphik.toml для использования Qdrant:**

```toml
[vector_store]
provider = "qdrant"
host = "localhost"  # Используйте "qdrant" при запуске в Docker
port = 6333
collection_name = "morphik_embeddings"
```

2. **Опциональные переменные среды:**

```bash
# Если используете Qdrant Cloud
export QDRANT_API_KEY="your-api-key-here"
```

3. **Qdrant с внешним хостом:**

```toml
[vector_store]
provider = "qdrant"
host = "your-qdrant-host.com"
port = 6333
collection_name = "morphik_embeddings"
```

### Настройка UI

1. **Переменные среды для UI (опционально):**

```bash
# Если API работает на другом хосте
export NEXT_PUBLIC_API_URL="http://your-api-host:8000"
```

2. **Для разработки UI:**

```bash
cd ee/ui-component
npm install
npm run dev
```

UI будет доступен на http://localhost:3000

## 🐳 Docker Compose файлы

Проект теперь включает следующие сервисы в `docker-compose.yml`:

```yaml
services:
  morphik:      # API сервер (порт 8000)
  worker:       # Background worker
  postgres:     # PostgreSQL база данных
  redis:        # Redis для очередей
  qdrant:       # Qdrant векторная БД (порт 6333)
  ui:           # Next.js веб-интерфейс (порт 3000)
  ollama:       # Ollama LLM сервер (опционально)
```

## 🔧 Конфигурация

### Переключение между pgvector и Qdrant

**Для pgvector (по умолчанию):**
```toml
[vector_store]
provider = "pgvector"
```

**Для Qdrant:**
```toml
[vector_store]
provider = "qdrant"
host = "localhost"
port = 6333
collection_name = "morphik_embeddings"
```

### Настройка подключения к UI

В конфигурации PDF viewer:
```toml
[pdf_viewer]
frontend_url = "http://localhost:3000/api/pdf"
```

## ⚠️ Важные замечания

### ColPali поддержка

**Внимание:** ColPali (многовекторные эмбеддинги для изображений) пока поддерживается только с PostgreSQL:

```toml
# Если используете ColPali, оставьте pgvector
[vector_store]
provider = "pgvector"

[morphik]
enable_colpali = true
colpali_mode = "local"
```

### Миграция данных

При переключении с pgvector на Qdrant:
1. Данные НЕ переносятся автоматически
2. Потребуется повторная индексация документов
3. Рекомендуется создать бэкап перед переключением

## 🔍 Мониторинг и отладка

### Qdrant Dashboard

Посетите http://localhost:6333/dashboard для:
- Просмотра коллекций
- Мониторинга производительности
- Отладки запросов

### Логи сервисов

```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f morphik
docker-compose logs -f qdrant
docker-compose logs -f ui
```

### Health checks

```bash
# Проверка API
curl http://localhost:8000/health

# Проверка Qdrant
curl http://localhost:6333/health

# Проверка UI
curl http://localhost:3000
```

## 🛠️ Разработка

### Разработка UI

```bash
cd ee/ui-component
npm install
npm run dev
```

### Добавление новых векторных хранилищ

1. Создайте новый класс в `core/vector_store/`, наследуясь от `BaseVectorStore`
2. Обновите `core/config.py` для добавления нового провайдера
3. Обновите `core/services_init.py` и `core/workers/ingestion_worker.py`

### Кастомизация UI

UI компоненты находятся в:
- `ee/ui-component/components/` - React компоненты
- `ee/ui-component/app/` - Next.js страницы
- `ee/ui-component/lib/` - Утилиты

## 📊 Производительность

### Qdrant vs pgvector

| Метрика | pgvector | Qdrant |
|---------|----------|---------|
| Скорость поиска | Хорошая | Отличная |
| Масштабируемость | Ограничена PostgreSQL | Высокая |
| Память | Зависит от PostgreSQL | Оптимизированная |
| Кластеризация | Нет | Да |

### Рекомендации

- **Малые проекты (< 100k векторов):** pgvector достаточно
- **Средние проекты (100k - 1M векторов):** Qdrant рекомендуется
- **Большие проекты (> 1M векторов):** Обязательно Qdrant

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь что все сервисы запущены: `docker-compose ps`
3. Проверьте конфигурацию в `morphik.toml`
4. Создайте issue в репозитории с детальным описанием проблемы

## 📝 Примеры использования

### Пример запроса к API через UI

1. Откройте http://localhost:3000
2. Загрузите документ через интерфейс
3. Задайте вопрос в чате
4. Получите ответ с контекстом из документа

### Пример работы с Qdrant API

```python
from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)

# Просмотр коллекций
collections = client.get_collections()
print(f"Collections: {collections}")

# Поиск похожих векторов
results = client.search(
    collection_name="morphik_embeddings",
    query_vector=[0.1, 0.2, ...],  # ваш вектор запроса
    limit=5
)
```

---

**Удачи в использовании новых функций Morphik! 🚀**