"""Registry of minimal boilerplate scaffolds for various technology stacks.
Each scaffold returns a dict: {path: content}
Focus: config + entrypoints only (no business logic).
"""
from __future__ import annotations
from typing import List, Dict, Union

# Simple content helpers
FASTAPI_MAIN = """from fastapi import FastAPI\n\napp = FastAPI(title='FastAPI Boilerplate')\n\n@app.get('/')\nasync def root():\n    return {'status': 'ok'}\n"""
FASTAPI_REQUIREMENTS = "fastapi>=0.110.0\nuvicorn>=0.29.0\n"

# Flask
FLASK_MAIN = """from flask import Flask, jsonify\napp = Flask(__name__)\n\n@app.get('/')\ndef root():\n    return jsonify(status='ok')\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=8000)\n"""
FLASK_REQUIREMENTS = "flask>=3.0.0\n"

EXPRESS_PACKAGE = {
    "name": "express-boilerplate",
    "version": "0.1.0",
    "type": "module",
    "scripts": {"start": "node src/server.js"},
    "dependencies": {"express": "^4.18.2"}
}
EXPRESS_SERVER = """import express from 'express';\nconst app = express();\napp.get('/', (req,res)=>res.json({status:'ok'}));\napp.listen(3000, ()=> console.log('Express boilerplate listening on 3000'));\n"""

DJANGO_REQUIREMENTS = "django>=5.0\n"
DJANGO_MANAGE = """#!/usr/bin/env python\nimport os, sys\nif __name__ == '__main__':\n    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')\n    from django.core.management import execute_from_command_line\n    execute_from_command_line(sys.argv)\n"""
DJANGO_SETTINGS = """SECRET_KEY = 'dev-key'\nDEBUG = True\nALLOWED_HOSTS = ['*']\nINSTALLED_APPS = ['django.contrib.contenttypes','django.contrib.auth']\nROOT_URLCONF = 'project.urls'\nMIDDLEWARE = []\nfrom pathlib import Path\nBASE_DIR = Path(__file__).resolve().parent.parent\nDATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR/'db.sqlite3'}}\n"""
DJANGO_URLS = """from django.urls import path\nfrom django.http import JsonResponse\n\ndef root(req): return JsonResponse({'status':'ok'})\nurlpatterns = [path('', root)]\n"""

SPRING_BOOT_POM = """<project>\n  <modelVersion>4.0.0</modelVersion>\n  <groupId>com.example</groupId>\n  <artifactId>demo</artifactId>\n  <version>0.0.1-SNAPSHOT</version>\n</project>\n"""
SPRING_BOOT_APP = """package com.example.demo;\nimport org.springframework.boot.SpringApplication;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\nimport org.springframework.web.bind.annotation.*;\n@SpringBootApplication\n@RestController\npublic class DemoApplication {\n  @GetMapping("/") public Object root(){ return java.util.Map.of("status","ok"); }\n  public static void main(String[] args){ SpringApplication.run(DemoApplication.class, args); }\n}\n"""

NEXT_PACKAGE = {
    "name": "next-boilerplate",
    "version": "0.1.0",
    "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
    "dependencies": {"next": "14.1.0", "react": "18.2.0", "react-dom": "18.2.0"}
}
NEXT_PAGE = """export default function Home(){ return <div>Status ok</div> }\n"""

# NestJS (minimal) - intentionally slim to avoid full Nest CLI structure
NEST_PACKAGE = {
    "name": "nest-boilerplate",
    "version": "0.1.0",
    "scripts": {"start": "node dist/main.js", "dev": "node --loader ts-node/esm src/main.ts"},
    "dependencies": {"@nestjs/core": "^10.0.0", "@nestjs/common": "^10.0.0", "reflect-metadata": "^0.1.13", "rxjs": "^7.8.0"},
    "type": "module"
}
NEST_MAIN = """import 'reflect-metadata';\nimport { NestFactory } from '@nestjs/core';\nimport { Module, Controller, Get } from '@nestjs/common';\n@Controller()\nclass AppController { @Get() root(){ return { status: 'ok' }; } }\n@Module({ controllers: [AppController] }) class AppModule {}\nasync function bootstrap(){ const app = await NestFactory.create(AppModule); await app.listen(3000); }\nbootstrap();\n"""

