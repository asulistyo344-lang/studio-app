const path = require("path");

const INSTALL_DIR = __dirname;

module.exports = {
  apps: [
    {
      name: "studio-backend",
      script: path.join(INSTALL_DIR, "venv/bin/python3.11"),
      args: "-m app.main",
      cwd: INSTALL_DIR,
      interpreter: "none",
      env: { PYTHONPATH: INSTALL_DIR },
      error_file: path.join(INSTALL_DIR, "logs/error.log"),
      out_file: path.join(INSTALL_DIR, "logs/out.log"),
      restart_delay: 5000,
      max_restarts: 10,
    },
    {
      name: "studio-worker",
      script: path.join(INSTALL_DIR, "venv/bin/arq"),
      args: "app.workers.generation_worker.WorkerSettings",
      cwd: INSTALL_DIR,
      interpreter: "none",
      env: { PYTHONPATH: INSTALL_DIR },
      error_file: path.join(INSTALL_DIR, "logs/worker-error.log"),
      out_file: path.join(INSTALL_DIR, "logs/worker-out.log"),
      restart_delay: 5000,
      max_restarts: 10,
    },
  ],
};
