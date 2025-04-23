# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

import argparse
from awscrt import io
from uuid import uuid4

class CommandLineUtils:
    def __init__(self, description) -> None:
        self.parser = argparse.ArgumentParser(description="Send and receive messages through and MQTT connection.")
        self.commands = {}
        self.parsed_commands = None

    def register_command(self, command_name, example_input, help_output, required=False, type=None, default=None, choices=None, action=None):
        self.commands[command_name] = {
            "name":command_name,
            "example_input":example_input,
            "help_output":help_output,
            "required": required,
            "type": type,
            "default": default,
            "choices": choices,
            "action": action
        }

    def remove_command(self, command_name):
        if command_name in self.commands.keys():
            self.commands.pop(command_name)

    """
    Returns the command if it exists and has been passed to the console, otherwise it will print the help for the sample and exit the application.
    """
    def get_command_required(self, command_name, command_name_alt = None):
        if(command_name_alt != None):
            if hasattr(self.parsed_commands, command_name_alt):
                if(getattr(self.parsed_commands, command_name_alt) != None):
                    return getattr(self.parsed_commands, command_name_alt)

        if hasattr(self.parsed_commands, command_name):
            if(getattr(self.parsed_commands, command_name) != None):
                return getattr(self.parsed_commands, command_name)

        self.parser.print_help()
        print("Command --" + command_name + " required.")
        exit()

    """
    Returns the command if it exists, has been passed to the console, and is not None. Otherwise it returns whatever is passed as the default.
    """
    def get_command(self, command_name, default=None):
        if hasattr(self.parsed_commands, command_name):
            result = getattr(self.parsed_commands, command_name)
            if (result != None):
                return result
        return default

    def get_args(self):
        # if we have already parsed, then return the cached parsed commands
        if self.parsed_commands is not None:
            return self.parsed_commands

        # add all the commands
        for command in self.commands.values():
            if not command["action"] is None:
                self.parser.add_argument("--" + command["name"], action=command["action"], help=command["help_output"],
                    required=command["required"], default=command["default"])
            else:
                self.parser.add_argument("--" + command["name"], metavar=command["example_input"], help=command["help_output"],
                    required=command["required"], type=command["type"], default=command["default"], choices=command["choices"])

        self.parsed_commands = self.parser.parse_args()
        # Automatically start logging if it is set
        if self.parsed_commands.verbosity:
            io.init_logging(getattr(io.LogLevel, self.parsed_commands.verbosity), 'stderr')

        return self.parsed_commands

    def update_command(self, command_name, new_example_input=None, new_help_output=None, new_required=None, new_type=None, new_default=None, new_action=None):
        if command_name in self.commands.keys():
            if new_example_input:
                self.commands[command_name]["example_input"] = new_example_input
            if new_help_output:
                self.commands[command_name]["help_output"] = new_help_output
            if new_required:
                self.commands[command_name]["required"] = new_required
            if new_type:
                self.commands[command_name]["type"] = new_type
            if new_default:
                self.commands[command_name]["default"] = new_default
            if new_action:
                self.commands[command_name]["action"] = new_action

    def add_common_mqtt_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_endpoint,
            "<str>",
            "The endpoint of the mqtt server not including a port.",
            True,
            str)
        self.register_command(
            CommandLineUtils.m_cmd_ca_file,
            "<path>",
            "Path to AmazonRootCA1.pem (optional, system trust store used by default)",
            False,
            str)
        self.register_command(
            CommandLineUtils.m_cmd_is_ci,
            "<str>",
            "If present the sample will run in CI mode (optional, default='None')",
            False,
            str)

    def add_common_mqtt5_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_endpoint,
            "<str>",
            "The endpoint of the mqtt server not including a port.",
            True,
            str)
        self.register_command(
            CommandLineUtils.m_cmd_ca_file,
            "<path>",
            "Path to AmazonRootCA1.pem (optional, system trust store used by default)",
            False,
            str)
        self.register_command(
            CommandLineUtils.m_cmd_is_ci,
            "<str>",
            "If present the sample will run in CI mode (optional, default='None')",
            False,
            str)

    def add_common_proxy_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_proxy_host,
            "<str>",
            "Host name of the proxy server to connect through (optional)",
            False,
            str)
        self.register_command(
            CommandLineUtils.m_cmd_proxy_port,
            "<int>",
            "Port of the http proxy to use (optional, default='8080')",
            type=int,
            default=8080)

    def add_common_topic_message_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_topic,
            "<str>",
            "Topic to publish, subscribe to (optional, default='test/topic').",
            default="test/topic")
        self.register_command(
            CommandLineUtils.m_cmd_message,
            "<str>",
            "The message to send in the payload (optional, default='Hello World!').",
            default="Hello World! ")

    def add_common_logging_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_verbosity,
            "<Log Level>",
            "Logging level.",
            default=io.LogLevel.NoLogs.name,
            choices=[
                x.name for x in io.LogLevel])

    def add_cse546_commands(self):
        self.register_command(CommandLineUtils.m_cmd_response_q_url, "<path>", "Reponse queue URL.", True, str)
        self.register_command(CommandLineUtils.m_cmd_image_folder, "<path>", "Path to your test image dataset.", True, str)
        self.register_command(CommandLineUtils.m_cmd_prediction_file, "<path>", "Path to your ground truth prediction file.", True, str)

    def add_common_key_cert_commands(self):
        self.register_command(CommandLineUtils.m_cmd_key_file, "<path>", "Path to your key in PEM format.", True, str)
        self.register_command(CommandLineUtils.m_cmd_cert_file, "<path>", "Path to your client certificate in PEM format.", True, str)

    def add_common_custom_authorizer_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_custom_auth_username,
            "<str>",
            "The name to send when connecting through the custom authorizer (optional)")
        self.register_command(
            CommandLineUtils.m_cmd_custom_auth_authorizer_name,
            "<str>",
            "The name of the custom authorizer to connect to (optional but required for everything but custom domains)")
        self.register_command(
            CommandLineUtils.m_cmd_custom_auth_authorizer_signature,
            "<str>",
            "The signature to send when connecting through a custom authorizer (optional)")
        self.register_command(
            CommandLineUtils.m_cmd_custom_auth_password,
            "<str>",
            "The password to send when connecting through a custom authorizer (optional)")
        self.register_command(
            CommandLineUtils.m_cmd_custom_auth_token_key_name,
            "<str>",
            "Key used to extract the custom authorizer token (optional)")
        self.register_command(
            CommandLineUtils.m_cmd_custom_auth_token_value,
            "<str>",
            "The opaque token value for the custom authorizer (optional)")

    def add_common_x509_commands(self):
        self.register_command(
            CommandLineUtils.m_cmd_x509_endpoint,
            "<str>",
            "The credentials endpoint to fetch x509 credentials from",
        )
        self.register_command(
            CommandLineUtils.m_cmd_x509_thing_name,
            "<str>",
            "Thing name to fetch x509 credentials on behalf of"
        )
        self.register_command(
            CommandLineUtils.m_cmd_x509_role_alias,
            "<str>",
            "Role alias to use with the x509 credentials provider"
        )
        self.register_command(
            CommandLineUtils.m_cmd_x509_key,
            "<path>",
            "Path to the IoT thing private key used in fetching x509 credentials"
        )
        self.register_command(
            CommandLineUtils.m_cmd_x509_cert,
            "<path>",
            "Path to the IoT thing certificate used in fetching x509 credentials"
        )

        self.register_command(
            CommandLineUtils.m_cmd_x509_ca,
            "<path>",
            "Path to the root certificate used in fetching x509 credentials"
        )

    ########################################################################
    # cmdData utils/functions
    ########################################################################

    class CmdData:
        # General use
        input_endpoint : str
        input_cert : str
        input_key : str
        input_ca : str
        input_clientId : str
        input_port : int
        input_is_ci : bool
        input_use_websockets : bool
        # Proxy
        input_proxy_host : str
        input_proxy_port : int
        # PubSub
        input_topic : str
        input_message : str
        input_count : int
        # Websockets
        input_signing_region : str
        # Cognito
        input_cognito_identity : str
        # Custom auth
        input_custom_auth_username : str
        input_custom_authorizer_name : str
        input_custom_authorizer_signature : str
        input_custom_auth_password : str
        input_custom_authorizer_token_key_name : str
        input_custom_authorizer_token_value : str
        # Fleet provisioning
        input_template_name : str
        input_template_parameters : str
        input_csr_path : str
        # Services (Shadow, Jobs, Greengrass, etc)
        input_thing_name : str
        input_mode : str
        # Shared Subscription
        input_group_identifier : str
        # PKCS#11
        input_pkcs11_lib_path : str
        input_pkcs11_user_pin : str
        input_pkcs11_token_label : str
        input_pkcs11_slot_id : int
        input_pkcs11_key_label : str
        # X509
        input_x509_endpoint : str
        input_x509_role : str
        input_x509_thing_name : str
        input_x509_cert : str
        input_x509_key : str
        input_x509_ca : str
        # Basic discovery
        input_max_pub_ops : int
        input_print_discovery_resp_only : bool
        # Jobs
        input_job_time : int
        # Shadow
        input_shadow_property : str
        input_shadow_value : str
        input_shadow_name : str
        # PKCS12
        input_pkcs12_file : str
        input_pkcs12_password : str
        # Static credentials
        input_session_token : str
        input_access_key_id : str
        input_secret_access_key : str

        #CSE546
        input_response_queue_url: str
        input_image_fodler: str
        input_prediction_file: str

        def __init__(self) -> None:
            pass

        def parse_input_topic(self, cmdUtils):
            self.input_topic = cmdUtils.get_command(CommandLineUtils.m_cmd_topic, "test/topic")
            if (cmdUtils.get_command(CommandLineUtils.m_cmd_is_ci) != None):
                self.input_topic += "/" + str(uuid4())

    def parse_sample_input_basic_discovery():
        allowed_actions = ['both', 'publish', 'subscribe']

        cmdUtils = CommandLineUtils("Basic Discovery - Greengrass discovery example.")
        cmdUtils.add_cse546_commands()
        cmdUtils.add_common_mqtt_commands()
        cmdUtils.add_common_topic_message_commands()
        cmdUtils.add_common_logging_commands()
        cmdUtils.add_common_key_cert_commands()
        cmdUtils.remove_command(CommandLineUtils.m_cmd_endpoint)
        cmdUtils.register_command(CommandLineUtils.m_cmd_thing_name, "<str>", "The name assigned to your IoT Thing", required=True)
        cmdUtils.register_command(
            CommandLineUtils.m_cmd_mode, "<mode>",
            f"The operation mode (optional, default='both').\nModes:{allowed_actions}", default='both')
        cmdUtils.register_command(CommandLineUtils.m_cmd_region, "<str>", "The region to connect through.", required=True)
        cmdUtils.register_command(
            CommandLineUtils.m_cmd_max_pub_ops, "<int>",
            "The maximum number of publish operations (optional, default='10').",
            default=10, type=int)
        cmdUtils.register_command(
            CommandLineUtils.m_cmd_print_discovery_resp_only, "", "(optional, default='False').",
            default=False, type=bool, action="store_true")
        cmdUtils.add_common_proxy_commands()
        cmdUtils.get_args()

        cmdData = CommandLineUtils.CmdData()
        cmdData.parse_input_topic(cmdUtils)

        cmdData.input_response_queue_url = cmdUtils.get_command_required(CommandLineUtils.m_cmd_response_q_url)
        cmdData.input_image_folder       = cmdUtils.get_command_required(CommandLineUtils.m_cmd_image_folder)
        cmdData.input_prediction_file    = cmdUtils.get_command_required(CommandLineUtils.m_cmd_prediction_file)

        cmdData.input_message   = cmdUtils.get_command(CommandLineUtils.m_cmd_message, "Hello World! ")
        cmdData.input_cert      = cmdUtils.get_command_required(CommandLineUtils.m_cmd_cert_file)
        cmdData.input_key       = cmdUtils.get_command_required(CommandLineUtils.m_cmd_key_file)
        cmdData.input_ca        = cmdUtils.get_command(CommandLineUtils.m_cmd_ca_file, None)
        cmdData.input_thing_name    = cmdUtils.get_command_required(CommandLineUtils.m_cmd_thing_name)
        cmdData.input_mode      = cmdUtils.get_command(CommandLineUtils.m_cmd_mode, "both")
        cmdData.input_signing_region = cmdUtils.get_command_required(CommandLineUtils.m_cmd_region, CommandLineUtils.m_cmd_signing_region)
        #cmdData.input_max_pub_ops = int(cmdUtils.get_command(CommandLineUtils.m_cmd_max_pub_ops, 10))
        cmdData.input_max_pub_ops   = int(cmdUtils.get_command(CommandLineUtils.m_cmd_max_pub_ops, 1))
        cmdData.input_print_discovery_resp_only = bool(cmdUtils.get_command(CommandLineUtils.m_cmd_print_discovery_resp_only, False))
        cmdData.input_proxy_host    = cmdUtils.get_command(CommandLineUtils.m_cmd_proxy_host)
        cmdData.input_proxy_port    = int(cmdUtils.get_command(CommandLineUtils.m_cmd_proxy_port))
        cmdData.input_is_ci         = cmdUtils.get_command(CommandLineUtils.m_cmd_is_ci, None) != None
        return cmdData

    # Constants for commonly used/needed commands
    m_cmd_endpoint = "endpoint"
    m_cmd_ca_file = "ca_file"
    m_cmd_cert_file = "cert"
    m_cmd_key_file = "key"
    m_cmd_proxy_host = "proxy_host"
    m_cmd_proxy_port = "proxy_port"
    m_cmd_signing_region = "signing_region"
    m_cmd_pkcs11_lib = "pkcs11_lib"
    m_cmd_pkcs11_cert = "cert"
    m_cmd_pkcs11_pin = "pin"
    m_cmd_pkcs11_token = "token_label"
    m_cmd_pkcs11_slot = "slot_id"
    m_cmd_pkcs11_key = "key_label"
    m_cmd_message = "message"
    m_cmd_topic = "topic"
    m_cmd_verbosity = "verbosity"
    m_cmd_custom_auth_username = "custom_auth_username"
    m_cmd_custom_auth_authorizer_name = "custom_auth_authorizer_name"
    m_cmd_custom_auth_authorizer_signature = "custom_auth_authorizer_signature"
    m_cmd_custom_auth_password = "custom_auth_password"
    m_cmd_custom_auth_token_key_name = "custom_auth_token_key_name"
    m_cmd_custom_auth_token_value = "custom_auth_token_value"
    m_cmd_cognito_identity = "cognito_identity"
    m_cmd_x509_endpoint = "x509_endpoint"
    m_cmd_x509_thing_name = "x509_thing_name"
    m_cmd_x509_role_alias = "x509_role_alias"
    m_cmd_x509_cert = "x509_cert"
    m_cmd_x509_key = "x509_key"
    m_cmd_x509_ca = "x509_ca_file"
    m_cmd_port = "port"
    m_cmd_client_id = "client_id"
    m_cmd_is_ci = "is_ci"
    m_cmd_thing_name = "thing_name"
    m_cmd_mode = "mode"
    m_cmd_max_pub_ops = "max_pub_ops"
    m_cmd_print_discovery_resp_only = "print_discover_resp_only"
    m_cmd_csr = "csr"
    m_cmd_template_name = "template_name"
    m_cmd_template_parameters = "template_parameters"
    m_cmd_job_time = "job_time"
    m_cmd_use_websockets = "use_websockets"
    m_cmd_count = "count"
    m_cmd_group_identifier = "group_identifier"
    m_cmd_shadow_property = "shadow_property"
    m_cmd_shadow_value = "shadow_value"
    m_cmd_shadow_name = "shadow_name"
    m_cmd_pkcs12_file = "pkcs12_file"
    m_cmd_pkcs12_password = "pkcs12_password"
    m_cmd_region = "region"
    m_cmd_mqtt_version = "mqtt_version"
    m_cmd_session_token = "session_token"
    m_cmd_secret_access_key = "secret_access_key"
    m_cmd_access_key_id = "access_key_id"
    m_cmd_response_q_url = "response_queue_url"
    m_cmd_image_folder = "image_folder"
    m_cmd_prediction_file = "prediction_file"

