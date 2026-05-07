FROM python:3.14-slim@sha256:5b3879b6f3cb77e712644d50262d05a7c146b7312d784a18eff7ff5462e77033 AS build

WORKDIR /src
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY aigis ./aigis
RUN pip install --no-cache-dir --upgrade pip build \
    && python -m build --wheel --outdir /wheels

FROM python:3.14-slim@sha256:5b3879b6f3cb77e712644d50262d05a7c146b7312d784a18eff7ff5462e77033 AS runtime

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
