"""
Code Fix API routes - 代码错误检测与自动修复
"""

import os
import ast
import io
import re
import json
import asyncio
import py_compile
import traceback
import difflib
import zipfile
import tempfile
import shutil
import base64
from typing import Optional

import requests
import paramiko
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from web.database import get_user_credits, deduct_credits
from web.api.servers import get_server_credentials, load_config

router = APIRouter()

# 豆包 AI 配置
ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
DOUBAO_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_MODEL_ID = "ep-20260707225043-z7nkm"

# 积分消耗配置
CREDIT_COST_FIX = 200


# ============ Models ============

class AnalyzeRequest(BaseModel):
    path: str
    user_id: Optional[str] = None


class RepairError(BaseModel):
    file: str
    line: int
    error: str
    severity: str  # "error" | "warning"
    error_type: str  # "syntax" | "import" | "type" | "config" | "bracket"


class RepairRequest(BaseModel):
    path: str
    errors: list[RepairError]
    user_id: Optional[str] = None


class RepairResult(BaseModel):
    file: str
    original: str
    fixed: str
    diff: str


# ============ 本地检测逻辑 ============

def collect_files(project_path: str, extensions: list[str]) -> list[str]:
    """收集指定扩展名的文件"""
    files = []
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next', '.nuxt'}
    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in filenames:
            if any(f.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, f))
    return files


def check_python_syntax(filepath: str) -> list[dict]:
    """使用 py_compile 检测 Python 语法错误"""
    errors = []
    try:
        py_compile.compile(filepath, doraise=True)
    except py_compile.PyCompileError as e:
        line = 0
        msg = str(e)
        # 提取行号
        match = re.search(r'line (\d+)', msg)
        if match:
            line = int(match.group(1))
        errors.append({
            "file": filepath,
            "line": line,
            "error": msg.split('\n')[-1].strip() if '\n' in msg else msg.strip(),
            "severity": "error",
            "error_type": "syntax"
        })
    return errors


def check_python_ast(filepath: str) -> list[dict]:
    """使用 ast 检测 Python 代码问题"""
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        
        # 收集所有 import 的模块
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
        
        # 检查顶层的 Name 引用是否有定义 (简化检测)
        defined_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    defined_names.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    defined_names.add(alias.asname or alias.name)

    except SyntaxError as e:
        errors.append({
            "file": filepath,
            "line": e.lineno or 0,
            "error": f"AST解析错误: {e.msg}",
            "severity": "error",
            "error_type": "syntax"
        })
    except Exception:
        pass
    
    return errors


