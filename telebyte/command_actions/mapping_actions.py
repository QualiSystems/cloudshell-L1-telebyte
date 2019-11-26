#!/usr/bin/python
# -*- coding: utf-8 -*-

import telebyte.command_templates.mapping as command_template
from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor


class MappingActions(object):
    def __init__(self, cli_service, logger):
        """ Mapping actions
        :param cli_service: default mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._cli_service = cli_service
        self._logger = logger

    def map_bidi(self, slot_id, src_port, dst_port):
        """ Unidirectional mapping
        :param src_port:
        :param dst_ports:
        :return:
        """

        try:
            connection = "{}:{}".format(dst_port, int(src_port))
        except:
            connection = "{}:{}".format(src_port, int(dst_port))

        executor = CommandTemplateExecutor(self._cli_service, command_template.SET_CONN)
        output = executor.execute_command(slot_id=slot_id, connection=connection)
        return output

    def map_clear(self, slot_id, port):
        """ Clear bidirectional mapping
        :param ports:
        :return:
        """

        # connection = " ".join(ports)

        executor = CommandTemplateExecutor(self._cli_service, command_template.DEL_CONN)
        output = executor.execute_command(slot_id=slot_id, connection=port)
        return output



"""
600-6SL:~$ set con 1 B:1

ACCEPTED  set con 1 b:1

600-6SL:~$ set con 2 b:1

ERROR  Module Not Found

600-6SL:~$ set con 1 b:2

ACCEPTED  set con 1 b:2

600-6SL:~$ set con 1 b:3

ERROR  Invalid Input Channel

600-6SL:~$ set con 1 r:1

ERROR  Invalid Output

600-6SL:~$ set con 1 b:0

ERROR  Invalid Input Channel







600-6SL:~$ set term 1 b

ACCEPTED  set term 1 b

600-6SL:~$ set term 1 1

ERROR  Invalid Output

600-6SL:~$ set term 1 t

ERROR  Invalid Output

600-6SL:~$ set term 1 b

ACCEPTED  set term 1 b




"""