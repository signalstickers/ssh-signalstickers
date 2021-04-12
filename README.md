# SSH server for `signalstickers.com`

This project allows to serve a SSH-accessible version of `signalstickers.com`.
Intended as a April Fools' jokes, but time management is not my strong point.

## Accessing the live version

### *nix

Simply do 

```bash
ssh user@ssh.signalstickers.com
```

Accept the finderprint, and enter the password that the server will give you (yay, security!)

### Windows

Install [PuTTY](https://www.putty.org/), and connect to `ssh.signalstickers.com` with user `user`.

If you have WSL installed, refer to the *nix previous chapter.

### Current key fingerprint

```
SHA256:1dTyx71w4IEyGFfaCb9oKtz2RHl/tHgCX9V4WBwKdB8
```

## Dev

#### Installation
Suggested config: vscode + `PIPENV_VENV_IN_PROJECT=1`

```
PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
```

You will need to generate a SSH keypair with `ssh-keygen` and put it in the
`src/` folder.

#### Generating the packs data file
This project needs a zip containing all the pack with their stickers converted
to ASCII art. First, take an export of signalstickers' packs in JSON (available
at https://github.com/signalstickers/stickers/tree/gh-pages), and rename it
`packs.json`, in the `src/` folder. Then, run `src/create_packsdata.py`.