def check_js_syntax(filepath: str) -> list[dict]:
    """使用正则检测 JavaScript/TypeScript 常见错误"""
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        lines = content.split('\n')
        
        # 检测括号匹配
        bracket_stack = []
        bracket_map = {')': '(', ']': '[', '}': '{'}
        open_brackets = set('({[')
        close_brackets = set(')}]')
        
        in_string = False
        string_char = None
        in_template = False
        in_line_comment = False
        in_block_comment = False
        
        for line_no, line in enumerate(lines, 1):
            in_line_comment = False
            i = 0
            while i < len(line):
                ch = line[i]
                
                # 处理注释
                if not in_string and not in_template:
                    if in_block_comment:
                        if ch == '*' and i + 1 < len(line) and line[i + 1] == '/':
                            in_block_comment = False
                            i += 2
                            continue
                        i += 1
                        continue
                    if ch == '/' and i + 1 < len(line):
                        if line[i + 1] == '/':
                            break  # 剩余都是注释
                        if line[i + 1] == '*':
                            in_block_comment = True
                            i += 2
                            continue
                
                # 处理字符串
                if not in_block_comment and not in_line_comment:
                    if in_string:
                        if ch == '\\':
                            i += 2
                            continue
                        if ch == string_char:
                            in_string = False
                    elif in_template:
                        if ch == '\\':
                            i += 2
                            continue
                        if ch == '`':
                            in_template = False
                    else:
                        if ch in ('"', "'"):
                            in_string = True
                            string_char = ch
                        elif ch == '`':
                            in_template = True
                        elif ch in open_brackets:
                            bracket_stack.append((ch, line_no))
                        elif ch in close_brackets:
                            if bracket_stack and bracket_stack[-1][0] == bracket_map[ch]:
                                bracket_stack.pop()
                            else:
                                errors.append({
                                    "file": filepath,
                                    "line": line_no,
                                    "error": f"未匹配的闭合括号 '{ch}'",
                                    "severity": "error",
                                    "error_type": "bracket"
                                })
                
                i += 1
        
        # 检查未闭合的括号
        if bracket_stack:
            for bracket, line_no in bracket_stack[-5:]:  # 最多报5个
                errors.append({
                    "file": filepath,
                    "line": line_no,
                    "error": f"未闭合的括号 '{bracket}'",
                    "severity": "warning",
                    "error_type": "bracket"
                })
        
        # 检测常见的 require 但模块可能缺失
        require_pattern = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""")
        for line_no, line in enumerate(lines, 1):
            for match in require_pattern.finditer(line):
                module = match.group(1)
                # 检查是否是相对路径
                if module.startswith('.') or module.startswith('/'):
                    dir_of_file = os.path.dirname(filepath)
                    possible_paths = [
                        os.path.join(dir_of_file, module),
                        os.path.join(dir_of_file, module + '.js'),
                        os.path.join(dir_of_file, module + '.ts'),
                        os.path.join(dir_of_file, module, 'index.js'),
                    ]
                    if not any(os.path.exists(p) for p in possible_paths):
                        errors.append({
                            "file": filepath,
                            "line": line_no,
                            "error": f"引用的本地模块可能不存在: {module}",
                            "severity": "warning",
                            "error_type": "import"
                        })
    
    except Exception:
        pass
    
    return errors


def check_json_files(filepath: str) -> list[dict]:
    """检测 JSON 文件格式错误"""
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.strip():
            json.loads(content)
    except json.JSONDecodeError as e:
        errors.append({
            "file": filepath,
            "line": e.lineno,
            "error": f"JSON格式错误: {e.msg}",
            "severity": "error",
            "error_type": "config"
        })
    except Exception:
        pass
    return errors


def check_yaml_files(filepath: str) -> list[dict]:
    """检测 YAML 文件格式错误"""
    errors = []
    try:
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.strip():
            yaml.safe_load(content)
    except ImportError:
        # yaml 模块不可用，使用简单检测
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            # 基本检查：tab缩进（YAML不允许tab）
            for line_no, line in enumerate(content.split('\n'), 1):
                if '\t' in line and not line.strip().startswith('#'):
                    errors.append({
                        "file": filepath,
                        "line": line_no,
                        "error": "YAML文件中使用了Tab缩进（YAML只允许空格缩进）",
                        "severity": "error",
                        "error_type": "config"
                    })
                    break
        except Exception:
            pass
    except Exception as e:
        line = getattr(e, 'problem_mark', None)
        line_no = line.line + 1 if line else 0
        errors.append({
            "file": filepath,
            "line": line_no,
            "error": f"YAML格式错误: {str(e.problem) if hasattr(e, 'problem') else str(e)}",
            "severity": "error",
            "error_type": "config"
        })
    return errors


def check_python_imports(project_path: str) -> list[dict]:
    """检查 Python 项目的 requirements.txt 与实际 import 的对应"""
    errors = []
    req_file = os.path.join(project_path, 'requirements.txt')
    if not os.path.exists(req_file):
        return errors
    
    try:
        # 解析 requirements.txt
        declared_packages = set()
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # 提取包名（去掉版本约束）
                    pkg = re.split(r'[>=<!~\[]', line)[0].strip()
                    if pkg:
                        declared_packages.add(pkg.lower().replace('-', '_'))
        
        # 收集项目中所有的 import
        py_files = collect_files(project_path, ['.py'])
        imported_modules = set()
        for fpath in py_files:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_modules.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.level == 0:
                            imported_modules.add(node.module.split('.')[0])
            except Exception:
                continue
        
        # 标准库模块（部分）
        stdlib = {
            'os', 'sys', 're', 'json', 'math', 'datetime', 'collections',
            'itertools', 'functools', 'pathlib', 'typing', 'dataclasses',
            'asyncio', 'threading', 'subprocess', 'shutil', 'glob', 'io',
            'hashlib', 'uuid', 'time', 'logging', 'unittest', 'abc',
            'contextlib', 'enum', 'copy', 'pprint', 'traceback', 'inspect',
            'importlib', 'textwrap', 'string', 'struct', 'tempfile',
            'socket', 'http', 'urllib', 'email', 'html', 'xml',
            'csv', 'sqlite3', 'pickle', 'base64', 'binascii',
            'codecs', 'signal', 'stat', 'operator', 'warnings',
            'secrets', 'hmac', 'argparse', 'getpass', 'platform',
            'concurrent', 'multiprocessing', 'queue', 'random',
            'decimal', 'fractions', 'statistics', 'array',
            'py_compile', 'ast', 'dis', 'token', 'tokenize',
            'pdb', 'profile', 'timeit', 'types', 'weakref',
            'web', 'src', '__future__', 'builtins', 'ctypes',
            'mimetypes', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
        }
        
        # 检查是否有import的第三方模块不在 requirements.txt 中
        for mod in imported_modules:
            mod_lower = mod.lower().replace('-', '_')
            if (mod_lower not in declared_packages and 
                mod_lower not in stdlib and
                not mod.startswith('.')):
                errors.append({
                    "file": req_file,
                    "line": 0,
                    "error": f"模块 '{mod}' 被引用但未在 requirements.txt 中声明",
                    "severity": "warning",
                    "error_type": "import"
                })
    except Exception:
        pass
    
    return errors


def check_package_json(project_path: str) -> list[dict]:
    """检查 Node.js 项目的依赖完整性"""
    errors = []
    pkg_file = os.path.join(project_path, 'package.json')
    if not os.path.exists(pkg_file):
        return errors
    
    try:
        with open(pkg_file, 'r', encoding='utf-8') as f:
            pkg = json.load(f)
        
        deps = set(pkg.get('dependencies', {}).keys())
        dev_deps = set(pkg.get('devDependencies', {}).keys())
        all_deps = deps | dev_deps
        
        # 收集 JS/TS 文件中的 import
        js_files = collect_files(project_path, ['.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'])
        
        imported_packages = set()
        for fpath in js_files:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 匹配 import ... from 'package' 和 require('package')
                for match in re.finditer(r"""(?:import\s+.*?\s+from\s+['"]([^'"./][^'"]*)['"]|require\s*\(\s*['"]([^'"./][^'"]*)['"]\s*\))""", content):
                    pkg_name = match.group(1) or match.group(2)
                    if pkg_name:
                        # 获取包名（处理 scoped packages）
                        if pkg_name.startswith('@'):
                            parts = pkg_name.split('/')
                            if len(parts) >= 2:
                                imported_packages.add(f"{parts[0]}/{parts[1]}")
                        else:
                            imported_packages.add(pkg_name.split('/')[0])
            except Exception:
                continue
        
        # Node.js 内置模块
        node_builtins = {
            'fs', 'path', 'http', 'https', 'url', 'util', 'os', 'stream',
            'crypto', 'events', 'buffer', 'child_process', 'cluster',
            'dgram', 'dns', 'net', 'readline', 'tls', 'vm', 'zlib',
            'assert', 'async_hooks', 'console', 'constants', 'domain',
            'inspector', 'module', 'perf_hooks', 'process', 'punycode',
            'querystring', 'string_decoder', 'sys', 'timers', 'tty',
            'v8', 'worker_threads', 'node:fs', 'node:path', 'node:http',
            'node:https', 'node:url', 'node:util', 'node:os', 'node:stream',
            'node:crypto', 'node:events', 'node:buffer', 'node:child_process',
        }
        
        for pkg_name in imported_packages:
            if (pkg_name not in all_deps and 
                pkg_name not in node_builtins and
                not pkg_name.startswith('node:')):
                errors.append({
                    "file": pkg_file,
                    "line": 0,
                    "error": f"包 '{pkg_name}' 被引用但未在 package.json 中声明",
                    "severity": "warning",
                    "error_type": "import"
                })
    except json.JSONDecodeError:
        pass  # JSON 格式错误已由 check_json_files 处理
    except Exception:
        pass
    
    return errors


