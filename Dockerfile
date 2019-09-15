FROM python:3.7.4

COPY requirements.txt /app/requirements.txt
COPY setup.py /app/setup.py
COPY logsql /app/logsql

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN cd /app && pip install -e .

WORKDIR /app
CMD ["python3", "-m", "logsql"]
