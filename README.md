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

Then run `just update` in order to download the dependencies
(and also update the playbook to the latest version).

Now you will need to get the configuration from this repository:

```bash
git clone git@github.com:3cn-ecn/matrix-config.git inventory
```

*We use ssh but you can also use https*

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

*Please note that this alone is pointless with this setup because we disabled
password storage, and thus you won't be able to log in with that user.*

It can still be used to grant admin rights to a user if they have not already
logged in. You need to create a user using this command with the same username
as the one set in [Nantral Platform](https://nantral-platform.fr/) and then login
with that user.

## Design choices

### Authentication

We use [Nantral Platform](https://nantral-platform.fr/) to provide
the password and user database. This server is developed by ourselves
and does the verification of the users for us. The main drawback is
that no user exist without an account on [Nantral Platform](https://nantral-platform.fr/),
which is sort of the goal, but it also prevents the use of bots,
because they cannot be authenticated.

### Federation

One of the great features of Matrix is federation, which allows
users from different homeservers to communicate with each other.

However, we decided to disable it so our network can remain safe
and private. Indeed, this server only aims to let the students of
Centrale Nantes communicate with each other.

### Media Storage

In order to save storage costs, we use an S3 bucket to store all the media.
All the files are uploaded there so that we save space on the VPS.

### Element

We host our own element web client, in order to have more control on
what is available. However, we do not host the mobile clients, so
users would be required to use the official Element clients

Keep in mind that all matrix clients should be able to connect to the server,
even if we recommend using our hosted Element web client.

## Changing the Configuration

Please refer once again the [MDAD documentation](https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/prerequisites.md#your-local-computer)
for all the available options and how to update the playbook on the remote host.