def analyze_project(project_path: str) -> list[dict]:
    """完整分析项目代码错误"""
    all_errors = []
    
    # Python 文件检测
    py_files = collect_files(project_path, ['.py'])
    for f in py_files:
        all_errors.extend(check_python_syntax(f))
        all_errors.extend(check_python_ast(f))
    
    # JavaScript/TypeScript 文件检测
    js_files = collect_files(project_path, ['.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'])
    for f in js_files:
        all_errors.extend(check_js_syntax(f))
    
    # JSON 文件检测
    json_files = collect_files(project_path, ['.json'])
    for f in json_files:
        all_errors.extend(check_json_files(f))
    
    # YAML 文件检测
    yaml_files = collect_files(project_path, ['.yml', '.yaml'])
    for f in yaml_files:
        all_errors.extend(check_yaml_files(f))
    
    # 依赖检查
    all_errors.extend(check_python_imports(project_path))
    all_errors.extend(check_package_json(project_path))
    
    # 将文件路径转为相对路径
    for err in all_errors:
        err['file'] = os.path.relpath(err['file'], project_path)
    
    # 去重
    seen = set()
    unique_errors = []
    for err in all_errors:
        key = (err['file'], err['line'], err['error'])
        if key not in seen:
            seen.add(key)
            unique_errors.append(err)
    
    # 排序: error 在前, warning 在后
    unique_errors.sort(key=lambda x: (0 if x['severity'] == 'error' else 1, x['file'], x['line']))
    
    return unique_errors


