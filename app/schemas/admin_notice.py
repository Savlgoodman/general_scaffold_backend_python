"""
通知公告相关的 Pydantic Schema
用于请求参数校验和响应数据序列化，前端通过 OpenAPI 自动生成对接代码
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AdminNoticeCreate(BaseModel):
    """
    创建通知公告请求参数。
    创建后默认为草稿状态，需要调用发布接口才会对前端可见。
    """
    title: str = Field(..., min_length=1, max_length=200, description="公告标题")
    content: str = Field(..., min_length=1, description="公告内容，支持富文本HTML格式")
    notice_type: str = Field(..., description="公告类型: notice=通知（内部通知）, announcement=公告（面向全体用户）")
    is_top: bool = Field(False, description="是否置顶显示，置顶公告始终排在最前面")
    sort_order: int = Field(0, description="排序序号，数值越大越靠前，同为置顶时按此排序")


class AdminNoticeUpdate(BaseModel):
    """
    更新通知公告请求参数。
    所有字段均为可选，仅传入需要修改的字段。仅草稿状态的公告可编辑内容。
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="公告标题")
    content: Optional[str] = Field(None, min_length=1, description="公告内容，支持富文本HTML格式")
    notice_type: Optional[str] = Field(None, description="公告类型: notice=通知, announcement=公告")
    is_top: Optional[bool] = Field(None, description="是否置顶显示")
    sort_order: Optional[int] = Field(None, description="排序序号，数值越大越靠前")


class AdminNoticeResponse(BaseModel):
    """通知公告响应，包含公告完整信息"""
    id: int = Field(..., description="公告ID")
    title: str = Field(..., description="公告标题")
    content: str = Field(..., description="公告内容（富文本HTML）")
    notice_type: str = Field(..., description="公告类型: notice=通知, announcement=公告")
    status: str = Field(..., description="公告状态: draft=草稿, published=已发布, revoked=已撤回")
    publish_time: Optional[datetime] = Field(None, description="发布时间，草稿状态为空")
    publisher_id: int = Field(..., description="发布者用户ID")
    publisher_name: str = Field(..., description="发布者用户名")
    is_top: bool = Field(..., description="是否置顶")
    sort_order: int = Field(..., description="排序序号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")

    class Config:
        from_attributes = True


class AdminNoticeListResponse(BaseModel):
    """
    通知公告列表项响应（不含content，减少传输量）。
    用于列表页展示，点击后再通过详情接口获取完整内容。
    """
    id: int = Field(..., description="公告ID")
    title: str = Field(..., description="公告标题")
    notice_type: str = Field(..., description="公告类型: notice=通知, announcement=公告")
    status: str = Field(..., description="公告状态: draft=草稿, published=已发布, revoked=已撤回")
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    publisher_name: str = Field(..., description="发布者用户名")
    is_top: bool = Field(..., description="是否置顶")
    sort_order: int = Field(..., description="排序序号")
    created_at: datetime = Field(..., description="���建时间")

    class Config:
        from_attributes = True


class AdminNoticeQuery(BaseModel):
    """通知公告查询参数，支持多条件筛选和分页"""
    title: Optional[str] = Field(None, description="按标题模糊搜索")
    notice_type: Optional[str] = Field(None, description="按公告类型筛选: notice / announcement")
    status: Optional[str] = Field(None, description="按状态筛选: draft / published / revoked")
    publisher_name: Optional[str] = Field(None, description="按发布者用户名模糊搜索")
    start_time: Optional[datetime] = Field(None, description="创建时间起始，ISO 8601 格式")
    end_time: Optional[datetime] = Field(None, description="创建时间结束，ISO 8601 格式")
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")
