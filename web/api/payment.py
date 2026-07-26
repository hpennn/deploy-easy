"""
Payment API routes - 虎皮椒支付集成（积分包购买制）
"""

import time
import hashlib
import uuid
from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from web.database import (
    create_order, update_order_status, get_order,
    get_user, upsert_user, add_credits, get_user_credits,
)

router = APIRouter()

# 虎皮椒支付配置
XUNHU_APPID = "201906182239"
XUNHU_APPSECRET = "a03834403fd0101fb1c622545967b3db"
XUNHU_API = "https://api.xunhupay.com"

# 积分包套餐配置
CREDIT_PACKAGES = {
    "starter": {
        "price": 9.9,
        "credits": 30000,
        "label": "体验包",
        "desc": "30,000 积分，约60次生成项目",
    },
    "basic": {
        "price": 29,
        "credits": 90000,
        "label": "基础包",
        "desc": "90,000 积分，约180次生成项目",
    },
    "pro": {
        "price": 99,
        "credits": 300000,
        "label": "进阶包",
        "desc": "300,000 积分，约600次生成项目",
    },
    "ultimate": {
        "price": 299,
        "credits": 900000,
        "label": "旗舰包",
        "desc": "900,000 积分，约1800次生成项目",
    },
}

# 每次操作消耗积分配置
CREDIT_COSTS = {
    "generate_project": 500,
    "modify_code": 300,
    "fix_code": 200,
    "deploy_script": 0,
    "remote_deploy": 0,
}


# ============ Models ============

class CreatePaymentRequest(BaseModel):
    user_id: str
    package: str  # "starter" | "basic" | "pro" | "ultimate"


class CheckPaymentResponse(BaseModel):
    order_id: str
    status: str  # "pending" | "paid"
    package: Optional[str] = None


# ============ Helpers ============

def _generate_order_id() -> str:
    ts = int(time.time() * 1000)
    rand = uuid.uuid4().hex[:8]
    return f"ORD{ts}{rand}"


def _sign_params(params: dict) -> str:
    filtered = {k: v for k, v in params.items() if k != "hash" and v != "" and v is not None}
    sorted_keys = sorted(filtered.keys())
    raw = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
    raw += XUNHU_APPSECRET
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _verify_notify_hash(params: dict) -> bool:
    received_hash = params.get("hash", "")
    if not received_hash:
        return False
    filtered = {k: v for k, v in params.items() if k != "hash" and v != "" and v is not None}
    sorted_keys = sorted(filtered.keys())
    raw = "&".join(f"{k}={filtered[k]}" for k in sorted_keys)
    raw += XUNHU_APPSECRET
    expected = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return received_hash == expected


# ============ Routes ============

@router.post("/create")
async def create_payment(req: CreatePaymentRequest):
    """创建积分包购买订单"""
    if req.package not in CREDIT_PACKAGES:
        raise HTTPException(status_code=400, detail="无效的套餐类型")

    pkg = CREDIT_PACKAGES[req.package]
    order_id = _generate_order_id()
    amount = pkg["price"]
    label = pkg["label"]

    create_order(order_id, req.user_id, amount, req.package)

    nonce = str(int(time.time()))
    pay_params = {
        "version": "1.1",
        "appid": XUNHU_APPID,
        "trade_order_id": order_id,
        "total_fee": str(amount),
        "title": f"AI Auto Deploy - {label}",
        "body": f"AI Auto Deploy {label}，获得 {pkg['credits']:,} 积分",
        "notify_url": "/api/payment/notify",
        "nonce_str": nonce,
        "time": nonce,
        "type": "WAP",
    }
    pay_params["hash"] = _sign_params(pay_params)

    try:
        resp = requests.post(
            f"{XUNHU_API}/payment/do.html",
            json=pay_params,
            timeout=10,
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise HTTPException(status_code=500, detail=f"支付创建失败: {data.get('errmsg', '未知错误')}")
        return {
            "order_id": order_id,
            "amount": amount,
            "package": req.package,
            "credits": pkg["credits"],
            "pay_url": data.get("url", ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"支付服务异常: {str(e)}")


@router.post("/notify")
async def payment_notify(request: Request):
    """虎皮椒支付回调 - 支付成功后加积分"""
    form = await request.form()
    params = dict(form)

    if not _verify_notify_hash(params):
        raise HTTPException(status_code=400, detail="签名验证失败")

    order_id = params.get("trade_order_id", "")
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 更新订单状态
    update_order_status(order_id, "paid")

    # 给用户加积分
    user_id = order["user_id"]
    package_id = order["paid_type"]  # 订单的 paid_type 存的是 package id
    pkg = CREDIT_PACKAGES.get(package_id)

    if pkg:
        credits_amount = pkg["credits"]
        label = pkg["label"]
        add_credits(user_id, credits_amount, "recharge", f"购买{label}")

    return {"errcode": 0, "errmsg": "success"}


@router.get("/check/{order_id}")
async def check_payment(order_id: str):
    """检查支付状态"""
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_id": order_id,
        "status": order["status"],
        "package": order.get("paid_type"),
        "amount": order["amount"],
    }


@router.get("/user/{user_id}")
async def get_user_payment(user_id: str):
    """查询用户积分状态"""
    user = get_user(user_id)
    credits = get_user_credits(user_id)

    return {
        "user_id": user_id,
        "credits": credits,
        "paid_type": user["paid_type"] if user else "free",
        "paid_at": user.get("paid_at") if user else None,
        "expires_at": user.get("expires_at") if user else None,
        "packages": {k: {"price": v["price"], "credits": v["credits"], "label": v["label"]} for k, v in CREDIT_PACKAGES.items()},
        "credit_costs": CREDIT_COSTS,
    }


@router.get("/packages")
async def get_packages():
    """获取积分包套餐"""
    return {
        "packages": CREDIT_PACKAGES,
        "credit_costs": CREDIT_COSTS,
    }
