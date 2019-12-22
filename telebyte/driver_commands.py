#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface
from cloudshell.layer_one.core.response.response_info import ResourceDescriptionResponseInfo, GetStateIdResponseInfo, \
    AttributeValueResponseInfo
from cloudshell.layer_one.core.response.resource_info.entities.blade import Blade
from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
from cloudshell.layer_one.core.response.resource_info.entities.port import Port

from telebyte.command_actions.autoload_actions import AutoloadActions
from telebyte.command_actions.mapping_actions import MappingActions
from telebyte.cli.telebyte_cli_handler import TelebyteCliHandler
# from telebyte.exceptions.telebyte_exceptions import InvalidSlotNumberException, InvalidConnectionException


class DriverCommands(DriverCommandsInterface):
    """ Driver commands implementation """
    PORT_ADD = 64
    SLOT_COUNT = 6

    def __init__(self, logger, runtime_config):
        """
        :type logger: logging.Logger
        :type runtime_config: cloudshell.layer_one.core.helper.runtime_configuration.RuntimeConfiguration
        """

        self._logger = logger
        self._runtime_config = runtime_config
        self._cli_handler = TelebyteCliHandler(logger)
        self._max_slot_count = runtime_config.read_key("DRIVER.SLOT_COUNT", self.SLOT_COUNT)

    def address_parser(self, address):
        """  """

        match = re.search(r"(?P<address>.*):(?P<blade>\d):(?P<port_1>\w):(?P<port_2>\w)", address)
        if match:
            return match.groupdict()
        else:
            raise Exception("Wrong address format."
                            "Address should be in format <address>:<blade_number>:<literal_port_1>:<literal_port_2>")

    def login(self, address, username, password):
        """
        Perform login operation on the device
        :param address: resource address, "192.168.42.240"
        :param username: username to login on the device
        :param password: password
        :return: None
        :raises Exception: if command failed
        Example:
            # Define session attributes
            self._cli_handler.define_session_attributes(address, username, password)

            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Executing simple command
                device_info = session.send_command("show version")
                self._logger.info(device_info)
        """

        address = self.address_parser(address).get("address")
        self._cli_handler.define_session_attributes(address, username, password)
        with self._cli_handler.default_mode_service() as session:
            actions = AutoloadActions(session, self._logger)
            self._logger.info("Model: {}, Serial: {}".format(*actions.get_device_info()))

    def get_resource_description(self, address):
        """ Auto-load function to retrieve all information from the device
        :param address: resource address, "192.168.42.240"
        :type address: str
        :return: resource description
        :rtype: cloudshell.layer_one.core.response.response_info.ResourceDescriptionResponseInfo
        :raises cloudshell.layer_one.core.layer_one_driver_exception.LayerOneDriverException: Layer one exception.

        Example:

            from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
            from cloudshell.layer_one.core.response.resource_info.entities.blade import Blade
            from cloudshell.layer_one.core.response.resource_info.entities.port import Port

            chassis_resource_id = chassis_info.get_id()
            chassis_address = chassis_info.get_address()
            chassis_model_name = "Telebyte Chassis"
            chassis_serial_number = chassis_info.get_serial_number()
            chassis = Chassis(resource_id, address, model_name, serial_number)

            blade_resource_id = blade_info.get_id()
            blade_model_name = "Generic L1 Module"
            blade_serial_number = blade_info.get_serial_number()
            blade.set_parent_resource(chassis)

            port_id = port_info.get_id()
            port_serial_number = port_info.get_serial_number()
            port = Port(port_id, "Generic L1 Port", port_serial_number)
            port.set_parent_resource(blade)

            return ResourceDescriptionResponseInfo([chassis])
        """

        address_data = self.address_parser(address)

        address = address_data.get("address")
        slot_id = address_data.get("blade")
        port_name_1 = address_data.get("port_1")
        port_name_2 = address_data.get("port_2")

        with self._cli_handler.default_mode_service() as session:
            autoload_actions = AutoloadActions(session, self._logger)

            dev_model, serial_number = autoload_actions.get_device_info()

            chassis = Chassis("", address, "Telebyte Chassis", serial_number)
            chassis.set_model_name(dev_model)
            chassis.set_os_version(autoload_actions.get_device_software())
            chassis.set_serial_number(serial_number)

            slot_info = autoload_actions.get_slot_info(slot_id=slot_id)
            self._logger.debug("SLOT INFO: {}".format(slot_info))

            if slot_info:
                real_blade = Blade(port_name_1, "Generic L1 Module", slot_info.get("Serial", ""))
                real_blade.set_model_name(slot_info.get("Model", ""))
                real_blade.set_parent_resource(chassis)

                for port_name in [port_name_1, port_name_2]:
                    self._logger.debug("Port ID : {}".format(port_name))

                    blade = Blade(port_name, "Generic L1 Module", "")
                    blade.set_parent_resource(real_blade)

                    for i in [1, 2]:
                        port_id = "{}{}".format(port_name, i)
                        port_serial = "{dev_serial}.{port_id}".format(dev_serial=slot_info.get("Serial", ""),
                                                                      port_id=port_id)
                        port = Port(port_id, "Generic L1 Port", port_serial)
                        port.set_parent_resource(blade)

            # slot_id = 0
            # while slot_id <= self._max_slot_count:
            #     try:
            #         slot_id += 1
            #         slot_info = autoload_actions.get_slot_info(slot_id=slot_id)
            #         self._logger.debug("SLOT INFO: {}".format(slot_info))
            #
            #         if slot_info:
            #             blade = Blade(slot_id, "Generic L1 Module", slot_info.get("Serial", ""))
            #             blade.set_model_name(slot_info.get("Model", ""))
            #             blade.set_parent_resource(chassis)
            #
            #             ports = {}
            #             out_ports, in_ports = autoload_actions.get_in_out_ports(slot_info=slot_info)
            #             self._logger.debug("OUT PORTS: {}, IN PORTS: {}".format(out_ports, in_ports))
            #             if out_ports is None:
            #                 raise Exception("Can not determine out port count")
            #
            #             for i in range(1, out_ports + 1):
            #                 port_id = chr(i + self.PORT_ADD)
            #                 port_serial = "{dev_serial}.{port_id}".format(dev_serial=slot_info.get("Serial", ""),
            #                                                               port_id=port_id)
            #                 self._logger.debug("Port ID : {}".format(port_id))
            #
            #                 port = Port(port_id, "Generic L1 Port", port_serial)
            #                 port.set_parent_resource(blade)
            #                 ports[port_id] = port
            #
            #             for i in range(1, in_ports + 1):
            #                 port_id = i
            #
            #                 port_serial = "{dev_serial}.{port_id}".format(dev_serial=slot_info.get("Serial", ""),
            #                                                               port_id=port_id)
            #                 self._logger.debug("Port ID : {}".format(port_id))
            #
            #                 port = Port(port_id, "Generic L1 Port", port_serial)
            #                 port.set_parent_resource(blade)
            #                 ports[port_id] = port
            #
            #             conn_info = autoload_actions.get_slot_connections(slot_id=slot_id)
            #             self._logger.debug("SLOT CONNECTIONS: {}".format(conn_info))
            #
            #             for out_port_id, in_port_id in conn_info.items():
            #                 if in_port_id == 0: #  means no connection
            #                     continue
            #
            #                 out_port = ports.get(out_port_id)
            #                 in_port = ports.get(in_port_id)
            #                 out_port.add_mapping(in_port)
            #                 in_port.add_mapping(out_port)
            #
            #     except InvalidSlotNumberException:
            #         # self._max_slot_count = min(slot_id, self._max_slot_count)
            #         break

        return ResourceDescriptionResponseInfo([chassis])

    def map_uni(self, src_port, dst_ports):
        """ Unidirectional mapping of two ports
        :param src_port: src port address, "192.168.42.240/1/A/A1"
        :type src_port: str
        :param dst_ports: list of dst ports addresses, ["192.168.42.240/1/A/A2", "192.168.42.240/1/B/B2"]
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed
        """

        raise Exception("Unidirectional connection does not supported")

    def map_bidi(self, src_port, dst_port):
        """ Create a bidirectional connection between source and destination ports
        :param src_port: src port address, "192.168.42.240/1/A/A1"
        :type src_port: str
        :param dst_port: dst port address, "192.168.42.240/1/B/B2"
        :type dst_port: str
        :return: None
        :raises Exception: if command failed
        """

        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session, self._logger)

            for port in [src_port, dst_port]:
                _, blade, port_aggr, port_id = port.split("/")

                match = re.search(r"\w+(?P<port_id>\d+)", port_id)
                if match:
                    port_id = match.groupdict()["port_id"]
                else:
                    raise Exception("Wrong port name structure provided")

                mapping_actions.map_bidi(slot_id=blade, src_port=port_id, dst_port=port_aggr)

            # _, src_blade, src_port_aggr, src = src_port.split("/")
            # _, dst_blade, dst_port_aggr, dst = dst_port.split("/")
            #
            # if src_blade != dst_blade:
            #     raise InvalidConnectionException("Connections can be created inside one blade only")
            #
            # mapping_actions.map_bidi(slot_id=src_blade, src_port=src, dst_port=dst)

    def map_clear_to(self, src_port, dst_ports):
        """ Remove simplex/multi-cast/duplex connection ending on the destination port
        :param src_port: src port address, "192.168.42.240/1/21"
        :type src_port: str
        :param dst_ports: list of dst ports addresses, ["192.168.42.240/1/21", "192.168.42.240/1/22"]
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed
        """

        self._logger.debug("SRC: {}, DST: {}".format(src_port, dst_ports))

        ports_list = [src_port]
        ports_list.extend(dst_ports)

        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session, self._logger)
            for port in ports_list:
                _, blade_id, port_aggr, _ = port.split("/")

                mapping_actions.map_clear(slot_id=blade_id, port=port_aggr)

        # _, blade_id, src = src_port.split("/")
        #
        # try:
        #     src = int(src)
        #     self._logger.debug("Port identifier should be literal not numeric. Got: {}".format(src_port))
        # except ValueError:
        #     with self._cli_handler.default_mode_service() as session:
        #         mapping_actions = MappingActions(session, self._logger)
        #         mapping_actions.map_clear(slot_id=blade_id, port=src)

        # raise Exception("Unidirectional connection does not supported")

    def map_clear(self, ports):
        """
        Remove simplex/multi-cast/duplex connection ending on the destination port
        :param ports: ports, ["192.168.42.240/1/21", "192.168.42.240/1/22"]
        :type ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            exceptions = []
            with self._cli_handler.config_mode_service() as session:
                for port in ports:
                    try:
                        session.send_command("map clear {}".format(convert_port(port)))
                    except Exception as e:
                        exceptions.append(str(e))
                if exceptions:
                    raise Exception("self.__class__.__name__", ",".join(exceptions))
        """

        with self._cli_handler.default_mode_service() as session:
            mapping_actions = MappingActions(session, self._logger)
            for port in ports:

                _, blade_id, src, _ = port.split("/")
                # _, blade_id, src = port.split("/")

                mapping_actions.map_clear(slot_id=blade_id, port=src)

    def map_tap(self, src_port, dst_ports):
        """
        Add TAP connection
        :param src_port: port to monitor "192.168.42.240/1/21"
        :type src_port: str
        :param dst_ports: ["192.168.42.240/1/22", "192.168.42.240/1/23"]
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            return self.map_uni(src_port, dst_ports)
        """
        raise NotImplementedError

    def set_speed_manual(self, src_port, dst_port, speed, duplex):
        """
        Set connection speed. It is not used with new standard
        :param src_port:
        :param dst_port:
        :param speed:
        :param duplex:
        :return:
        """
        raise NotImplementedError

    def get_attribute_value(self, cs_address, attribute_name):
        """
        Retrieve attribute value from the device
        :param cs_address: address, "192.168.42.240/1/21"
        :type cs_address: str
        :param attribute_name: attribute name, "Port Speed"
        :type attribute_name: str
        :return: attribute value
        :rtype: cloudshell.layer_one.core.response.response_info.AttributeValueResponseInfo
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.get_attribute_command(cs_address, attribute_name)
                value = session.send_command(command)
                return AttributeValueResponseInfo(value)
        """
        raise NotImplementedError

    def set_attribute_value(self, cs_address, attribute_name, attribute_value):
        """
        Set attribute value to the device
        :param cs_address: address, "192.168.42.240/1/21"
        :type cs_address: str
        :param attribute_name: attribute name, "Port Speed"
        :type attribute_name: str
        :param attribute_value: value, "10000"
        :type attribute_value: str
        :return: attribute value
        :rtype: cloudshell.layer_one.core.response.response_info.AttributeValueResponseInfo
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.set_attribute_command(cs_address, attribute_name, attribute_value)
                session.send_command(command)
                return AttributeValueResponseInfo(attribute_value)
        """
        raise NotImplementedError

    def get_state_id(self):
        """
        Check if CS synchronized with the device.
        :return: Synchronization ID, GetStateIdResponseInfo(-1) if not used
        :rtype: cloudshell.layer_one.core.response.response_info.GetStateIdResponseInfo
        :raises Exception: if command failed

        Example:
            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Execute command
                chassis_name = session.send_command("show chassis name")
                return chassis_name
        """

        self._logger.info("Command 'get state id' called")
        return GetStateIdResponseInfo("-1")

    def set_state_id(self, state_id):
        """
        Set synchronization state id to the device, called after Autoload or SyncFomDevice commands
        :param state_id: synchronization ID
        :type state_id: str
        :return: None
        :raises Exception: if command failed

        Example:
            # Obtain cli session
            with self._cli_handler.config_mode_service() as session:
                # Execute command
                session.send_command("set chassis name {}".format(state_id))
        """

        self._logger.info("set_state_id {}".format(state_id))
        # raise NotImplementedError
