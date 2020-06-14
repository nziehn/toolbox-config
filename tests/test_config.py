import os
from nose import tools as _tools
import mock as _mock
from unittest.mock import patch as _patch
from toolbox import config as _config


def get_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'examples')
    config = _config.Config(path=config_path, env='production')
    return config


def test_example():
    config = get_config()

    _tools.assert_equal(
        config.get(['deep', 'inner', 'value']),
        'base-fallback',
    )

    _tools.assert_equal(
        config.get(['data']),
        ['this', 'is', 'production'],
    )

    _tools.assert_equal(
        config.get(['new-key']),
        'new-production-value',
    )

    _tools.assert_equal(
        config.get(['key']),
        'base-value',
    )


def test_special_value_handling():
    config = get_config()
    expected_ssm_value = 'expected_ssm_value'
    env_var = 'ENV_VAR'

    with _patch.dict('os.environ', {'MYSQL_PASSWORD': env_var}):
        with _mock.patch.object(config, '_get_from_aws_ssm', return_value=expected_ssm_value) as _:
            _tools.assert_equal(
                config.get(key_path=['mysql', 'user']),
                expected_ssm_value
            )

            _tools.assert_equal(
                config.get(key_path=['mysql', 'password']),
                env_var
            )

            _tools.assert_equal(
                config.get(key_path=['mysql']).get('password'),
                env_var
            )


def test_special_value_this():
    config = get_config()
    _tools.assert_equal(
        config.get(key_path=['cross_reference_example']),
        'production'
    )


if __name__ == '__main__':
    test_example()