const path = require('path');

module.exports = {
  apps: [
    {
      name: 'grammar-check',
      script: path.join(__dirname, '.venv/bin/uvicorn'),
      interpreter: path.join(__dirname, '.venv/bin/python'),
      args: 'main:app --host 0.0.0.0 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
      },
      error_file: './logs/err.log',
      out_file: './logs/out.log',
      log_file: './logs/combined.log',
      time: true,
    },
  ],
};
