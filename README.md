# Matrix Configuration

This is the configuration file for the matrix homeserver of the students
of Centrale Nantes. It uses the [Matrix Docker Ansible Deploy (MDAD)](https://github.com/spantaleev/matrix-docker-ansible-deploy)
playbook.

See the [config file](host_vars/matrix.nantral-platform.fr/vars.yml) for the
details on the configuration.

Please refer to the [Matrix Docker Ansible Deploy documentation](https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/README.md)
if you want more information on how to use this configuration.

## First Time Setup

You need to follow the [MDAD documentation](https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/prerequisites.md#your-local-computer)
for your local setup.

Then you need to get the playbook using

```bash
git clone https://github.com/spantaleev/matrix-docker-ansible-deploy.git
cd matrix-docker-ansible-deploy
```

Now you will need to get the configuration from this repository:

```bash
git clone git@github.com:3cn-ecn/matrix-config.git inventory
```

*We use ssh but you can also use https*

*Note: for the next steps, please don't `cd` into this repo.*

It is then necessary to run

```bash
git apply inventory/grafana_logs.patch
```

in order to add the logs to Grafana (not included in the playbook).

Then, run `just update` in order to download the dependencies
(and also update the playbook to the latest version). If you encounter
errors linked with the patch, please update the patch to work with
the latest version of the playbook.

If you want to deploy to another server, move the `vars.yml` file to the
appropriate directory, change the server name in it and update the
[`inventory/hosts`](hosts) file.

You also need to reconfigure all the vault encrypted variables.

Finally, you can run the playbook with:

```bash
just install-all --ask-vault-pass
```

If you removed components, you will need to run to actually remove them:

```bash
just setup-all --ask-vault-pass
```

To create a new user, you can run (`yes` at the end is for granting admin rights,
use `no` if you don't want to):

```bash
just register-user YOUR_USERNAME YOUR_PASSWORD yes --ask-vault-pass
```

## Design choices

### Authentication

We use [Matrix Authetication Service](https://element-hq.github.io/matrix-authentication-service/)
as authentication method in order to comply with the latest matrix clients.
[Nantral Platform](https://nantral-platform.fr/) is configured as an upstream
account provider. This website is developed by ourselves and does the
verification of the users for us. We can also add other accounts with
token registration if we want to add external users.

To add someone with token registration, you can do it from the [admin panel](https://admin.nantral-platform.fr/registration-tokens?revoked=false).
Click add, let the first field empty, add a limit of 1 use (one token per user recommended)
and add a expiration date (recommended). Then you can give the token to the user and they
can use it to register on the server.

### Federation

One of the great features of Matrix is federation, which allows
users from different homeservers to communicate with each other.

However, we decided to disable it so our network can remain safe
and private. Indeed, this server only aims to let the students of
Centrale Nantes communicate with each other.

### Media Storage

In order to save storage costs and improve performances,
we use an S3 bucket to store all the media. All the files
are uploaded there so that we save space on the VPS.

### Element

We host our own element web client, in order to have more control on
what is available. However, we do not host the mobile clients, so
users would be required to use the official Element clients

Keep in mind that all matrix clients should be able to connect to the server,
even if we recommend using our hosted Element web client.

## Changing the Configuration

Please refer once again the [MDAD documentation](https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/prerequisites.md#your-local-computer)
for all the available options and how to update the playbook on the remote host.
