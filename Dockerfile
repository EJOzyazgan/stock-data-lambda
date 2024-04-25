FROM 3.10-alpine

COPY requirements.txt .

RUN apt-get update && apt-get install -y wget bzip2 libxtst6 libgtk-3-0 libx11-xcb-dev libdbus-glib-1-2 libxt6 libpci-dev

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl firefox-esr

RUN pip3 install --no-cache-dir wheel
RUN pip3 install --no-cache-dir -r requirements.txt

RUN export HOME=/tmp