# ============ AI 修复逻辑 ============

def call_doubao_api(messages: list[dict]) -> str:
    """调用豆包 API"""
    try:
        response = requests.post(
            f"{DOUBAO_ENDPOINT}/chat/completions",
            headers={
                "Authorization": f"Bearer {ARK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DOUBAO_MODEL_ID,
                "messages": messages,
                "temperature": 0.1,
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {str(e)}")


def generate_fix(project_path: str, error: dict) -> dict:
    """使用 AI 生成修复代码"""
    filepath = os.path.join(project_path, error['file'])
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail=f"文件不存在: {error['file']}")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        original_content = f.read()
    
    # 获取错误附近的代码上下文
    lines = original_content.split('\n')
    error_line = error.get('line', 0)
    
    # 取错误行前后各 10 行作为上下文
    start = max(0, error_line - 11) if error_line > 0 else 0
    end = min(len(lines), error_line + 10) if error_line > 0 else min(len(lines), 50)
    context_lines = lines[start:end]
    context = '\n'.join(context_lines)
    
    prompt = f"""你是一个代码修复专家。请修复以下代码中的错误。

文件: {error['file']}
错误类型: {error['error_type']}
错误描述: {error['error']}
错误行号: {error['line']}

以下是错误附近的代码（第{start+1}行到第{end}行）:
```
{context}
```

请只输出修复后的完整文件内容，不要包含任何解释或markdown标记。
确保只修复指定的错误，不要改变其他代码的功能。
如果原文件整体内容太长，输出完整的修复后文件。"""

    messages = [
        {"role": "system", "content": "你是一个代码修复专家。用户会给你代码和错误信息，你需要返回修复后的完整代码。只返回代码本身，不要包含markdown代码块标记或任何解释文字。"},
        {"role": "user", "content": prompt}
    ]
    
    fixed_content = call_doubao_api(messages)
    
    # 清理可能的 markdown 标记
    fixed_content = fixed_content.strip()
    if fixed_content.startswith('```'):
        # 去掉第一行
        first_newline = fixed_content.index('\n') if '\n' in fixed_content else len(fixed_content)
        fixed_content = fixed_content[first_newline + 1:]
    if fixed_content.endswith('```'):
        fixed_content = fixed_content[:-3].strip()
    
    # 生成 diff
    diff = ''.join(difflib.unified_diff(
        original_content.splitlines(keepends=True),
        fixed_content.splitlines(keepends=True),
        fromfile=f"a/{error['file']}",
        tofile=f"b/{error['file']}",
        lineterm=''
    ))
    
    return {
        "file": error['file'],
        "original": original_content,
        "fixed": fixed_content,
        "diff": diff
    }


# ============ Routes ============

@router.post("/analyze")
async def analyze_code(req: AnalyzeRequest):
    """分析项目代码错误（检测本身免费，AI修复才收费）"""
    project_path = req.path.strip()
    
    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")
    
    try:
        errors = analyze_project(project_path)
        return {
            "errors": errors,
            "total": len(errors),
            "error_count": sum(1 for e in errors if e['severity'] == 'error'),
            "warning_count": sum(1 for e in errors if e['severity'] == 'warning'),
            "path": project_path,
            "fix_credit_cost": CREDIT_COST_FIX,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/repair")
async def repair_code(req: RepairRequest):
    """自动修复代码错误（消耗积分）"""
    project_path = req.path.strip()
    
    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")
    
    if not req.errors:
        raise HTTPException(status_code=400, detail="没有需要修复的错误")

    # Check credits before repair
    if req.user_id:
        credits = get_user_credits(req.user_id)
        if credits < CREDIT_COST_FIX:
            raise HTTPException(
                status_code=402,
                detail=f"积分不足，代码修复需要 {CREDIT_COST_FIX} 积分，当前余额 {credits} 积分，请充值",
            )
    
    results = []
    for error in req.errors:
        try:
            result = generate_fix(project_path, error.dict())
            results.append(result)
        except HTTPException:
            raise
        except Exception as e:
            results.append({
                "file": error.file,
                "original": "",
                "fixed": "",
                "diff": f"修复失败: {str(e)}"
            })
    
    # Deduct credits after success
    if req.user_id and results:
        deduct_credits(req.user_id, CREDIT_COST_FIX, "代码检测+修复")
    
    return {
        "results": results,
        "credits_cost": CREDIT_COST_FIX,
        "credits_remaining": get_user_credits(req.user_id) if req.user_id else None,
    }


@router.post("/apply")
async def apply_fix(req: dict):
    """应用修复到文件"""
    project_path = req.get("path", "").strip()
    fixes = req.get("fixes", [])
    
    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail=f"目录不存在: {project_path}")
    
    applied = []
    for fix in fixes:
        filepath = os.path.join(project_path, fix['file'])
        try:
            # 备份原文件
            backup_path = filepath + '.bak'
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    original = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original)
            
            # 写入修复后的内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fix['fixed'])
            
            applied.append({"file": fix['file'], "status": "success"})
        except Exception as e:
            applied.append({"file": fix['file'], "status": "failed", "error": str(e)})
    
    return {"applied": applied}

