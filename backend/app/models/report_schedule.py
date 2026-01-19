"""ReportSchedule model for scheduled admin report configuration."""

import uuid
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ScheduleType(str, Enum):
    """Schedule type enumeration."""

    WEEKLY = "weekly"
    DAILY = "daily"
    DISABLED = "disabled"


class DayOfWeek(str, Enum):
    """Day of week enumeration."""

    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class ReportSchedule(Base, TimestampMixin):
    """
    Singleton table for storing report schedule configuration.

    Only one row should exist in this table, containing the global
    schedule settings for admin reports.
    """

    __tablename__ = "report_schedule"

    # Primary key (always 1 for singleton)
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1,
        nullable=False,
    )

    # Schedule enabled flag
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Schedule type: weekly, daily, or disabled
    schedule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ScheduleType.WEEKLY.value,
    )

    # Day of week for weekly reports
    day_of_week: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=DayOfWeek.MON.value,
    )

    # Time to send (UTC)
    hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=9,
    )

    minute: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Track who last updated the schedule
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        """String representation of the schedule."""
        return (
            f"<ReportSchedule(enabled={self.enabled}, "
            f"type={self.schedule_type}, day={self.day_of_week}, "
            f"time={self.hour:02d}:{self.minute:02d})>"
        )

    def to_dict(self) -> dict:
        """Convert schedule to dictionary for API responses."""
        return {
            "enabled": self.enabled,
            "schedule_type": self.schedule_type,
            "day_of_week": self.day_of_week,
            "hour": self.hour,
            "minute": self.minute,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
