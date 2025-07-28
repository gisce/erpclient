FROM ubuntu:18.04

# Install basic packages
RUN apt-get update && apt-get install -qqy \
  python-setuptools \
  python-pip \
  python-glade2 \
  python-gtk2 \
  libssl-dev \
  git \
  x11-apps \
  evince \
  gtk2-engines \
  iceweasel

# Install ERPClient
WORKDIR erpclient
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN easy_install egenix-mx-base
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install pyOpenSSL pycairo
RUN for lib in cairo gi glib gobject gtk-2.0 pygtk.pth pygtk.py; do \
        echo "Linking $lib..."; \
        ln -s /usr/lib/python2.7/dist-packages/$lib /usr/local/lib/python2.7/site-packages/$lib; \
    done

CMD python bin/openerp-client.py
