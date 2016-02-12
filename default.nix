{ stdenv, pkgs, ... }:
{
  ec2-reservation-pricing-comparison = stdenv.mkDerivation {
    name = "ec2-reservation-pricing-comparison";
    buildInputs = [
        pkgs.curl
        pkgs.cacert
        pkgs.python3
        pkgs.awscli
    ];

    shellHook = ''
      export SSL_CERT_FILE='/etc/ssl/certs/ca-certificates.crt'
    '';
  };
}
