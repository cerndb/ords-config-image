#  Copyright 2020 CERN
# This software is distributed under the terms of the GNU General Public Licence
# version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying
# this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself
# to any jurisdiction.

FROM gitlab-registry.cern.ch/jeedy/jdk-images/jdk11-11.0.6_10:1.9

ARG TARGET_IMAGE_TAG
ENV TARGET_IMAGE_TAG=${TARGET_IMAGE_TAG}

LABEL maintainers.1="Jakub Granieczny <jakub.granieczny@cern.ch>"
WORKDIR /work-dir
COPY repos/* /etc/yum.repos.d/
COPY  config/ai.conf  /etc/ai/ai.conf

RUN yum install -y dnf  \
    && dnf install -y 'dnf-command(config-manager)' \
    && yum clean all \
    && rm -rf /var/cache/yum 


RUN \
dnf config-manager --enable cernonly \
&& dnf install -y --setopt=skip_missing_names_on_install=False  python2-cryptography \
                    python36 \
                    python36-jinja2 \
                    python36-prettytable \
                    python36-pyOpenSSL \
                    python3-cx_Oracle \
                    zip \
                    ai-tools \
                    oracle-instantclient19.3-sqlplus \
&& yum clean all \
&& ln -sf /usr/bin/python3 /usr/bin/python \
&& rm -rf /var/cache/yum \
&& mkdir -p /etc/ai /work-dir 

COPY scripts /work-dir/scripts/
COPY user-documentation /work-dir/
COPY dadEdit /work-dir/dadEdit


ENTRYPOINT ["/work-dir/scripts/entrypoint.sh"]