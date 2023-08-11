# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import os
import pathlib
import shutil
from distutils.dir_util import copy_tree
from tempfile import mkdtemp
from typing import List, Optional, Tuple, Dict

from pyhocon import ConfigFactory as CF
from pyhocon import ConfigTree

from nvflare.apis.job_def import JobMetaKey
from nvflare.cli_exception import CLIException
from nvflare.fuel.flare_api.flare_api import new_secure_session
from nvflare.fuel.utils.config import ConfigFormat
from nvflare.fuel.utils.config_factory import ConfigFactory
from nvflare.tool.job.config.configer import merge_configs_from_cli, extract_value_from_index, \
    build_config_file_indexers
from nvflare.utils.cli_utils import append_if_not_in_list, get_curr_dir, get_startup_kit_dir, save_config, \
    find_job_template_location, get_hidden_nvflare_dir

CMD_LIST_TEMPLATES = "list_templates"
CMD_SHOW_VARIABLES = "show_variables"
CMD_CREATE_JOB = "create"
CMD_SUBMIT_JOB = "submit"


def find_filename_basename(f: str):
    basename = os.path.basename(f)
    if "." in basename:
        return os.path.splitext(basename)[0]
    else:
        return basename


def build_job_template_indices(job_template_dir: str) -> ConfigTree:
    conf = CF.parse_string("{ templates = {} }")
    config_file_base_names = ["config_fed_client", "config_fed_server", "config_exchange", "meta"]
    template_conf = conf.get("templates")
    keys = ["description", "controller_type", "client_category"]
    for root, dirs, files in os.walk(job_template_dir):
        config_files = [f for f in files if find_filename_basename(f) in config_file_base_names]
        if len(config_files) > 0:
            job_temp_name = find_filename_basename(root)
            info_conf = get_template_info_config(root)
            for key in keys:
                value = info_conf.get(key, "NA") if info_conf else "NA"
                template_conf.put(f"{root}.{key}", value)

    # save the index file for debugging purpose
    save_job_template_index_file(conf)
    return conf


def save_job_template_index_file(conf):
    dst_path = get_template_registry_file_path()
    save_config(conf, dst_path)


def get_template_registry_file_path():
    filename = "job_templates.conf"
    hidden_nvflare_dir = get_hidden_nvflare_dir()
    file_path = os.path.join(hidden_nvflare_dir, filename)
    return file_path


def get_template_info_config(template_dir):
    info_conf_path = os.path.join(template_dir, "info.conf")
    return CF.parse_file(info_conf_path) if os.path.isfile(info_conf_path) else None


def create_job(cmd_args):
    prepare_job_folder(cmd_args)
    job_template_location = find_job_template_location()
    template_index_conf = build_job_template_indices(job_template_location)
    job_folder = cmd_args.job_folder
    config_dir = get_config_dir(job_folder)

    fmt, real_config_path = ConfigFactory.search_config_format("config_fed_server.conf", [config_dir])
    if real_config_path and not cmd_args.force:
        print(
            f"""\nwarning: configuration files:\n
                {"config_fed_server.[json|conf|yml]"} already exists.
            \nNot generating the config files. If you would like to overwrite, use -force option"""
        )
        return

    target_template_name = cmd_args.template
    check_config_exists(target_template_name, template_index_conf)

    job_template_dir = find_job_template_location()
    src = os.path.join(job_template_dir, target_template_name)
    copy_tree(src=src, dst=config_dir)
    prepare_meta_config(cmd_args)

    variable_values = prepare_job_config(cmd_args)
    display_template_variables(variable_values)


def show_variables(cmd_args):
    indices: Dict[str, (Dict, Dict)] = build_config_file_indexers(cmd_args.job_folder)
    variable_values = extract_value_from_index(indices_configs=indices)
    variable_values = extract_value_from_index(indices_configs=indices)
    display_template_variables(variable_values)


def check_config_exists(target_temp_name, template_index_conf):

    targets = [os.path.basename(key) for key in template_index_conf.get("templates").keys()]
    found = target_temp_name in targets

    if not found:
        raise ValueError(
            f"Invalid template name {target_temp_name}, "
            f"please check the available templates using nvflare job list_templates"
        )


def display_template_variables(variable_values: Dict[str, Dict]):
    print("\nThe following are the variables you can change in the template\n")
    print("-" * 100)
    file_name_fix_length = 35
    var_name_fix_length = 25
    var_value_fix_length = 25
    file_name = fix_length_format("file_name", file_name_fix_length)
    var_name = fix_length_format("var_name", var_name_fix_length)
    var_value = fix_length_format("value", var_value_fix_length)
    print(" " * 3, file_name, var_name, var_value)
    print("-" * 100)
    for file in sorted(variable_values.keys()):
        indices = variable_values.get(file)
        file_name = os.path.basename(file)
        file_name = fix_length_format(file_name, file_name_fix_length)
        for index in sorted(indices.keys()):
            var_name = fix_length_format(index, var_name_fix_length)
            var_value = indices[index]
            print(" " * 3, file_name, var_name, var_value)
        print("")
    print("-" * 100)


