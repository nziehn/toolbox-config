import os
import yaml as _yaml
import getpass as _getpass
import boto3
from cachetools import TTLCache

INHERITS_KEY = 'INHERITS'


def get_env(env=None):
    if env is None:
        env = os.environ.get('ENV', 'local')
    env = env.lower()
    return env


class Config(object):
    def __init__(self, path, env=None, ttl=5 * 60):
        self.__env = get_env(env)
        self.__config_data = self._load(path=path)
        self.__cache = TTLCache(maxsize=1000, ttl=ttl)

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
            with open(config_path) as config_file:
                config_dict = _yaml.load(config_file)
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
                    return self._get_from_aws_ssm(fn_value)

        return value

    def _get_from_aws_ssm(self, key):
        cache_key = ('ssm', key)
        if cache_key in self.__cache:
            return self.__cache[cache_key]

        client = boto3.client('ssm')
        resp = client.get_parameter(
            Name=key,
            WithDecryption=True
        )
        value = resp['Parameter']['Value']
        self.__cache[cache_key] = value
        return value

    def get(self, key_path, default_value=None):
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

