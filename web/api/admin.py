"""
Admin API routes - 管理后台
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel

from web.database import (
    get_all_users, get_all_orders, get_admin_stats,
    update_user_paid, get_deploy_logs, is_admin, set_admin, get_user,
    get_credit_logs, add_credits, get_user_credits,
)

router = APIRouter()

# Admin token from environment variable
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

# Default admin token (can be overridden by env var)
DEFAULT_ADMIN_TOKEN = "ai-auto-deploy-admin-2024"


def _verify_admin(request: Request):
    """Verify admin access via token or user_id."""
    token = request.headers.get("x-admin-token", "")
    user_id = request.headers.get("x-user-id", "")

    # Method 1: Fixed token
    expected = ADMIN_TOKEN or DEFAULT_ADMIN_TOKEN
    if token and token == expected:
        return True

    # Method 2: User is admin in DB
    if user_id and is_admin(user_id):
        return True

    raise HTTPException(status_code=403, detail="需要管理员权限")


# ============ Models ============

class UpdateUserRequest(BaseModel):
    paid_type: str  # "free" | "monthly" | "yearly" | "permanent"
    expires_at: Optional[str] = None


class SetAdminRequest(BaseModel):
    user_id: str
    is_admin: bool


class AddCreditsRequest(BaseModel):
    user_id: str
    amount: int
    description: Optional[str] = "管理员手动充值"


# ============ Routes ============

@router.get("/users")
async def list_users(request: Request):
    """获取所有用户列表"""
    _verify_admin(request)
    users = get_all_users()
    return {"users": users, "total": len(users)}


@router.get("/orders")
async def list_orders(request: Request):
    """获取所有订单"""
    _verify_admin(request)
    orders = get_all_orders()
    return {"orders": orders, "total": len(orders)}


@router.get("/stats")
async def dashboard_stats(request: Request):
    """统计数据"""
    _verify_admin(request)
    stats = get_admin_stats()
    return stats


@router.put("/users/{user_id}")
async def update_user(user_id: str, req: UpdateUserRequest, request: Request):
    """手动修改用户付费状态"""
    _verify_admin(request)

    if req.paid_type not in ("free", "monthly", "yearly", "permanent"):
        raise HTTPException(status_code=400, detail="无效的付费类型")

    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_user_paid(user_id, req.paid_type, req.expires_at)
    return {"message": "更新成功", "user_id": user_id, "paid_type": req.paid_type}


@router.get("/logs")
async def deploy_logs(request: Request, limit: int = 100):
    """获取部署日志"""
    _verify_admin(request)
    logs = get_deploy_logs(limit)
    return {"logs": logs, "total": len(logs)}


@router.post("/set-admin")
async def toggle_admin(request: Request, req: SetAdminRequest):
    """设置/取消管理员"""
    _verify_admin(request)
    user = get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    set_admin(req.user_id, req.is_admin)
    return {"message": "设置成功", "user_id": req.user_id, "is_admin": req.is_admin}


@router.get("/verify")
async def verify_admin(request: Request):
    """验证当前用户是否为管理员"""
    user_id = request.headers.get("x-user-id", "")
    token = request.headers.get("x-admin-token", "")
    expected = ADMIN_TOKEN or DEFAULT_ADMIN_TOKEN

    if (token and token == expected) or (user_id and is_admin(user_id)):
        return {"is_admin": True, "user_id": user_id}
    return {"is_admin": False, "user_id": user_id}


@router.get("/credit-logs")
async def credit_logs_endpoint(request: Request, user_id: Optional[str] = None, limit: int = 200):
    """获取积分流水记录"""
    _verify_admin(request)
    logs = get_credit_logs(user_id=user_id, limit=limit)
    return {"logs": logs, "total": len(logs)}


@router.post("/add-credits")
async def admin_add_credits(request: Request, req: AddCreditsRequest):
    """管理员手动给用户加积分"""
    _verify_admin(request)

    user = get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="积分数量必须大于0")

    success = add_credits(req.user_id, req.amount, "gift", req.description or "管理员手动充值")
    if not success:
        raise HTTPException(status_code=500, detail="积分添加失败")

    new_balance = get_user_credits(req.user_id)
    return {
        "message": f"成功为用户添加 {req.amount} 积分",
        "user_id": req.user_id,
        "added": req.amount,
        "new_balance": new_balance,
    }
