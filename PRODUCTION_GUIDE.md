# Production Deployment Guide

This guide will help you deploy the VolumeAI Flask application in a production environment.

## Docker Deployment (Recommended)

The easiest way to deploy this application is using Docker and Docker Compose:

1. Make sure you have Docker and Docker Compose installed on your server.
2. Clone the repository to your server.
3. Copy `.env.example` to `.env` and update all the variables:
   ```bash
   cp .env.example .env
   nano .env  # edit all required variables
   ```
   
   Make sure to set the following required variables:
   - `SECRET_KEY`: A strong, random key for securing your app
   - `PORT`: The port your app will run on (default: 5001)
   - `FLASK_ENV`: Set to "production" for production deployment
   - `VISION_AGENT_API_KEY`: Your API key if needed

4. Build and start the Docker containers:
   ```bash
   docker-compose up -d
   ```
   
   Docker Compose will automatically load environment variables from the .env file.

5. Access your application at http://your-server-ip:5001

## Manual Deployment

If you prefer to deploy without Docker:

1. Set up a Python 3.9+ environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   export SECRET_KEY="your-strong-secret-key"
   export FLASK_ENV="production"
   export PORT=5001
   ```
4. Start the Gunicorn server:
   ```bash
   gunicorn --bind 0.0.0.0:5001 --workers 3 --timeout 120 wsgi:app
   ```

## Nginx Reverse Proxy (Recommended)

For production, you should place the application behind a reverse proxy like Nginx:

1. Install Nginx:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. Create a new Nginx site configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/volumeai
   ```

3. Add the following configuration (update the server_name):
   ```
   server {
       listen 80;
       server_name yourdomain.com;
   
       location / {
           proxy_pass http://127.0.0.1:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           client_max_body_size 16M;
       }
   }
   ```

4. Enable the site and restart Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/volumeai /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. Set up SSL with Let's Encrypt for production security:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

## Monitoring and Maintenance

- Set up log rotation for application logs
- Consider using a monitoring system like Prometheus/Grafana or Datadog
- Regularly update dependencies and apply security patches
- Create a backup strategy for your uploads and results folders 

## Troubleshooting

### Environment Variables Not Loading

If you suspect that environment variables from your .env file are not being loaded correctly:

1. Run the included test script to check environment variables:
   ```bash
   # If running locally:
   python test_env.py
   
   # If using Docker:
   docker-compose exec web python test_env.py
   ```

2. Verify your .env file exists in the same directory as your docker-compose.yml file.

3. Make sure your .env file has the correct format with no spaces around the equals sign:
   ```
   VARIABLE_NAME=value
   ```

4. Restart your Docker containers after changing the .env file:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

5. Check Docker logs for any errors:
   ```bash
   docker-compose logs web
   ``` 