def list_templates(cmd_args):
    job_template_dir = find_job_template_location(cmd_args.job_template_dir)
    template_index_conf = build_job_template_indices(job_template_dir)
    display_available_templates(template_index_conf)

    if cmd_args.job_template_dir:
        update_job_template_dir(cmd_args.job_template_dir)


def update_job_template_dir(job_template_dir: str):
    hidden_nvflare_dir = get_hidden_nvflare_dir()
    file_path = os.path.join(hidden_nvflare_dir, "config.conf")
    config = CF.parse_file(file_path)
    config.put("job_template", job_template_dir)
    save_config(config, file_path)


def display_available_templates(template_index_conf):
    print("\nThe following job templates are available: \n")
    template_registry = template_index_conf.get("templates")
    print("-" * 120)
    name_fix_length = 15
    description_fix_length = 60
    controller_type_fix_length = 20
    client_category_fix_length = 20
    name = fix_length_format("name", name_fix_length)
    description = fix_length_format("description", description_fix_length)
    client_category = fix_length_format("client category", client_category_fix_length)
    controller_type = fix_length_format("controller type", controller_type_fix_length)
    print(" " * 2, name, description, controller_type, client_category)
    print("-" * 120)
    for file_path in sorted(template_registry.keys()):
        name = os.path.basename(file_path)
        # print(f"{name=}", f"{file_path=}", f"{template_registry=}")
        template_info = template_registry.get(file_path, None)
        if not template_info:
            template_info = template_registry.get(name)
        name = fix_length_format(name, name_fix_length)
        description = fix_length_format(template_info.get("description"), description_fix_length)
        client_category = fix_length_format(template_info.get("client_category"), client_category_fix_length)
        controller_type = fix_length_format(template_info.get("controller_type"), controller_type_fix_length)
        print(" " * 2, name, description, controller_type, client_category)
    print("-" * 120)


def fix_length_format(name: str, name_fix_length: int):
    return f"{name[:name_fix_length]:{name_fix_length}}"


def submit_job(cmd_args):
    temp_job_dir = None
    try:
        temp_job_dir = mkdtemp()
        copy_tree(cmd_args.job_folder, temp_job_dir)

        prepare_job_config(cmd_args, temp_job_dir)
        admin_username, admin_user_dir = find_admin_user_and_dir()
        internal_submit_job(admin_user_dir, admin_username, temp_job_dir)
    finally:
        if temp_job_dir:
            if cmd_args.debug:
                print(f"in debug mode, job configurations can be examined in temp job directory '{temp_job_dir}'")
            else:
                shutil.rmtree(temp_job_dir)


def find_admin_user_and_dir() -> Tuple[str, str]:
    startup_kit_dir = get_startup_kit_dir()
    fed_admin_config = ConfigFactory.load_config("fed_admin.json", [startup_kit_dir])

    admin_user_dir = None
    admin_username = None
    if fed_admin_config:
        admin_user_dir = os.path.dirname(os.path.dirname(fed_admin_config.file_path))
        config_dict = fed_admin_config.to_dict()
        admin_username = config_dict["admin"].get("username", None)
    else:
        raise ValueError(f"Unable to locate fed_admin configuration from startup kid location {startup_kit_dir}")

    return admin_username, admin_user_dir


def internal_submit_job(admin_user_dir, username, temp_job_dir):
    sess = new_secure_session(username=username, startup_kit_location=admin_user_dir)
    job_id = sess.submit_job(temp_job_dir)
    print(f"job: '{job_id} was submitted")


job_sub_cmd_handlers = {CMD_CREATE_JOB: create_job,
                        CMD_SUBMIT_JOB: submit_job,
                        CMD_LIST_TEMPLATES: list_templates,
                        CMD_SHOW_VARIABLES: show_variables}


def handle_job_cli_cmd(cmd_args):
    job_cmd_handler = job_sub_cmd_handlers.get(cmd_args.job_sub_cmd, None)
    job_cmd_handler(cmd_args)


def def_job_cli_parser(sub_cmd):
    cmd = "job"
    parser = sub_cmd.add_parser(cmd)
    job_subparser = parser.add_subparsers(title="job", dest="job_sub_cmd", help="job subcommand")
    define_list_templates_parser(job_subparser)
    define_create_job_parser(job_subparser)
    define_submit_job_parser(job_subparser)
    define_variables_parser(job_subparser)

    return {cmd: parser}


