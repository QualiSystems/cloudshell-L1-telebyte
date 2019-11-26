#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

import telebyte.command_templates.autoload as command_template

from telebyte.exceptions.telebyte_exceptions import InvalidSlotNumberException
from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor


class AutoloadActions(object):
    """
    Autoload actions
    """

    def __init__(self, cli_service, logger):
        """
        :param cli_service: default mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._cli_service = cli_service
        self._logger = logger

    def get_device_software(self):
        """ Determain device software

        ACCEPTED  show system software

        "software" Mux-2.6.0.1
        """

        output = CommandTemplateExecutor(self._cli_service, command_template.SYSTEM_SOFTWARE).execute_command()

        if "ACCEPTED" in output.upper():
            match = re.search(r"\"software\"\s*(?P<soft>.*)", output, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.groupdict()["soft"]

        return ""

    def get_device_info(self):
        """ Determain device information like Serial Number, OS Version etc

        ACCEPTED SUCCESSFULLY

        System P/N: 600-6SL
        System Rev: A
        System S/N: TB8216
        Carrier P/N: 0519-0727
        Carrier Rev: C
        Carrier S/N: SUB1453
        SBC P/N: TS4200
        SBC Rev: E
        SBC S/N: 4EFF30
        """

        model, serial = "", ""

        output = CommandTemplateExecutor(self._cli_service, command_template.SYSTEM_INFO).execute_command()

        if "ACCEPTED" in output.upper():
            match_model = re.search(r"System P/N:\s*(?P<model>.*)", output, re.IGNORECASE | re.MULTILINE)
            if match_model:
                model = match_model.groupdict()["model"]

            match_serial = re.search(r"System S/N:\s*(?P<serial>.*)", output, re.IGNORECASE | re.MULTILINE)
            if match_serial:
                serial = match_serial.groupdict()["serial"]

        return model, serial


    def get_slot_info(self, slot_id):
        """ Determine blade information Serial Number, Model Name etc

        ACCEPTED  show slot-id 1

        Slot: 1
          PN: 600-SM-16-1-2
          Rev: A.1
          SN: TB8129

        """

        output = CommandTemplateExecutor(self._cli_service, command_template.SLOT_INFO).execute_command(slot_id=slot_id)

        if "ACCEPTED" in output.upper():
            match = re.search(r"PN:\s*(?P<model>.*).*?Rev:\s*(?P<rev>.*).*?SN:\s*(?P<serial>.*)",
                              output,
                              re.IGNORECASE | re.DOTALL)
            self._logger.debug("Slot {} detailed info: {}".format(slot_id, output))
            if match:
                slot_info = {"Serial": match.groupdict()["serial"].strip(),
                             "Revision": match.groupdict()["rev"].strip(),
                             "Model": match.groupdict()["model"].strip()}
            else:
                slot_info = {}
        elif "ERROR" in output.upper():
            """ ERROR  Module Not Found
                ERROR  Data is not available
                ERROR  Invalid Slot Number """
            if "Invalid Slot Number" in output:
                raise InvalidSlotNumberException("Invalid Slot Number")
            else:
                slot_info = {}
        else:
            raise Exception()

        return slot_info

    def get_in_out_ports(self, slot_info):
        """ Get count of out and in ports """

        slot_model = slot_info.get("Model")
        if slot_model:
            match = re.search(r"(?P<out_ports>\d+)-\d+-(?P<in_ports>\d+)", slot_model)
            if match:
                return int(match.groupdict().get("out_ports")), int(match.groupdict().get("in_ports"))

        return None, None

    def get_slot_connections(self, slot_id):
        """ Determine port connections for the provided slot ID

            ACCEPTED  show con 1 all

            Slot: 1
            A:1;
            B:0;
            C:1;
            D:2;

        """

        output = CommandTemplateExecutor(self._cli_service, command_template.GET_CONN).execute_command(slot_id=slot_id)

        if "ACCEPTED" in output.upper():
            match = re.finditer(r"(?P<out_port>\w+):(?P<in_port>\d+);", output, re.IGNORECASE | re.MULTILINE)
            self._logger.debug("Slot {} connections info: {}".format(slot_id, output))
            if match:
                conn = {item.groupdict().get("out_port"): int(item.groupdict().get("in_port")) for item in match}
            else:
                conn = {}
        elif "ERROR" in output.upper():
            """ ERROR  Module Not Found
                ERROR  Data is not available
                ERROR  Invalid Slot Number """
            if "Invalid Slot Number" in output:
                raise InvalidSlotNumberException("Invalid Slot Number")
            else:
                conn = {}
        else:
            raise Exception()

        return conn


    """
    600-6SL:~$ show system software

ACCEPTED  show system software

"software" Mux-2.6.0.1


======
600-6SL:~$ show sys-id

ACCEPTED SUCCESSFULLY

System P/N: 600-6SL
System Rev: A
System S/N: TB8216
Carrier P/N: 0519-0727
Carrier Rev: C
Carrier S/N: SUB1453
SBC P/N: TS4200
SBC Rev: E
SBC S/N: 4EFF30

=======
600-6SL:~$ show con 1 all

ACCEPTED  show con 1 all

Slot: 1
A:1;
B:0;
C:1;
D:2;
E:0;
F:0;
G:0;
H:0;
I:0;
J:0;
K:0;
L:0;
M:0;
N:0;
O:0;
P:0;

600-6SL:~$
600-6SL:~$ show con 2 all

ERROR  Module Not Found

600-6SL:~$ show con 3 all

ERROR  Data is not available

600-6SL:~$ show con 4 all

ERROR  Module Not Found

600-6SL:~$ show con 5 all

ERROR  Data is not available

600-6SL:~$ show con 6 all

ERROR  Module Not Found

600-6SL:~$ show con 7 all

ERROR  Invalid Slot Number

    """
