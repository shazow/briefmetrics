with import <nixpkgs> {};

let
  pythonPackages = python3Packages;
in pkgs.mkShell rec {
  name = "briefmetrics";
  venvDir = "./.env3";

  buildInputs = [
    # Required for venvDir
    pythonPackages.python
    pythonPackages.venvShellHook

    # Baseline updates
    pythonPackages.pip
    pythonPackages.poetry

    # cryptography (poetry)
    pythonPackages.cffi
    pythonPackages.pyopenssl

    # For Pillow
    zlib
    libjpeg
    libxml2

    # for scss
    sassc
  ];

  # FIXME: Not sure if libxslt is necessary
  LIBRARY_PATH="${zlib.out}/lib:${zlib.dev}/include:${pkgs.libjpeg.out}/lib:${pkgs.libxml2.out}/lib:${pkgs.libxslt.out}/lib";
  LDFLAGS="-L${zlib.out}/lib -L${libjpeg.out}/lib";
  CFLAGS="-I${zlib.dev}/include -I${libjpeg.dev}/include";
  C_INCLUDE_PATH="${pkgs.libjpeg.dev}/include:${pkgs.libjpeg}/include:${pkgs.libxml2.dev}/include/libxml2:${pkgs.libxslt.dev}/include:${pkgs.zlib.dev}/include";

  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    poetry install
    python setup.py install_egg_info
  '';

  postShellHook = ''
    unset SOURCE_DATE_EPOCH
    export HISTFILE="$PWD/.bash_history";
  '';
}
