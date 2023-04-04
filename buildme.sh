DOCKER_BUILDKIT=1 docker build --platform amd64 -t sthv/mfb-grid:latest .
#docker run --rm -p 0.0.0.0:4777:4777  -p 0.0.0.0:5777:5777 --tty --env HASURA_GQL_ENDPOINT=http://51.250.47.166:8080/v1/graphql  --name mfb-grid sthv/mfb-grid

docker tag sthv/mfb-grid  cr.yandex/crpfskvn79g5ht8njq0k/contextmachine-mfb-grid:latest
docker push cr.yandex/crpfskvn79g5ht8njq0k/contextmachine-mfb-grid:latest
