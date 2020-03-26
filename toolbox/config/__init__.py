import os
import json as _json
import yaml as _yaml
import getpass as _getpass
import boto3 as _boto3
from cachetools import TTLCache

INHERITS_KEY = 'INHERITS'


def get_env(env=None):
    if env is None:
        env = os.environ.get('ENV', 'local')
    env = env.lower()
    return env


class Config(object):
    def __init__(self, path, env=None, ttl=5 * 60, boto_session=None):
        """
        Create a config object that allows access to your config values through the `get` method.

        :param path: The path to the config folder (can be relative!).
            To make unit testing easier, allows to pass a dict as mock config as well!
        :param env: The environment name, the value will be internally passed to `get_env(env)`
        :param ttl: If config values are read from dynamic sources (e.g. AWS Param Store)
            the ttl specifies the number of seconds the
            value will be cached befored refetching from the source
        :param boto_session: Pass a boto session to be able to control AWS access if needed in your config
        """
        self.__env = get_env(env)
        if isinstance(path, dict):
            config_data = [path]
        else:
            config_data = self._load(path=path)
        self.__config_data = config_data
        self.__cache = TTLCache(maxsize=1000, ttl=ttl)
        self.__boto_session = boto_session

    def get(self, key_path, default_value=None):
        """
        Get parameters from the config.

        If you need to access config values in nested dicts,
        make use of the key path, since it handles the config inheritance.

        :param key_path: a list or tuple of values to specify where the key should be looked up in nested dicts.
            You can also just provide a string to access top level fields.
        :param default_value: The default value in case the key does not exist. Default: None
        :return: The value behind the key_path or default_value

        >>> Config({'hello': {'world': 42}}).get(['hello', 'world'])
        42
        """
        if isinstance(key_path, list):
            key_path = tuple(key_path)
        elif not isinstance(key_path, tuple):
            key_path = (key_path, )

        for config_dict in self.__config_data:
            current = config_dict
            try:
                for key in key_path:
                    current = current[key]
            except:
                continue
            return self._handle_special_values(current)

        return default_value

    def _get_config_path(self, config_name, path):
        # check whether user has a locally modified config!
        if config_name == 'local':
            user_conf_path = os.path.join(path, '{}.{}.yml'.format(config_name, _getpass.getuser()))
            if os.path.exists(user_conf_path):
                return user_conf_path

        return os.path.join(path, config_name + '.yml')

    def _load(self, path):
        config_name = self.__env
        result = []
        while True:
            config_path = self._get_config_path(config_name=config_name, path=path)
            if not os.path.exists(config_path):
                raise ValueError('Config path does not exist: {}'.format(config_path))

            with open(config_path) as config_file:
                config_dict = _yaml.load(config_file, Loader=_yaml.FullLoader) or {}
                result.append(config_dict)
                if INHERITS_KEY not in config_dict:
                    break

                # could happen if somebody is making copy paste errors!
                if config_name == config_dict[INHERITS_KEY]:
                    break

                config_name = config_dict[INHERITS_KEY]

        return result

    def _handle_special_values(self, value):
        if isinstance(value, str):
            if value.startswith('$${') and value.endswith('}'):
                return value[1:]

            if value.startswith('${') and value.endswith('}'):
                fn_key, fn_value = tuple(value[2:-1].split(':', 1))
                if fn_key == 'env':
                    return os.environ.get(fn_value)

                if fn_key == 'ssm':
                    return self._get_from_aws_ssm(fn_value, None)

                if fn_key == 'ssm_json':
                    return self._get_from_aws_ssm(fn_value, 'json')

                if fn_key == 'ssm_yaml':
                    return self._get_from_aws_ssm(fn_value, 'yaml')

        return value

    def _get_from_aws_ssm(self, key, loader_type):
        cache_key = ('ssm', key)
        if cache_key in self.__cache:
            return self.__cache[cache_key]

        client = (self.__boto_session or _boto3).client('ssm')
        resp = client.get_parameter(
            Name=key,
            WithDecryption=True
        )
        value = resp['Parameter']['Value']

        if loader_type:
            if loader_type == 'json':
                value = _json.loads(value)
            if loader_type == 'yaml':
                value = _yaml.full_load(value)

        self.__cache[cache_key] = value
        return value
