
# Generic DevContainer Dockerfile template
FROM python:3.14-trixie

# Install basic tools and dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash git libnss3-tools x11-apps jq \
    && rm -rf /var/lib/apt/lists/*

# Add custom certificates if needed
RUN mkdir -p /usr/local/share/ca-certificates/custom
COPY certs/* /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

RUN mkdir -p /root/.pki/nssdb
RUN certutil -d /root/.pki/nssdb -N --empty-password
RUN ls -l /usr/local/share/ca-certificates/custom/
RUN for cert in /usr/local/share/ca-certificates/custom/*; do \
        cert_name=$(basename "$cert"); \
        certutil -A -a -t "C,," -i "$cert" -d "/root/.pki/nssdb" -n "$cert_name"; \
    done
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Add custom scripts if needed
COPY scripts/* /usr/local/bin/ 
RUN find /usr/local/bin -type f -exec chmod 0775 {} ';'

# Workspace and bash history
RUN mkdir -p /workspace /commandhistory && touch /commandhistory/bash_history
COPY bashrc /tmp/bashrc
RUN cat /tmp/bashrc >> /root/.bashrc 2>/dev/null || true

# Ajout du sourcing automatique du venv dans le bashrc
RUN echo 'source /workspace/.venv/bin/activate' >> /root/.bashrc

# Installer les dépendances Python dans un venv local au workspace
RUN python3 -m venv /workspace/.venv \
    && /workspace/.venv/bin/pip install --upgrade pip

# Ajouter le venv au PATH pour tous les shells
ENV PATH="/workspace/.venv/bin:$PATH"

WORKDIR /workspace

CMD ["sleep", "inf"]
