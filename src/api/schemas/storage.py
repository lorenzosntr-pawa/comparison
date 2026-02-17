"""Pydantic schemas for storage monitoring API endpoints.

This module defines request and response schemas for storage monitoring:
- TableSize: Individual table size information
- StorageSizes: Current storage sizes for all tables
- StorageSampleResponse: Historical storage sample record
- StorageHistoryResponse: List of historical samples

Uses camelCase aliases for frontend compatibility.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TableSize(BaseModel):
    """Size information for a single database table.

    Attributes:
        table_name: Name of the database table.
        size_bytes: Size in bytes.
        size_human: Human-readable size (e.g., "12.5 MB").
        row_count: Approximate number of rows (from pg_stat_user_tables).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    table_name: str = Field(description="Database table name")
    size_bytes: int = Field(description="Table size in bytes")
    size_human: str = Field(description="Human-readable size (e.g., '12.5 MB')")
    row_count: int = Field(description="Approximate row count")


class StorageSizes(BaseModel):
    """Current storage sizes for all database tables.

    Attributes:
        tables: List of individual table sizes.
        total_bytes: Total database size in bytes.
        total_human: Human-readable total database size.
        measured_at: Timestamp when measurements were taken.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    tables: list[TableSize] = Field(description="Individual table sizes")
    total_bytes: int = Field(description="Total database size in bytes")
    total_human: str = Field(description="Human-readable total size")
    measured_at: datetime = Field(description="When measurements were taken")


class StorageSampleResponse(BaseModel):
    """Response model for a single storage sample record.

    Attributes:
        id: Unique database ID.
        sampled_at: When the sample was taken.
        total_bytes: Total database size at sample time.
        table_sizes: Dict mapping table names to size in bytes.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(description="Unique database ID")
    sampled_at: datetime = Field(description="When sample was taken")
    total_bytes: int = Field(description="Total database size in bytes")
    table_sizes: dict[str, int] = Field(description="Table name to size mapping")


class StorageHistoryResponse(BaseModel):
    """Response model for storage history list.

    Attributes:
        samples: List of storage sample records.
        total: Total number of samples in database.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    samples: list[StorageSampleResponse] = Field(description="Storage sample records")
    total: int = Field(description="Total samples in database")


class StorageAlertResponse(BaseModel):
    """Response model for a storage alert.

    Attributes:
        id: Unique database ID.
        created_at: When the alert was created.
        alert_type: Type of alert ('growth_warning' or 'size_critical').
        message: Human-readable description.
        current_bytes: Database size when alert was created.
        previous_bytes: Previous sample size.
        growth_percent: Growth percentage from previous sample.
        resolved_at: When alert was resolved (None if active).
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(description="Unique database ID")
    created_at: datetime = Field(description="When alert was created")
    alert_type: str = Field(description="Alert type (growth_warning, size_critical)")
    message: str = Field(description="Human-readable description")
    current_bytes: int = Field(description="Database size when alert was created")
    previous_bytes: int = Field(description="Previous sample size")
    growth_percent: float = Field(description="Growth percentage")
    resolved_at: datetime | None = Field(description="When alert was resolved")


class StorageAlertsResponse(BaseModel):
    """Response model for storage alerts list.

    Attributes:
        alerts: List of storage alert records.
        count: Number of alerts returned.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    alerts: list[StorageAlertResponse] = Field(description="Storage alert records")
    count: int = Field(description="Number of alerts")
