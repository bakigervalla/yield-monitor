{ pkgs }: {
  deps = [
    (pkgs.python311.withPackages (ps: with ps; [
      fastapi
      uvicorn
      jinja2
      python-multipart
      httpx
      python-dotenv
    ]))
  ];
}