def define_submit_job_parser(job_subparser):
    submit_parser = job_subparser.add_parser("submit", help="submit job")
    submit_parser.add_argument(
        "-j",
        "--job_folder",
        type=str,
        nargs="?",
        default=os.path.join(get_curr_dir(), "current_job"),
        help="job_folder path, default to current directory",
    )
    submit_parser.add_argument(
        "-f",
        "--config_file",
        type=str,
        action="append",
        nargs="*",
        help="""Training config file with corresponding optional key=value pairs. 
                                       If key presents in the preceding config file, the value in the config
                                       file will be overwritten by the new value """,
    )
    submit_parser.add_argument(
        "-a",
        "--app_config",
        type=str,
        nargs="*",
        help="""key=value options will be passed directly to script argument """,
    )

    submit_parser.add_argument("-debug", "--debug", action="store_true", help="debug is on")


def define_list_templates_parser(job_subparser):
    show_jobs_parser = job_subparser.add_parser("list_templates", help="show available job templates")
    show_jobs_parser.add_argument(
        "-d",
        "--job_template_dir",
        type=str,
        nargs="?",
        default=None,
        help="Job template directory, if not specified, "
             "will search from ./nvflare/config.conf and NVFLARE_HOME env. variables",
    )
    show_jobs_parser.add_argument("-debug", "--debug", action="store_true", help="debug is on")


def define_variables_parser(job_subparser):
    show_variables_parser = job_subparser.add_parser("show_variables",
                                                     help="show template variable values in configuration")
    show_variables_parser.add_argument(
        "-j",
        "--job_folder",
        type=str,
        nargs="?",
        default=os.path.join(get_curr_dir(), "current_job"),
        help="job_folder path, default to current directory",
    )
    show_variables_parser.add_argument("-debug", "--debug", action="store_true", help="debug is on")


def define_create_job_parser(job_subparser):
    create_parser = job_subparser.add_parser("create", help="create job")
    create_parser.add_argument(
        "-j",
        "--job_folder",
        type=str,
        nargs="?",
        default=os.path.join(get_curr_dir(), "current_job"),
        help="job_folder path, default to current directory",
    )
    create_parser.add_argument(
        "-w",
        "--template",
        type=str,
        nargs="?",
        default="sag_pt",
        help="""template name, use liste_templates to see available jobs from job templates """,
    )
    create_parser.add_argument("-s", "--script", type=str, nargs="?", help="""code script such as train.py""")
    create_parser.add_argument(
        "-sd",
        "--script_dir",
        type=str,
        nargs="?",
        help="""script directory contains additional related files. 
                                       All files or directories under this directory will be copied over 
                                       to the custom directory.""",
    )
    create_parser.add_argument(
        "-f",
        "--config_file",
        type=str,
        action="append",
        nargs="*",
        help="""Training config file with corresponding optional key=value pairs. 
                                       If key presents in the preceding config file, the value in the config
                                       file will be overwritten by the new value """,
    )
    create_parser.add_argument(
        "-a",
        "--app_config",
        type=str,
        nargs="*",
        help="""key=value options will be passed directly to script argument """,
    )
    create_parser.add_argument("-debug", "--debug", action="store_true", help="debug is on")
    create_parser.add_argument(
        "-force",
        "--force",
        action="store_true",
        help="force create is on, if -force, " "overwrite existing configuration with newly created configurations",
    )


# ====================================================================
def prepare_job_config(cmd_args, tmp_job_dir: Optional[str] = None):
    update_client_app_script(cmd_args)
    merged_conf = merge_configs_from_cli(cmd_args)
    if tmp_job_dir is None:
        tmp_job_dir = cmd_args.job_folder
    save_merged_configs(merged_conf, tmp_job_dir)
    variable_values = extract_value_from_index(merged_conf)

    return variable_values


def update_client_app_script(cmd_args):
    if cmd_args.app_config:
        client_config, config_path = _update_client_app_config_script(cmd_args.job_folder, cmd_args.app_config)

        print(f"2. {client_config=}", config_path)
        client_config.put("hello", "chester")
        save_config(client_config, config_path)


def _update_client_app_config_script(job_folder, app_config: str) -> Tuple[ConfigTree, str]:
    config_args = " ".join([f"--{k}" for k in app_config])
    config_dir = get_config_dir(job_folder)
    config = ConfigFactory.load_config( os.path.join(config_dir, "config_fed_client.xxx"))
    if config.format == ConfigFormat.JSON or config.format == ConfigFormat.OMEGACONF:
        client_config = CF.from_dict(config.to_dict())
    else:
        client_config = config.conf

    client_config.put("app_config", config_args)
    return client_config, config.file_path


