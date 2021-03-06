FROM alpine:latest
MAINTAINER TAGOMORI Satoshi <tagomoris@gmail.com>
LABEL Description="Fluentd docker image" Vendor="Fluent Organization" Version="1.1"

# Do not split this into multiple RUN!
# Docker creates a layer for every RUN-Statement
# therefore an 'apk delete build*' has no effect
RUN apk --no-cache --update add \
                            build-base \
                            ca-certificates \
                            ruby \
                            ruby-irb \
                            ruby-dev \
                            python3 && \
    echo 'gem: --no-document' >> /etc/gemrc && \
    gem install fluentd -v 0.12.20 && \
    apk del build-base ruby-dev && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

RUN adduser -D -g '' -u 1000 -h /home/fluent fluent
RUN chown -R fluent:fluent /home/fluent

# for log storage (maybe shared with host)
RUN mkdir -p /fluentd/log
# configuration/plugins path (default: copied from .)
RUN mkdir -p /fluentd/etc /fluentd/plugins

RUN chown -R fluent:fluent /fluentd

USER fluent
WORKDIR /home/fluent

# Tell ruby to install packages as user
RUN echo "gem: --user-install --no-document" >> ~/.gemrc
ENV PATH /home/fluent/.gem/ruby/2.2.0/bin:$PATH
ENV GEM_PATH /home/fluent/.gem/ruby/2.2.0:$GEM_PATH

COPY fluent.conf.TMPL /fluentd/etc/
ONBUILD COPY fluent.conf.TMPL /fluentd/etc/
ONBUILD COPY plugins /fluentd/plugins/
ADD write_config_and_start_fluentd.py /home/fluent/write_config_and_start_fluentd.py

ENV FLUENTD_OPT=""
ENV FLUENTD_CONF="fluent.conf"

EXPOSE 24224

CMD exec ./write_config_and_start_fluentd.py
