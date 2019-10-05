with import <nixpkgs> {};
with python37Packages;

stdenv.mkDerivation {
  name = "briefmetrics";

  src = null;

  buildInputs = [
    python37Full

    # For Pillow
    zlib
    libjpeg
    lxml
  ];

  LIBRARY_PATH="${zlib.out}/lib:${zlib.dev}/include:${lxml.out}/lib";

  LDFLAGS="-L${zlib.out}/lib -L${libjpeg.out}/lib";
  CFLAGS="-I${zlib.dev}/include -I${libjpeg.dev}/include";

  shellHook = ''
    SOURCE_DATE_EPOCH=$(date +%s)
    if [[ ! -d .env3 ]]; then
      python -m venv .env3
    fi
    source .env3/bin/activate
  '';
}
