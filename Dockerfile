FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proxy.py selftest.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

VOLUME ["/config"]
ENTRYPOINT ["./entrypoint.sh"]
CMD ["serve"]
