#!/usr/bin/python
# -*- coding: utf-8 -*-


from cloudshell.cli.command_template.command_template import CommandTemplate


SET_CONN = CommandTemplate("set con {slot_id} {connection}")
DEL_CONN = CommandTemplate("set term {slot_id} {connection}")
