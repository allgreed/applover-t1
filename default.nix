let
  pkgs = import (builtins.fetchGit {
    url = "https://github.com/nixos/nixpkgs/";
    ref = "refs/heads/nixos-unstable";
    rev = "b8697e57f10292a6165a20f03d2f42920dfaf973"; # 4-03-2024
    # obtain via `git ls-remote https://github.com/nixos/nixpkgs nixos-unstable`
  }) { config = {}; };

  # helpers
  pythonDevPkgs = python-packages: devDeps python-packages;
  devPython = pythonCore.withPackages pythonDevPkgs;

  pythonCore = pkgs.python311;
  devDeps = p: with p; [
    ptpython # nicer repl
    pytest

    psycopg2
  ];
in
{
  pname = "fillthis";
  version = "0.0.1";
  shell = pkgs.mkShellNoCC {
    buildInputs = with pkgs; [
      git
      gnumake

      devPython
      pyright
      pdm
      ruff
      ruff-lsp

      podman
      podman-compose

      # if managed fully by nix we could probably have version of this automatically match the server version
      # "use more podman" alas
      postgresql_16
    ];
  };
}