# Go (net/http)
GO_MAIN = """package main\nimport (\n  "fmt"\n  "net/http"\n)\nfunc root(w http.ResponseWriter, r *http.Request){ w.Header().Set("Content-Type","application/json"); w.Write([]byte(`{\"status\":\"ok\"}`)) }\nfunc main(){ http.HandleFunc("/", root); fmt.Println("Go server listening on :8080"); http.ListenAndServe(":8080", nil) }\n"""
GO_MOD = """module goapp\n\ngo 1.21\n"""

DOTNET_PROJ = """<Project Sdk=\"Microsoft.NET.Sdk.Web\">\n  <PropertyGroup>\n    <TargetFramework>net8.0</TargetFramework>\n  </PropertyGroup>\n</Project>\n"""
DOTNET_PROGRAM = """var builder = WebApplication.CreateBuilder(args);\nvar app = builder.Build();\napp.MapGet(\"/\", () => new { status = \"ok\" });\napp.Run();\n"""


def _as_json(obj: Dict) -> str:
    import json
    return json.dumps(obj, indent=2) + '\n'


def _to_name_list(stack: List[Union[str, Dict]]) -> List[str]:
    names: List[str] = []
    for item in stack:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            nm = item.get('name') or item.get('id') or item.get('value')
            if nm:
                names.append(str(nm))
    return names

def detect_primary(stack: List[Union[str, Dict]]) -> str:
    names = _to_name_list(stack)
    lowered = [s.lower() for s in names]
    for key in ['fastapi','flask','django','express','nest','nestjs','next','spring','springboot','spring-boot','dotnet','aspnet','go','gin']:
        if key in lowered:
            return key
    # fallback by language hints
    if any(k in lowered for k in ['python']):
        return 'fastapi'
    if any(k in lowered for k in ['node','javascript','typescript']):
        return 'express'
    if 'java' in lowered:
        return 'spring'
    if 'go' in lowered or 'golang' in lowered:
        return 'go'
    return 'fastapi'


def get_scaffold(stack: List[Union[str, Dict]]) -> Dict[str,str]:
    key = detect_primary(stack)
    if key == 'fastapi':
        return {
            'app/main.py': FASTAPI_MAIN,
            'requirements.txt': FASTAPI_REQUIREMENTS,
        }
    if key == 'flask':
        return {
            'app/main.py': FLASK_MAIN,
            'requirements.txt': FLASK_REQUIREMENTS,
        }
    if key == 'django':
        return {
            'manage.py': DJANGO_MANAGE,
            'project/__init__.py': '',
            'project/settings.py': DJANGO_SETTINGS,
            'project/urls.py': DJANGO_URLS,
            'requirements.txt': DJANGO_REQUIREMENTS,
        }
    if key == 'express':
        return {
            'package.json': _as_json(EXPRESS_PACKAGE),
            'src/server.js': EXPRESS_SERVER,
        }
    if key in ('nest','nestjs'):
        return {
            'package.json': _as_json(NEST_PACKAGE),
            'src/main.ts': NEST_MAIN,
            'tsconfig.json': _as_json({"compilerOptions": {"module": "es2022", "target": "es2022", "moduleResolution": "node", "esModuleInterop": True}})
        }
    if key in ('spring','springboot','spring-boot'):
        return {
            'pom.xml': SPRING_BOOT_POM,
            'src/main/java/com/example/demo/DemoApplication.java': SPRING_BOOT_APP,
        }
    if key == 'next':
        return {
            'package.json': _as_json(NEXT_PACKAGE),
            'pages/index.js': NEXT_PAGE,
        }
    if key in ('dotnet','aspnet'):
        return {
            'WebApp/WebApp.csproj': DOTNET_PROJ,
            'WebApp/Program.cs': DOTNET_PROGRAM,
        }
    if key in ('go','gin'):
        return {
            'main.go': GO_MAIN,
            'go.mod': GO_MOD,
        }
    # fallback
    return {'app/main.py': FASTAPI_MAIN}
