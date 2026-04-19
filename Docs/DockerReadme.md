1) Сборка образа бекенда \
docker build -t map_image  .
 

2) Создать докер сеть \
docker network create MapNetwork


3) Создание образа БД \
docker run --name map_db \
-p 6432:5432 \
-e POSTGRES_USER=postgres \
-e POSTGRES_PASSWORD=09876543210hh \
-e POSTGRES_DB=MapApp \
--network=MapNetwork \
--volume pg-map-data:/var/lib/postgresql/data \
-d postgres:16


4) Создание образа Redis \
docker run --name map_cache \
-p 7379:6379 \
--network=MapNetwork \
-d redis:7.4 \


5) Запустить docker-compose.yml

Запуск контейнера с приложением \
docker run --name map_back \
-p 8000:8000 \
--network=MapNetwork \
map_image


#### Вставка моковых даннных в БД:
Выполнить команду:  \
docker exec -it map_back src/seed_data.py