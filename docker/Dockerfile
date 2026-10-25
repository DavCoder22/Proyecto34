FROM jupyter/scipy-notebook:python-3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

USER $NB_UID

RUN pip install --no-cache-dir \
    pandas \
    openpyxl \
    sqlalchemy \
    psycopg2-binary \
    chardet \
    matplotlib \
    seaborn \
    ipywidgets

WORKDIR /home/jovyan/work

EXPOSE 8888

CMD sh -c "start-notebook.sh --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token=$JUPYTER_TOKEN --NotebookApp.password=''"