def save_merged_configs(merged_conf, tmp_job_dir):
    for file, (file_indices, file_configs) in merged_conf.items():
        config_dir = pathlib.Path(tmp_job_dir) / "app" / "config"
        base_filename = os.path.basename(file)
        if base_filename.startswith("meta."):
            config_dir = tmp_job_dir
        base_filename = os.path.splitext(base_filename)[0]
        dst_path = os.path.join(config_dir, f"{base_filename}.json")
        save_config(file_configs, dst_path)


def get_upload_dir(startup_dir) -> str:
    console_config_path = os.path.join(startup_dir, "fed_admin.json")
    try:
        with open(console_config_path, "r") as f:
            console_config = json.load(f)
            upload_dir = console_config["admin"]["upload_dir"]
    except IOError as e:
        raise CLIException(f"failed to load {console_config_path} {e}")
    except json.decoder.JSONDecodeError as e:
        raise CLIException(f"failed to load {console_config_path}, please double check the configuration {e}")
    return upload_dir


def prepare_model_exchange_config(job_folder: str, force: bool):
    dst_path = dst_config_path(job_folder, "config_exchange.conf")
    if os.path.isfile(dst_path) and not force:
        return

    dst_config = load_src_config_template("config_exchange.conf")
    save_config(dst_config, dst_path)


def load_predefined_config():
    file_dir = os.path.dirname(__file__)
    return CF.parse_file(os.path.join(file_dir, "config/pre_defined.conf"))


def prepare_meta_config(cmd_args):
    job_folder = cmd_args.job_folder
    app_name = os.path.basename(job_folder)
    dst_path = os.path.join(job_folder, "meta.conf")

    # Use existing meta.conf if user already defined it.
    folder_name_key = JobMetaKey.JOB_FOLDER_NAME.value
    if not os.path.isfile(dst_path):
        dst_config = load_src_config_template("meta.conf")
        dst_config.put("name", app_name)
    else:
        dst_config = CF.from_dict(ConfigFactory.load_config(dst_path).to_dict())

    dst_config.put(folder_name_key, os.path.basename(job_folder))
    save_config(dst_config, dst_path)


def load_src_config_template(config_file_name: str):
    file_dir = os.path.dirname(__file__)
    config_template = CF.parse_file(os.path.join(file_dir, f"config/{config_file_name}"))
    return config_template


def dst_app_path(job_folder: str):
    return os.path.join(job_folder, "app")


def dst_config_path(job_folder, config_filename):
    config_dir = get_config_dir(job_folder)
    dst_path = os.path.join(config_dir, config_filename)
    return dst_path


def get_config_dir(job_folder):
    app_dir = dst_app_path(job_folder)
    config_dir = os.path.join(app_dir, "config")
    return config_dir


def convert_args_list_to_dict(kvs: Optional[List[str]] = None) -> dict:
    """
    Convert a list of key-value strings to a dictionary.

    Args:
        kvs (Optional[List[str]]): A list of key-value strings in the format "key=value".

    Returns:
        dict: A dictionary containing the key-value pairs from the input list.
    """
    kv_dict = {}
    if kvs:
        for kv in kvs:
            try:
                key, value = kv.split("=")
                kv_dict[key.strip()] = value.strip()
            except ValueError:
                raise ValueError(f"Invalid key-value pair: '{kv}'")

    return kv_dict


def prepare_job_folder(cmd_args):
    job_folder = cmd_args.job_folder
    if job_folder:
        if not os.path.exists(job_folder):
            os.makedirs(job_folder)
        elif not os.path.isdir(job_folder):
            raise ValueError(f"job_folder '{job_folder}' exits but not directory")

    app_dir = os.path.join(job_folder, "app")
    app_config_dir = os.path.join(app_dir, "config")
    app_custom_dir = os.path.join(app_dir, "custom")
    dirs = [app_dir, app_config_dir, app_custom_dir]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    if cmd_args.script and len(cmd_args.script.strip()) > 0:
        if os.path.exists(cmd_args.script):
            shutil.copy(cmd_args.script, app_custom_dir)
        else:
            raise ValueError(f"{cmd_args.script} doesn't exists")

    if cmd_args.script_dir and len(cmd_args.script_dir.strip()) > 0:
        if os.path.exists(cmd_args.script_dir):
            copy_tree(cmd_args.script_dir, app_custom_dir)
        else:
            raise ValueError(f"{cmd_args.script_dir} doesn't exists")
