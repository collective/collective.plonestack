# Ansible Collection - collective.plonestack

This is a collection of Ansible roles and modules for deploying and managing Plone installations. The goal is to ease the deployment of Plone sites and to provide a set of tools to manage them.

Main objectives include:

1. Install and configure Plone with `Ansible`
2. Do not depend on `zc.buildout` anymore

Motivations:

- Ansible is a very solid, widespread, maintained, powerful and well documented tool
- Ansible can operate locally or on a remote server
- Creating or modifying ansible tasks is by far easier than creating or modifying buildout recipes

## Available roles

### deploy_plone

Example playbook:

```yaml
- hosts: localhost
  roles:
    - role: collective.plonestack.deploy_plone
      vars:
        deploy_plone_target: "/opt/plone"
        deploy_plone_version: "6.0.12"
        deploy_plone_python: "3.11"
        deploy_plone_extra_requirements:
          - "collective.pdbpp"
          - "collective.icecream"
          - "plone.app.debugtoolbar"
        deploy_plone_extra_constraints:
          collective.icecream: 1.0.0a1
          collective.pdbpp: 1.0.0a2
        deploy_plone_source_checkouts:
          - name: "plone.app.debugtoolbar"
            repo: "git@github.com:plone/plone.app.debugtoolbar.git"
            version: "master"
        deploy_plone_zcml:
          - "plone.app.debugtoolbar"
        deploy_plone_environment_vars: |
          zope_i18n_compile_mo_files true
          CHAMELEON_CACHE {{ deploy_plone_target }}/var/cache
          DIAZO_ALWAYS_CACHE_RULES true
          PTS_LANGUAGES en
        deploy_plone_instances:
          - name: "instance"
```

#### Variables

- **`deploy_plone_target`**

  - **Description**: The target directory for the Plone installation. FIXME: for the time being the role will not expand the `~` character.
  - **Default**: Not set
  - **Example**: `{{ ansible_env.HOME }}/plone`

- **`deploy_plone_ansible_etc_dir`**

  - **Description**: A directory might contain ansible configuration files that can be used to control the deployment.
  - **Default**: Not set
  - **Example**: `{{ deploy_plone_target }}/etc/ansible`

- **`deploy_plone_version`**

  - **Description**: The version of Plone to install.
  - **Default**: Not set
  - **Example**: `6.0.12`

- **`deploy_plone_python`**

  - **Description**: The version of Python to use.
  - **Default**: Not set
  - **Example**: `3.11`

- **`deploy_plone_extra_requirements`**

  - **Description**: A list of extra packages to install.
  - **Default**: `[]`
  - **Example**:

    ```yaml
    - "collective.pdbpp"
    - "collective.icecream"
    ```

- **`deploy_plone_extra_constraints`**

  - **Description**: A dictionary of extra constraints to apply.
  - **Default**: `{}`
  - **Example**:

    ```yaml
    collective.icecream: "1.0.0a1"
    collective.pdbpp: "1.0.0a2"
    ```

- **`deploy_plone_source_checkouts`**

  - **Description**: A list of source checkouts to include in the virtual environment.
  - **Default**: `[]`
  - **Example**:

    ```yaml
    - name: "plone.app.debugtoolbar"
      repo: "git@github.com:plone/plone.app.debugtoolbar.git"
    ```

- **`deploy_plone_zcml`**

  - **Description**: A list of ZCML slugs to include in the buildout configuration.
  - **Default**: `[]`
  - **Example**:

    ```yaml
    - "plone.app.debugtoolbar"
    ```

- **`deploy_plone_environment_vars`**

  - **Description**: A string of environment variables to set.
  - **Default**: Not set
  - **Example**:

    ```yaml
    zope_i18n_compile_mo_files true
    CHAMELEON_CACHE {{ deploy_plone_target }}/var/cache
    DIAZO_ALWAYS_CACHE_RULES true
    PTS_LANGUAGES en
    ```

- **`deploy_plone_additional_zcml`**

  - **Description**: A list of additional ZCML slugs to include in the buildout configuration.
  - **Default**: `[]`
  - **Example**:

    ```yaml
    deploy_plone_additional_zcml: |
      <include package="z3c.saconfig" file="meta.zcml" />
    ```

- **deploy_plone_zeo_server_address**

  - **Description**: The address of the ZEO server.
  - **Default**: Not set, it will fallback to a f{deploy_plone_target}/var/zeoserver.sock
  - **Example**:

    ```yaml
    deploy_plone_zeo_server_address: 192.168.1.1:8100
    ```

- **deploy_plone_blob_dir**

  - **Description**: The directory where blobs will be stored.
  - **Default**: Not set, it will fallback to a f{deploy_plone_target}/var/blobstorage
  - **Example**:

    ```yaml
    deploy_plone_blob_dir: /var/blobstorage
    ```

- **`deploy_plone_instances`**

  - **Description**: A list of instances to create. Instances are described with dictionaries. More on that in the next section.
  - **Default**: `- name: "instance"`
  - **Example**:

    ```yaml
    - name: "instance"
      http_port: 8080
      fast_listen: true
      threads: 2
      key1: value1
      key2: value2
      ...
    ```

- **`deploy_plone_base_port`**

  - **Description**: The base port for the instances.
  - **Default**: `8080`
  - **Example**: `9000`

#### Instances

Instances are described with dictionaries. You can put any key-value pair you want in the dictionary. So far the playbook makes use of the following keys:

- **`name`**

  - **Description**: The name of the instance.

- **`http_port`**

  - **Description**: The port the instance will listen to
  - **Default**: Fallback to the instances `deploy_plone_base_port` + index of the instance. If `deploy_plone_base_port` is 8080 the first instance will listen to 8080, the second to 8081, etc.

- **`threads`**

  - **Description**: The number of threads the instance will use.
  - **Default**: Fallback to the instances `thread` value

- **`skip_supervisor`**

  - **Description**: If set to `true` the instance will not be managed by supervisor.
  - **Default**: `false`
