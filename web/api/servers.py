"""
Server management api routes
"""

import os
import json
import base64
import hashlib
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

CONFIG_FILE = os.path.expanduser("~/.ai-deploy.json")

_ENCRYPTION_SALT = "ai-auto-deploy-2024"


def _get_encryption_key() -> bytes:
    try:
        with open("/etc/machine-id", "r") as f:
            machine_id = f.read().strip()
    except Exception:
        machine_id = "fallback-machine-id"
    raw = f"{machine_id}:{_ENCRYPTION_SALT}"
    return hashlib.sha256(raw.encode()).digest()


def _encrypt_value(value: str) -> str:
    if not value:
        return ""
    try:
        from cryptography.fernet import Fernet
        key_bytes = _get_encryption_key()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        f = Fernet(fernet_key)
        encrypted = f.encrypt(value.encode("utf-8"))
        return encrypted.decode("utf-8")
    except ImportError:
        return "b64:" + base64.b64encode(value.encode("utf-8")).decode("utf-8")


def _decrypt_value(value: str) -> str:
    if not value:
        return ""
    try:
        if value.startswith("b64:"):
            return base64.b64decode(value[4:]).decode("utf-8")
        from cryptography.fernet import Fernet
        key_bytes = _get_encryption_key()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        f = Fernet(fernet_key)
        return f.decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        return value


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"servers": [], "defaults": {}}


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


class ServerCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    user: str = "root"
    password: Optional[str] = None
    key_file: Optional[str] = None
    baota: bool = False
    baota_port: Optional[str] = None
    baota_path: Optional[str] = None


class ServerTestRequest(BaseModel):
    host: str
    port: int = 22
    user: str = "root"
    password: Optional[str] = None
    key_file: Optional[str] = None


@router.get("")
async def list_servers():
    config = load_config()
    servers = config.get("servers", [])
    masked = []
    for s in servers:
        s_copy = dict(s)
        if s_copy.get("password"):
            s_copy["password"] = "******"
            s_copy["has_password"] = True
        if s_copy.get("key_content"):
            s_copy["key_content"] = "******"
            s_copy["has_key"] = True
        masked.append(s_copy)
    return {"servers": masked}


@router.post("")
async def add_server(server: ServerCreate):
    config = load_config()
    server_dict = {
        "name": server.name,
        "host": server.host,
        "port": server.port,
        "user": server.user,
        "baota": server.baota,
        "baota_port": server.baota_port,
        "baota_path": server.baota_path,
    }
    if server.password:
        server_dict["password"] = _encrypt_value(server.password)
        server_dict["has_password"] = True
    if server.key_file:
        if os.path.isfile(server.key_file):
            with open(server.key_file, "r") as f:
                key_content = f.read()
            server_dict["key_content"] = _encrypt_value(key_content)
            server_dict["has_key"] = True
        else:
            server_dict["key_content"] = _encrypt_value(server.key_file)
            server_dict["has_key"] = True
    config["servers"].append(server_dict)
    save_config(config)
    resp = dict(server_dict)
    if resp.get("password"):
        resp["password"] = "******"
    if resp.get("key_content"):
        resp["key_content"] = "******"
    return {"message": "服务器已添加", "server": resp}


@router.delete("/{index}")
async def delete_server(index: int):
    config = load_config()
    servers = config.get("servers", [])
    if index < 0 or index >= len(servers):
        raise HTTPException(status_code=404, detail="服务器不存在")
    removed = servers.pop(index)
    config["servers"] = servers
    save_config(config)
    return {"message": "服务器已删除", "server": removed.get("name", "")}


@router.post("/test")
async def test_server_connection(req: ServerTestRequest):
    try:
        import paramiko
    except ImportError:
        raise HTTPException(status_code=500, detail="paramiko 未安装")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connect_kwargs = {
            "hostname": req.host,
            "port": req.port,
            "username": req.user,
            "timeout": 10,
        }
        if req.key_file:
            if os.path.isfile(req.key_file):
                connect_kwargs["key_filename"] = req.key_file
            else:
                import io
                key_file_obj = io.StringIO(req.key_file)
                try:
                    pkey = paramiko.RSAKey.from_private_key(key_file_obj)
                except Exception:
                    key_file_obj = io.StringIO(req.key_file)
                    pkey = paramiko.Ed25519Key.from_private_key(key_file_obj)
                connect_kwargs["pkey"] = pkey
        elif req.password:
            connect_kwargs["password"] = req.password
        else:
            raise HTTPException(status_code=400, detail="需要提供密码或密钥")
        client.connect(**connect_kwargs)
        stdin, stdout, stderr = client.exec_command("echo 'connection_ok' && uname -a")
        output = stdout.read().decode("utf-8").strip()
        error = stderr.read().decode("utf-8").strip()
        return {
            "success": True,
            "message": "连接成功",
            "info": output,
            "error": error if error else None,
        }
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
    finally:
        client.close()


def get_server_credentials(server: dict) -> dict:
    creds = {
        "host": server["host"],
        "port": server.get("port", 22),
        "user": server.get("user", "root"),
    }
    encrypted_pwd = server.get("password", "")
    if encrypted_pwd and encrypted_pwd != "******":
        creds["password"] = _decrypt_value(encrypted_pwd)
    encrypted_key = server.get("key_content", "")
    if encrypted_key and encrypted_key != "******":
        creds["key_content"] = _decrypt_value(encrypted_key)
    return creds
