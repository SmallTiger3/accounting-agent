import re

with open("/etc/nginx/conf.d/ng.conf", "r") as f:
    content = f.read()

block = """    # 记账Agent
    location ^~ /accounting/ {
        alias /opt/accounting-agent/frontend/dist/;
        index index.html;
        try_files $uri $uri/ /accounting/index.html;
    }

    location ^~ /accounting/api/ {
        rewrite ^/accounting/api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

"""

content = content.replace("   location / {", block + "   location / {")

with open("/etc/nginx/conf.d/ng.conf", "w") as f:
    f.write(content)

print("Config updated")