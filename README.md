# applover-t1

A (apparently?) first-phase recruitment task, API for a library

## Usage

> Wywołanie polecenia `docker-compose up` powinno skutkować uruchomieniem działającej aplikacji.

### Development

#### Prerequisites
- [nix](https://nixos.org/download.html)
- `direnv` (`nix-env -iA nixpkgs.direnv`)
- [configured direnv shell hook ](https://direnv.net/docs/hook.html)
- some form of `make` (`nix-env -iA nixpkgs.gnumake`)

Hint: if something doesn't work because of missing package please add the package to `default.nix` instead of installing it on your computer. Why solve the problem for one if you can solve the problem for all? ;)

#### One-time setup
```
make init
```

#### Everything
```
make help
```

## Meta

I've heard that this task was to showcase my thinking, you may find the [decision_log.md](decision_log.md) interesting
