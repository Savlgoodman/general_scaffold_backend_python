"""
通知公告管理 API
提供系统通知和公告的创建、编辑、发布、撤回、查询等完整生命周期管理。
状态流转：草稿(draft) → 已发布(published) → 已撤回(revoked)。
管理端可查看所有状态的公告，前端展示端仅可查看已发布的公告。
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin_notice import (
    AdminNoticeCreate, AdminNoticeUpdate, AdminNoticeResponse,
    AdminNoticeListResponse, AdminNoticeQuery
)
from app.schemas.common import Response, PageResponse
from app.services.admin_notice_service import AdminNoticeService
from app.utils.dependencies import get_current_admin_user
from app.utils.query_params import clean_query_params
from app.utils.operation_log import log_operation

router = APIRouter(prefix="/notices", tags=["Notices"])


@router.get(
    "/list",
    response_model=Response[PageResponse[AdminNoticeListResponse]],
    summary="Get notice list (admin)",
    description="Paginated query of all notices for admin management, including draft/published/revoked. "
                "Supports filtering by title, type, status, publisher and time range. "
                "Results are sorted by: pinned first, then sort_order descending, then created_at descending."
)
def get_notices(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page, max 100"),
    title: Optional[str] = Query(None, description="Filter by title (fuzzy match)"),
    notice_type: Optional[str] = Query(None, description="Filter by type: notice / announcement"),
    notice_status: Optional[str] = Query(None, description="Filter by status: draft / published / revoked"),
    publisher_name: Optional[str] = Query(None, description="Filter by publisher name (fuzzy match)"),
    start_time: Optional[str] = Query(None, description="Start time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="End time, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(
        title=title,
        notice_type=notice_type,
        status=notice_status,
        publisher_name=publisher_name,
        start_time=(start_time, datetime),
        end_time=(end_time, datetime)
    )

    query_params = AdminNoticeQuery(
        page=page,
        page_size=page_size,
        **params
    )

    notices, total = AdminNoticeService.get_list(db, query_params)

    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminNoticeListResponse.model_validate(n) for n in notices]
        )
    )


@router.get(
    "/published",
    response_model=Response[PageResponse[AdminNoticeListResponse]],
    summary="Get published notice list (frontend)",
    description="Get published notices for frontend display. Only returns notices with status=published. "
                "Sorted by: pinned first, then sort_order descending, then publish_time descending. "
                "This API is intended for the frontend notification center."
)
def get_published_notices(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page, max 100"),
    notice_type: Optional[str] = Query(None, description="Filter by type: notice / announcement"),
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    params = clean_query_params(notice_type=notice_type)

    notices, total = AdminNoticeService.get_published_list(
        db, page=page, page_size=page_size, notice_type=params.get("notice_type")
    )

    return Response(
        code=200,
        message="获取成功",
        data=PageResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminNoticeListResponse.model_validate(n) for n in notices]
        )
    )


@router.get(
    "/detail/{notice_id}",
    response_model=Response[AdminNoticeResponse],
    summary="Get notice detail",
    description="Get full details of a single notice by ID, including the complete content (HTML)."
)
def get_notice(
    notice_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notice = AdminNoticeService.get_by_id(db, notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    return Response(
        code=200,
        message="获取成功",
        data=AdminNoticeResponse.model_validate(notice)
    )


@router.post(
    "/create",
    response_model=Response[AdminNoticeResponse],
    summary="Create notice",
    description="Create a new notice in draft status. After creation, call the publish API to make it visible. "
                "Supports rich text HTML content."
)
def create_notice(
    data: AdminNoticeCreate,
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notice = AdminNoticeService.create(
        db, data,
        publisher_id=current_user.id,
        publisher_name=current_user.username
    )

    log_operation(
        db, request=request, action="CREATE", resource_type="notice",
        resource_id=notice.id, description=f"创建公告「{notice.title}」",
    )

    return Response(
        code=200,
        message="创建成功",
        data=AdminNoticeResponse.model_validate(notice)
    )


@router.post(
    "/update/{notice_id}",
    response_model=Response[AdminNoticeResponse],
    summary="Update notice",
    description="Update notice information. Only draft notices can have their title/content/type modified. "
                "Published or revoked notices can only modify is_top and sort_order."
)
def update_notice(
    notice_id: int,
    data: AdminNoticeUpdate,
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notice = AdminNoticeService.update(db, notice_id, data)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    log_operation(
        db, request=request, action="UPDATE", resource_type="notice",
        resource_id=notice_id, description=f"更新公告「{notice.title}」",
    )

    return Response(
        code=200,
        message="更新成功",
        data=AdminNoticeResponse.model_validate(notice)
    )


@router.post(
    "/delete/{notice_id}",
    response_model=Response,
    summary="Delete notice",
    description="Soft-delete a notice. The notice will no longer appear in any list."
)
def delete_notice(
    notice_id: int,
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notice = AdminNoticeService.get_by_id(db, notice_id)
    success = AdminNoticeService.delete(db, notice_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    log_operation(
        db, request=request, action="DELETE", resource_type="notice",
        resource_id=notice_id,
        description=f"删除公告「{notice.title if notice else notice_id}」",
    )

    return Response(code=200, message="删除成功", data=None)


@router.post(
    "/publish/{notice_id}",
    response_model=Response[AdminNoticeResponse],
    summary="Publish notice",
    description="Publish a draft notice, changing its status from 'draft' to 'published'. "
                "Only draft notices can be published. Once published, the notice becomes visible to all users."
)
def publish_notice(
    notice_id: int,
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    try:
        notice = AdminNoticeService.publish(db, notice_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    log_operation(
        db, request=request, action="UPDATE", resource_type="notice",
        resource_id=notice_id, description=f"发布公告「{notice.title}」",
    )

    return Response(
        code=200,
        message="发布成功",
        data=AdminNoticeResponse.model_validate(notice)
    )


@router.post(
    "/revoke/{notice_id}",
    response_model=Response[AdminNoticeResponse],
    summary="Revoke notice",
    description="Revoke a published notice, changing its status from 'published' to 'revoked'. "
                "Only published notices can be revoked. Once revoked, the notice is no longer visible to users."
)
def revoke_notice(
    notice_id: int,
    request: Request,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    try:
        notice = AdminNoticeService.revoke(db, notice_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    log_operation(
        db, request=request, action="UPDATE", resource_type="notice",
        resource_id=notice_id, description=f"撤回公告「{notice.title}」",
    )

    return Response(
        code=200,
        message="撤回成功",
        data=AdminNoticeResponse.model_validate(notice)
    )
