# README

## Setup
Create a file named `/etc/sudoers.d/logsql` with the following contents:

```
matt ALL=(ALL) NOPASSWD: /bin/chown -R matt /var/lib/docker/containers
```

where:
* `matt` is replaced by your username.
* `/var/lib/docker` is the path to your docker installation.

Set the permissions to that file to `0440`:
```bash
sudo chmod 0440 /etc/sudoers.d/logsql
```

Create the database that logsql will use, e.g for Postgresql:
```bash
createdb logsql
createdb logsql_test   # for testing
```


## Running

### locally
```bash
python3 -m logsql
```
