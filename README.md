# Фудграм

## Описание проекта:
«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Развернутый проект: https://foodgramgram.zapto.org/

Репозиторий: https://github.com/Yulia-by/foodgram


## Стек технологий:
Django,  PostgreSQL,  React,  Nginx,  Docker,  GitHub,  Actions
## Устанавливаем Docker Compose на сервер:

Поочерёдно выполните на сервере команды для установки Docker и Docker Compose для Linux.

```bash
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```

Скопируйте на сервер в директорию проекта файл docker-compose.production.yml. Сделать это можно, например, при помощи утилиты SCP (secure copy) — она предназначена для копирования файлов между компьютерами. Зайдите на своём компьютере в директорию проекта и выполните команду копирования:

```bash
scp -i path_to_SSH/SSH_name docker-compose.production.yml \
    username@server_ip:/home/username/<директория проекта>/docker-compose.production.yml
```
- path_to_SSH — путь к файлу с SSH-ключом;
- SSH_name — имя файла с SSH-ключом (без расширения);
- username — ваше имя пользователя на сервере;
- server_ip — IP вашего сервера.

Скопируйте файл .env на сервер, в директорию проекта:

```bash
scp -i path_to_SSH/SSH_name .env \
    username@server_ip:/home/username/<директория проекта>/.env
```

На сервере в редакторе nano откройте конфиг Nginx: sudo nano /etc/nginx/sites-enabled/default. Измените все настройки location на одну в секции server.

```bash
location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:7000;
    }
```
Перезагрузите конфиг Nginx:

```bash
sudo service nginx reload
```
Загрузить образы из DockerHub:

```bash
sudo docker compose -f docker-compose.production.yml pull
```

Выполнить миграции:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
Собрать статику:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```

Создать суперпользователя (указать логин, e-mail, пароль):

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

Загрузить список ингредиентов в базу данных:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
```

## Workflow для обновления проекта на сервере:

Чтобы обновить проект на продакшене, нужно:

- выполнить на команду docker compose pull, чтобы скачать с Docker Hub на сервер обновлённые образы для контейнеров;
- перезапустить контейнеры из обновлённых образов.
При выполнении этих задач «вручную» разработчик соединяется по SSH с сервером и отправляет на сервер команды docker compose pull, docker compose down и docker compose up. После этого — выполняет команды для миграций и сборки статики. При работе с GitHub Actions эти действия должен выполнить раннер, читая инструкции из workflow.

Перейдите в настройки репозитория GitHub — Settings, выберите на панели слева Secrets and Variables → Actions, нажмите New repository secret.

Сохраните необходимые переменные с необходимыми значениями.

Ваш продакшен-сервер будет получать команды не с вашего компьютера, а от сервера GitHub Actions.

Сделайте коммит и пуш в репозиторий и проверьте, что все шаги выполнились.

Индикатор состояния рабочего процесса:

[![Main Foodgram Workflow](https://github.com/Yulia-by/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Yulia-by/foodgram/actions/workflows/main.yml)
## Автор:

[@Yulia-by](https://www.github.com/Yulia-by)
