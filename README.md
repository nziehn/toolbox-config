# toolbox-config

This package allows easy access to **YAML** based config files based on environment variable `ENV`.

[![CircleCI](https://circleci.com/gh/nziehn/toolbox-config/tree/production.svg?style=svg)](https://circleci.com/gh/nziehn/toolbox-config/tree/production)

## Features

- Using config files **per environment**, allows access to env specific data
- Config files can **inherit** from each other, to have shared variables between environments
- Access to **environment variables** via config (specify: `${env:VARIABLE}` as a value in the config)
- Access **AWS Simple System Manager Parameter Store** (specify: `${ssm:VARIABLE}` as a value in the config)
    - The parameter store allows for easy access to shared variables between services!)
    - Data in the parameter store can change during the runtime of the service - you can control the frequency how often values should be refetched from the config using the ttl parameter when creating the config.
    
    
## Basic Usage

```python
from toolbox import config as _config

config_path = '...'  # path to your config folder
config = _config.Config(path=config_path, env=None, ttl=60)
value_from_config = config.get(['some_key', 'hello', 'world'], 'DEFAULT_VALUE')
dict_from_config = config.get('some_key')  # equivalent to config.get(['some_key'])
```


#### Local development:
You can create a `local.yml` file. If you don't want to commit your personal config into the shared repo, you can use:

`local.$USER.yml` , e.g. `local.nziehn.yml` in my case, and add something like this to your `.gitignore`-file:
```
conf/local.*.yaml
```

#### Example configs

If you want to see example configs, please review the `examples` folder in this repository.

#### Installation

Use your favourite python package installer, e.g.:
```
pip install toolbox-config
```

## Suggested setup for real world projects:

1. Create a folder for configs in your repo - we will assume `REPO/conf`

2. Install toolbox-config lib: `pip install toolbox-config`

3. For ease of use, add a config.py file somewhere into your project, where you can easily import it - we will assume: `REPO/app/config.py`

4. Add the following code to your `config.py`: 
    ```python
    import os
    from toolbox import config as _config
    
    
    def get_config(env=None):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'examples')  # !! replace with path to your config folder
        config = _config.Config(path=config_path, env=env)
        return config
    ```
    
5. You can now start adding your configs - we advice adding a `base.yml` where other configs can inherit from:
    
    base config:
    ```yaml
    # base.yml
    first_key: value
    other_key: value2
    outter:
     inner: 'inner value'
 
    ``` 
    
    inherited production config:
    ```yaml
    # production.yml
    
    other_key: 'overriding value2'  # this will override he value in base.yml
    productiom_key: 'this is new'   # this key does not exist in base.yml
    
    # first_key is inherited from base.yml
    ```
    
6. You can now anywhere in your project import your `config.py` and acces the config like this:
    ```python
    from app import config as _config 
    
    def some_fn():
       config = _config.get_config()
       value = config.get(['first_key'])
       inner_value = config.get(['outter', 'inner'])
    ```


## Using AWS Param Store

First of all: Why is the abreviation of AWS Param Store 'ssm'?

- AWS System Manager used to be called "Simple System Manager" and the parameter store is a sub-api of it. In most other config tools it's called ssm as well.

If you need to configure the boto client to fetch the parameters, please use:

    ```python
    import os
    from toolbox import config as _config
    
    def get_config(env=None):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'examples')  # !! replace with path to your config folder
        boto_session = _boto3.Session(profile_name='YOUR_AWS_PROFILE_NAME')  # pass any boto session parameters...
        config = _config.Config(path=config_path, env='production', boto_session=boto_session)
        return config
    ```

In the config yaml files you can use the follow helpers to acccess AWS Parameter Store:

    ```yaml
    # base.yml
    some_string: '${ssm:NAME_OF_SSM_PARAMETER}'  # replace the all caps string with the name of your parameter
    
    complex_object_a: '${ssm_yaml:NAME_OF_SSM_PARAMETER}'  # if your parameter contains yaml data that you with to decode first
    complex_object_b: '${ssm_json:NAME_OF_SSM_PARAMETER}'  # if your parameter contains json data that you with to decode first
    ```
    
If you wonder why we have the json and yaml utility: It's possible that in a local environment you specify the values directly in the config, but in production fetch the entire object from the param store. 