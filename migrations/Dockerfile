FROM docker.io/flyway/flyway:11.13

RUN groupadd --system --gid 500 app \
  && useradd --system --uid 500 --gid app --no-create-home app

USER 500

COPY sql /flyway/sql
COPY flyway.toml /flyway/conf

CMD [ "migrate", "-skipCheckForUpdate" ]
