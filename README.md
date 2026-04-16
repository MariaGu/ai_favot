docker build -t trend_analytics:latest .
docker tag trend_analytics:latest mariagubina/trend_analytics:latest
docker push mariagubina/trend_analytics:latest

docker build -t web_app:latest .
docker tag web_app:latest mariagubina/web_app:latest
docker push mariagubina/web_app:latest

docker build -t collect_articles:latest .
docker tag collect_articles:latest mariagubina/collect_articles:latest
docker push mariagubina/collect_articles:latest

docker build -t generate_article:latest .
docker tag generate_article:latest mariagubina/generate_article:latest
docker push mariagubina/generate_article:latest