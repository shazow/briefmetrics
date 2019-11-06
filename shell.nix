with import <nixpkgs> {};
with python37Packages;

stdenv.mkDerivation {
  name = "briefmetrics";

  src = null;

  buildInputs = [
    python37Full

    # cryptography (poetry)
    cffi
    pyopenssl

    # For Pillow
    zlib
    libjpeg
    libxml2
  ];

  # FIXME: Not sure if libxslt is necessary
  LIBRARY_PATH="${zlib.out}/lib:${zlib.dev}/include:${pkgs.libjpeg.out}/lib:${pkgs.libxml2.out}/lib:${pkgs.libxslt.out}/lib";
  LDFLAGS="-L${zlib.out}/lib -L${libjpeg.out}/lib";
  CFLAGS="-I${zlib.dev}/include -I${libjpeg.dev}/include";
  C_INCLUDE_PATH="${pkgs.libjpeg.dev}/include:${pkgs.libjpeg}/include:${pkgs.libxml2.dev}/include/libxml2:${pkgs.libxslt.dev}/include:${pkgs.zlib.dev}/include";

  shellHook = ''
    export HISTFILE="$PWD/.bash_history";

    SOURCE_DATE_EPOCH=$(date +%s)
    if [[ ! -d .env3 ]]; then
      python -m venv .env3
    fi
    source .env3/bin/activate
  '';
}