# ============ 远程服务器检测/修复 ============

def _get_ssh_client(creds: dict) -> paramiko.SSHClient:
    """创建SSH连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        "hostname": creds["host"],
        "port": creds.get("port", 22),
        "username": creds.get("user", "root"),
        "timeout": 15,
    }
    key_content = creds.get("key_content")
    password = creds.get("password")

    if key_content:
        key_file_obj = io.StringIO(key_content)
        try:
            pkey = paramiko.RSAKey.from_private_key(key_file_obj)
        except Exception:
            key_file_obj = io.StringIO(key_content)
            try:
                pkey = paramiko.Ed25519Key.from_private_key(key_file_obj)
            except Exception:
                key_file_obj = io.StringIO(key_content)
                pkey = paramiko.ECDSAKey.from_private_key(key_file_obj)
        connect_kwargs["pkey"] = pkey
    elif password:
        connect_kwargs["password"] = password
    else:
        raise RuntimeError("需要提供密码或密钥")

    client.connect(**connect_kwargs)
    return client


def _download_remote_project(client: paramiko.SSHClient, remote_path: str, local_dir: str):
    """通过SFTP下载远程项目到本地临时目录"""
    sftp = client.open_sftp()
    try:
        def _recursive_download(remote_dir: str, local_base: str):
            try:
                entries = sftp.listdir_attr(remote_dir)
            except Exception:
                return

            for entry in entries:
                remote_full = remote_dir + "/" + entry.filename
                local_full = os.path.join(local_base, entry.filename)

                # 跳过隐藏目录和常见的非代码目录
                if entry.filename.startswith('.') or entry.filename in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'):
                    continue

                import stat as stat_module
                if stat_module.S_ISDIR(entry.st_mode):
                    os.makedirs(local_full, exist_ok=True)
                    _recursive_download(remote_full, local_full)
                else:
                    # 只下载代码相关文件
                    code_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css',
                                 '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.sh',
                                 '.sql', '.xml', '.md', '.txt', '.c', '.cpp', '.h', '.go',
                                 '.php', '.rb', '.java', '.svelte'}
                    _, ext = os.path.splitext(entry.filename)
                    if ext.lower() in code_exts or entry.filename in ('Makefile', 'Dockerfile', '.gitignore', '.env', 'requirements.txt', 'package.json', 'package-lock.json', 'go.mod', 'go.sum'):
                        try:
                            sftp.get(remote_full, local_full)
                        except Exception:
                            pass

        _recursive_download(remote_path, local_dir)
    finally:
        sftp.close()


@router.post("/analyze-remote")
async def analyze_remote(req: dict):
    """通过SSH连接远程服务器检测项目"""
    server_id = req.get("server_id", "")
    project_path = req.get("project_path", "").strip()
    user_id = req.get("user_id", "")

    if not server_id:
        raise HTTPException(status_code=400, detail="请选择服务器")
    if not project_path:
        raise HTTPException(status_code=400, detail="请输入项目路径")

    # 获取服务器配置
    config = load_config()
    servers = config.get("servers", [])
    server_index = None

    try:
        server_index = int(server_id)
    except ValueError:
        for i, s in enumerate(servers):
            if s.get("host") == server_id:
                server_index = i
                break

    if server_index is None or server_index >= len(servers):
        raise HTTPException(status_code=400, detail="服务器不存在")

    creds = get_server_credentials(servers[server_index])

    loop = asyncio.get_event_loop()

    def _do_download_and_analyze():
        client = _get_ssh_client(creds)
        try:
            # 检查远程目录是否存在
            stdin, stdout, stderr = client.exec_command(f'[ -d "{project_path}" ] && echo "exists" || echo "not_found"')
            result = stdout.read().decode().strip()
            if result != "exists":
                raise HTTPException(status_code=400, detail=f"远程目录不存在: {project_path}")

            # 下载到临时目录
            tmp_dir = tempfile.mkdtemp(prefix="fix-remote-")
            _download_remote_project(client, project_path, tmp_dir)

            # 检测
            errors = analyze_project(tmp_dir)
            return errors, tmp_dir
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"远程检测失败: {str(e)}")
        finally:
            client.close()

    try:
        errors, tmp_dir = await loop.run_in_executor(None, _do_download_and_analyze)
        return {
            "errors": errors,
            "total": len(errors),
            "error_count": sum(1 for e in errors if e["severity"] == "error"),
            "warning_count": sum(1 for e in errors if e["severity"] == "warning"),
            "path": project_path,
            "mode": "remote",
            "temp_dir": tmp_dir,
            "fix_credit_cost": CREDIT_COST_FIX,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/analyze-upload")
async def analyze_upload(file: UploadFile = File(...), user_id: str = Form(default="")):
    """上传ZIP项目检测"""
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 10MB")

    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="请上传 .zip 格式文件")

    tmp_dir = tempfile.mkdtemp(prefix="fix-upload-")
    zip_path = os.path.join(tmp_dir, "upload.zip")
    extract_dir = os.path.join(tmp_dir, "project")

    try:
        with open(zip_path, "wb") as f:
            f.write(contents)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # 如果解压后只有一个子目录，使用该子目录作为项目根目录
        entries = os.listdir(extract_dir)
        if len(entries) == 1:
            single_entry = os.path.join(extract_dir, entries[0])
            if os.path.isdir(single_entry):
                extract_dir = single_entry

        errors = analyze_project(extract_dir)

        return {
            "errors": errors,
            "total": len(errors),
            "error_count": sum(1 for e in errors if e["severity"] == "error"),
            "warning_count": sum(1 for e in errors if e["severity"] == "warning"),
            "path": extract_dir,
            "mode": "upload",
            "temp_dir": extract_dir,
            "fix_credit_cost": CREDIT_COST_FIX,
        }
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="无效的ZIP文件")
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/repair-upload")
async def repair_upload(req: dict):
    """修复上传的项目"""
    temp_dir = req.get("temp_dir", "").strip()
    errors = req.get("errors", [])
    user_id = req.get("user_id", "")

    if not temp_dir or not os.path.isdir(temp_dir):
        raise HTTPException(status_code=400, detail="项目临时目录不存在")
    if not errors:
        raise HTTPException(status_code=400, detail="没有需要修复的错误")

    # Check credits
    if user_id:
        credits = get_user_credits(user_id)
        if credits < CREDIT_COST_FIX:
            raise HTTPException(status_code=402, detail=f"积分不足，代码修复需要 {CREDIT_COST_FIX} 积分，当前余额 {credits} 积分")

    results = []
    for error in errors:
        try:
            result = generate_fix(temp_dir, error if isinstance(error, dict) else error)
            results.append(result)
        except Exception as e:
            err = error if isinstance(error, dict) else {"file": error.file, "line": error.line, "error": str(e), "error_type": "unknown"}
            results.append({
                "file": err.get("file", "unknown"),
                "original": "",
                "fixed": "",
                "diff": f"修复失败: {str(e)}"
            })

    # Deduct credits
    if user_id and results:
        deduct_credits(user_id, CREDIT_COST_FIX, "代码检测+修复(上传)")

    return {
        "results": results,
        "temp_dir": temp_dir,
        "credits_cost": CREDIT_COST_FIX,
        "credits_remaining": get_user_credits(user_id) if user_id else None,
    }


@router.post("/repair-remote")
async def repair_remote(req: dict):
    """修复远程服务器上的项目"""
    server_id = req.get("server_id", "")
    project_path = req.get("project_path", "").strip()
    errors = req.get("errors", [])
    user_id = req.get("user_id", "")

    if not server_id:
        raise HTTPException(status_code=400, detail="请选择服务器")
    if not project_path:
        raise HTTPException(status_code=400, detail="请输入项目路径")
    if not errors:
        raise HTTPException(status_code=400, detail="没有需要修复的错误")

    # Check credits
    if user_id:
        credits = get_user_credits(user_id)
        if credits < CREDIT_COST_FIX:
            raise HTTPException(status_code=402, detail=f"积分不足，代码修复需要 {CREDIT_COST_FIX} 积分，当前余额 {credits} 积分")

    # 获取服务器配置
    config = load_config()
    servers = config.get("servers", [])
    server_index = None

    try:
        server_index = int(server_id)
    except ValueError:
        for i, s in enumerate(servers):
            if s.get("host") == server_id:
                server_index = i
                break

    if server_index is None or server_index >= len(servers):
        raise HTTPException(status_code=400, detail="服务器不存在")

    creds = get_server_credentials(servers[server_index])

    loop = asyncio.get_event_loop()

    def _do_repair_remote():
        # 先下载到临时目录
        client = _get_ssh_client(creds)
        try:
            tmp_dir = tempfile.mkdtemp(prefix="fix-remote-repair-")
            _download_remote_project(client, project_path, tmp_dir)

            # 本地修复
            results = []
            for error in errors:
                try:
                    result = generate_fix(tmp_dir, error if isinstance(error, dict) else error)
                    results.append(result)
                except Exception as e:
                    err = error if isinstance(error, dict) else {"file": "unknown"}
                    results.append({
                        "file": err.get("file", "unknown"),
                        "original": "",
                        "fixed": "",
                        "diff": f"修复失败: {str(e)}"
                    })

            # 将修复后的文件写回远程服务器
            sftp = client.open_sftp()
            try:
                for result in results:
                    if result.get("fixed"):
                        remote_path = os.path.join(project_path, result["file"])
                        encoded = base64.b64encode(result["fixed"].encode("utf-8")).decode("ascii")
                        cmd = f'echo "{encoded}" | base64 -d > "{remote_path}"'
                        _stdin, _stdout, _stderr = client.exec_command(cmd, timeout=30)
                        _stdout.read()
            finally:
                sftp.close()

            return results
        finally:
            client.close()

    try:
        results = await loop.run_in_executor(None, _do_repair_remote)

        if user_id and results:
            deduct_credits(user_id, CREDIT_COST_FIX, "代码检测+修复(远程)")

        return {
            "results": results,
            "credits_cost": CREDIT_COST_FIX,
            "credits_remaining": get_user_credits(user_id) if user_id else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"远程修复失败: {str(e)}")


@router.post("/download-repaired")
async def download_repaired(req: dict):
    """下载修复后的项目为ZIP"""
    temp_dir = req.get("temp_dir", "").strip()

    if not temp_dir or not os.path.isdir(temp_dir):
        raise HTTPException(status_code=400, detail="临时目录不存在")

    tmp_zip = tempfile.mktemp(suffix=".zip")
    try:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for fname in files:
                    filepath = os.path.join(root, fname)
                    arcname = os.path.relpath(filepath, temp_dir)
                    zf.write(filepath, arcname)

        def iter_file():
            with open(tmp_zip, "rb") as fh:
                yield from fh

        return StreamingResponse(
            iter_file(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=repaired-project.zip"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打包失败: {str(e)}")
