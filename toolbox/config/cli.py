import textwrap as _textwrap
import argparse as _argparse
from toolbox import config as _config
import jsonpath_ng as _jsonpath_ng
import os as _os
import re as _re


def main():
    args = _parse_args()
    key_path = _config.Config.jsonpath_to_path(args.key_path[0])
    _handle_remote_config(key_path=key_path)
    _handle_normal_config(key_path=key_path, args=args)


def _parse_args():
    parser = _argparse.ArgumentParser(
        description=_textwrap.dedent(
            """
            Get configuration values.
            
            Example Usage:
            ---
            tb_config '$.key.path.to.value'
            tb_config '$.key[0].hello["Hello World"]'
            tb_config '$.__ssm_yaml__.YOUR_SSM_NAME.key.path.to.value'
            
            (Optional) environment variables:
            TB_CONFIG_PATH: Path to the config(s) folder
            TB_CONFIG_ENV: Which environment to used, can be overriden by --env parameter!
            ENV: if TB_CONFIG_ENV is not provided, then this one is used instead
            """
        ),
        formatter_class=_argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "key_path",
        nargs="+",
        help=(
            "The key path to access config values."
            " Use '.' to access properties, '[x]' for lists,"
            " '[\"some key\"]' for non standard property names"
        ),
    )
    parser.add_argument(
        "-e",
        "--env",
        help="Define which environment should be used (overrides TB_CONFIG_ENV env variable)",
    )
    parser.add_argument(
        "-p", "--config_path", help="Where can the config folder be found",
    )
    return parser.parse_args()


def _handle_remote_config(key_path):
    config_sources = ["ssm_yaml", "ssm_json", "ssm"]

    if len(key_path) >= 2:
        match = _re.match(r"__(.+)__", key_path[0])
        if match:
            if match.group(1) in config_sources:
                force_config = {
                    "ROOT": "${{{}:{}}}".format(match.group(1), key_path[1])
                }
                config = _config.Config(path=force_config)
                value = config.get(key_path=["ROOT"] + key_path[2:])
                print(value)  # we're finished
                exit(0)


def _handle_normal_config(key_path, args):
    env = (
        args.env
        or _os.environ.get("TB_CONFIG_ENV")
        or _os.environ.get("ENV")
        or "local"
    )
    config_path = args.config_path or _os.environ.get("TB_CONFIG_PATH") or "config"
    config = _config.Config(path=config_path, env=env)
    value = config.get(key_path=key_path)
    print(value)
    exit(0)


if __name__ == "__main__":
    main()
