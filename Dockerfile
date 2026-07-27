FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS build

WORKDIR /src
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY aigis ./aigis
RUN pip install --no-cache-dir --upgrade 'pip==26.1.1' 'build==1.5.0' \
    && python -m build --wheel --outdir /wheels

FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS runtime

LABEL org.opencontainers.image.title="Aigis"
LABEL org.opencontainers.image.description="Zero-dependency Python firewall for AI agents — 4-wall + L4-L7 defense, 7-paper coverage, 44 compliance templates."
LABEL org.opencontainers.image.source="https://github.com/killertcell428/aigis"
LABEL org.opencontainers.image.licenses="Apache-2.0"

RUN groupadd --system aigis && useradd --system --gid aigis --create-home aigis

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

USER aigis
WORKDIR /home/aigis

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2).status==200 else 1)"

ENTRYPOINT ["aigis"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
