#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.cli.command_template.command_template import CommandTemplate


SYSTEM_SOFTWARE = CommandTemplate("show system software")
SYSTEM_INFO = CommandTemplate("show sys-id")
SLOT_INFO = CommandTemplate("show slot-id {slot_id}")
GET_CONN = CommandTemplate("show con {slot_id} all")
