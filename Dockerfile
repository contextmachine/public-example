#syntax=docker/dockerfile:1
FROM cr.yandex/crpfskvn79g5ht8njq0k/mmcore:amd64
WORKDIR /mmservice
COPY --link . .
COPY prod.env .env
ENV PYTHON="$MAMBA_ROOT_PREFIX/bin/python"
ENV PATH=$PATH:"$MAMBA_ROOT_PREFIX/bin/python"
RUN npm install three
RUN /usr/local/bin/_entrypoint.sh python -m pip install --upgrade -r req.txt --no-cache
CMD ["main.py"]

