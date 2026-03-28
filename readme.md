# TeamFinder — Платформа для поиска команды

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## О проекте

**TeamFinder** — это веб-платформа для поиска единомышленников и создания команд для pet-проектов. 
Сервис помогает разработчикам, дизайнерам и другим IT-специалистам находить соратников для 
совместной работы над интересными идеями.

### Зачем это нужно?

- 🚀 **Найти команду мечты**: публикуйте свои проекты и находите участников с нужными навыками
- 💡 **Развивать идеи**: превращайте одиночные pet-проекты в командные разработки
- 🤝 **Нетворкинг**: знакомьтесь с профессионалами из разных областей IT
- 📈 **Рост навыков**: учитесь у коллег и делитесь опытом

### Основные возможности

#### Для всех пользователей:
- **Просмотр проектов** с фильтрацией по навыкам
- **Поиск участников** в открытых проектах
- **Детальная информация** о проектах и их авторах

#### Для авторизованных пользователей:
- **Создание проектов** с указанием требуемых навыков
- **Участие в проектах** (AJAX toggle, без перезагрузки)
- **Избранные проекты** (AJAX toggle, без перезагрузки)
- **Редактирование профиля** с валидацией телефона и GitHub
- **Смена пароля**
- **Управление навыками проекта** (добавление/удаление)

#### Особенности Варианта 3:
- 🎯 **Навыки проектов** — привязка технологий к проекту
- 🔍 **Автодополнение навыков** — умный поиск при добавлении
- 📊 **Фильтрация по навыкам** — быстрый поиск нужных проектов

### Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | Django 5.2 |
| Database | PostgreSQL 14 |
| Frontend | HTML5, CSS3, JavaScript (AJAX) |
| Image Processing | Pillow (генерация аватаров) |
| Authentication | Кастомный User (email как username) |
| Deployment | Docker, Docker Compose |

---

## Быстрый старт (Docker)

```bash
cp .env_example .env      # при необходимости отредактируйте пароли
docker compose up --build
```

После старта:
```bash
docker compose exec web python manage.py seed   # тестовые данные
```

Приложение доступно по адресу: http://localhost:8000

---

## Локальная разработка (без Docker)

**Требования:** Python 3.12+, PostgreSQL 14+

```bash
# 1. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Зависимости
pip install Django==5.2.4 pillow==11.3.0 psycopg2-binary==2.9.10 python-decouple==3.8

# 3. Переменные окружения
cp .env_example .env
# Укажите в .env параметры БД и TASK_VERSION=3

# 4. Только БД в Docker (опционально)
docker compose up db -d

# 5. Миграции
python manage.py migrate

# 6. Тестовые данные
python manage.py seed

# 7. Запуск
python manage.py runserver
```

---

## Тесты

```bash
# Локально (SQLite)
DJANGO_SETTINGS_MODULE=test_settings PYTHONPATH=/tmp:. python manage.py test users projects -v 2

# Или с PostgreSQL (после migrate)
python manage.py test users projects
```

Текущий результат: **51 тест, 0 ошибок**.

---

## Тестовый аккаунт

После `python manage.py seed`:

| Email | Пароль |
|-------|--------|
| maria@yandex.ru | password |
| admin@teamfinder.ru | adminpass123 |

---

## Структура проекта

```
team_finder/        — настройки Django
users/              — кастомная модель User, регистрация/авторизация
  ├── models.py     — User с авто-генерацией аватарки (Pillow)
  ├── forms.py      — все формы с валидацией телефона и GitHub URL
  ├── views.py      — auth views + профиль
  ├── backends.py   — аутентификация по email
  └── management/commands/seed.py
projects/           — проекты, навыки, избранное
  ├── models.py     — Project, Skill
  ├── forms.py      — ProjectForm с валидацией GitHub URL
  └── views.py      — CRUD + AJAX endpoints (participate, complete, fav, skills)
templates_var3/     — готовые HTML-шаблоны (Вариант 3)
static/             — CSS, JS, шрифты, картинки
```

---

## Реализованные фичи

- Кастомный `User` (email вместо username), авто-аватарка с буквой
- Регистрация, вход, выход, редактирование профиля, смена пароля
- Валидация телефона (форматы `8XXXXXXXXXX` / `+7XXXXXXXXXX`, нормализация, уникальность)
- Создание, редактирование, завершение проектов
- Участие в проектах (AJAX toggle)
- Избранные проекты (AJAX toggle)
- **[Вариант 3]** Навыки проекта — добавление/удаление без перезагрузки
- **[Вариант 3]** Автодополнение навыков (`GET /projects/skills/?q=`)
- **[Вариант 3]** Фильтрация проектов по навыку (`?skill=`)
- Пагинация (12 проектов/пользователей на странице)

Найти разработчика можно на
https://github.com/Bidulusha
или написать ему на почту
andreev.vadim.a@mail.ru