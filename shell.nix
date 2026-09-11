{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # Packages installed into the environment
  packages = [
    (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
      # List your required Python packages here
 #     pandas
#      requests
#      pysocks
#      numpy
    ]))
    
    # Non-Python system utilities can be added here
    pkgs.git
  ];

  # Optional: Environment variables or startup scripts
  shellHook = ''
    echo "Python development environment loaded!"
    python --version
  '';
}

