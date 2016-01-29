#!/usr/bin/env python3
""" Write a config file for FluentD containing an out_forward block and run it

This script looks for environment variables for out_forward servers. If those
variables are not given, it should write the config as is for stdout.

Several servers can be provided like this:

FLUENTD_SERVER_1_NAME=server1
FLUENTD_SERVER_1_HOST=server1.example.com
FLUENTD_SERVER_1_PORT=23123
FLUENTD_SERVER_1_WEIGHT=70

FLUENTD_SERVER_2_NAME=server2
[...]

Or only a single server like this:

FLUENTD_SERVER_NAME=server
[...]

"""
import os
from string import Template
import sys


SOURCE_TEMPLATE_PATH = '/fluentd/etc/fluent.conf.TMPL'
TARGET_FILE_PATH = '/fluentd/etc/fluent.conf'

MATCH_BLOCK_TEMPLATE = """
  <match **>
    @type forward
    ${SERVER_BLOCK}
  </match>
"""

SERVER_BLOCK_TEMPLATE = """
    <server>
      name ${FLUENTD_SERVER_NAME}
      host ${FLUENTD_SERVER_HOST}
      port ${FLUENTD_SERVER_PORT}
      weight ${FLUENTD_SERVER_WEIGHT}
    </server>
"""


def get_vars_and_render_server_block():
    """ This function is supposed to render the blocks for all given servers

    It needs to work for a single and also for multiple servers. It needs to
    render a server block for each server. To distinguish servers, we use all
    keys ending with _HOST and use the preceding substring to look up variables
    for that server.

    """
    server_block = """"""
    fluentd_keys = [key for key in os.environ if key.startswith('FLUENTD_SERVER_')]
    if fluentd_keys:
        fluentd_conf_dict = {k: os.environ.get(k) for k in fluentd_keys}

        hosts = [host for host in fluentd_keys if host.endswith('_HOST')]
        # this might look like ['FLUENTD_SERVER', 'FLUENTD_SERVER_1', ...]
        server_prefixes = [host.split('_HOST')[0] for host in hosts]

        # render server block for all prefixes
        for server_prefix in server_prefixes:
            # when both FLUENTD_SERVER_HOST and FLUENTD_SERVER_1_HOST both are
            # set, this doesn't work correctly because key.startswith matches
            # both.
            # This shouldn't happen though, either single FLUENTD_SERVER_HOST
            # or mutliple servers with numbers should be set.
            single_server_conf_keys = [key for key in fluentd_keys if
                                       key.startswith(server_prefix)]
            single_server_conf_with_idx = {k: fluentd_conf_dict[k] for
                                           k in single_server_conf_keys}

            # we need to cut the '_1' etc. out of the dictionary keys to use it
            # for substitution. There may be also vars for one server without
            # an index number ('FLUENTD_SERVER_HOST')
            single_server_conf_dict = {}
            for key, value in single_server_conf_with_idx.items():
                # this will be 'FLUENTD_SERVER'
                parts = key.split('_')[:2]
                # this will be 'HOST' or 'NAME' ...
                postfix = key.split('_')[-1]
                parts.append(postfix)

                single_server_conf_dict["_".join(parts)] = value

            # port and weight have default values, they are not mandatory
            single_server_conf_dict.setdefault('FLUENTD_SERVER_PORT', '24224')
            single_server_conf_dict.setdefault('FLUENTD_SERVER_WEIGHT', '60')

            t = Template(SERVER_BLOCK_TEMPLATE)
            try:
                server_block += t.substitute(single_server_conf_dict)
            except KeyError as exc:
                sys.exit('Failure. Required variable missing for {}: '
                         '{}'.format(server_prefix, exc))

    return server_block


def get_fluentd_config_dict(server_block):
    """ If there is no server_block, use empty string. Else render block """
    if not server_block:
        return {"MATCH_OUT_FORWARD": ""}

    t = Template(MATCH_BLOCK_TEMPLATE)
    out_forward_block = t.substitute({'SERVER_BLOCK': server_block})
    return {"MATCH_OUT_FORWARD": out_forward_block}


def write_fluentd_conf_file(fluentd_config_dict):
    template_file = open(SOURCE_TEMPLATE_PATH)
    template = Template(template_file.read())
    fluentd_conf = template.substitute(fluentd_conf_dict)
    fluentd_conf_file = open(TARGET_FILE_PATH, 'w')
    fluentd_conf_file.write(fluentd_conf)


if __name__ == '__main__':
    server_block = get_vars_and_render_server_block()
    fluentd_conf_dict = get_fluentd_config_dict(server_block)
    write_fluentd_conf_file(fluentd_conf_dict)

    print('config file fluent.conf written. Starting server.')
    os.system('exec fluentd -c /fluentd/etc/$FLUENTD_CONF -p /fluentd/plugins '
              '$FLUENTD_OPT')
